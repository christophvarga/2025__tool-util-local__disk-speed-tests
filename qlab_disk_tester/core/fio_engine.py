import subprocess
import json
import os
import time
import select
import fcntl

class FioEngine:
    def __init__(self, test_file_path="/tmp/fio_test_file", fio_path="fio"):
        self.test_file_path = test_file_path
        self.fio_path = fio_path

    def _get_fio_parameters(self, test_mode, disk_path, test_size_gb):
        """
        Returns fio parameters for a given test mode with optimized macOS settings.
        test_size_gb will be used to determine the actual size for the test file.
        """
        # Alias-Support: map QLab Show-Pattern mode to internal qlab_pattern
        if test_mode == "qlab_show_pattern":
            test_mode = "qlab_pattern"
            
        # Convert GB to bytes for fio size parameter
        test_size_bytes = test_size_gb * 1024 * 1024 * 1024

        # macOS-optimized parameters based on FIO CLI documentation
        # Removed --group_reporting and --eta to avoid shared memory issues on macOS
        base_params = [
            self.fio_path,
            '--output-format=json',
            '--eta=never',             # Disable ETA to avoid shared memory issues
            f'--filename={disk_path}/{os.path.basename(self.test_file_path)}',
            f'--size={test_size_bytes}',
            '--ioengine=sync',         # Optimal for macOS
        ]

        if test_mode == "setup_check":
            # Setup Check (5s) - Quick test to verify basic functionality
            return [
                base_params + [
                    '--name=setup_read',
                    '--rw=read',
                    '--bs=4k',
                    '--numjobs=1',
                    '--runtime=5',
                    '--time_based',
                    '--iodepth=1'
                ],
                base_params + [
                    '--name=setup_write',
                    '--rw=write',
                    '--bs=4k',
                    '--numjobs=1',
                    '--runtime=5',
                    '--time_based',
                    '--iodepth=1'
                ]
            ]
        elif test_mode == "baseline_streaming":
            # Baseline Streaming Test (1h) - Keep original for now
            return [
                base_params + [
                    '--name=baseline_streaming',
                    '--rw=read',
                    '--bs=1M',
                    '--numjobs=4',
                    '--time_based',
                    '--runtime=3600',
                    '--rate=700M',
                    '--iodepth=16',
                    '--log_avg_msec=100',
                    '--write_bw_log=baseline_bw',
                    '--write_lat_log=baseline_lat'
                ]
            ]
        elif test_mode == "qlab_pattern":
            # QLab-Pattern (5s) - Simplified for debugging
            return [
                base_params + [
                    '--name=qlab_pattern',
                    '--rw=randrw',
                    '--rwmixread=95',
                    '--bs=4k',
                    '--numjobs=1',
                    '--runtime=5',
                    '--time_based',
                    '--iodepth=1'
                ]
            ]
        elif test_mode == "crossfade_stress":
            # Stress Test - Überblendungs-Peaks (2h) - Keep original for now
            return [
                base_params + [
                    '--name=crossfade_stress',
                    '--rw=read',
                    '--bs=2M',
                    '--numjobs=8',
                    '--time_based',
                    '--runtime=7200',
                    '--rate=2100M',
                    '--rate_process=poisson',
                    '--iodepth=64',
                    '--thinktime=5000000',
                    '--thinktime_spin=1000000',
                    '--log_avg_msec=100',
                    '--write_bw_log=crossfade_bw',
                    '--write_lat_log=crossfade_lat',
                    '--lat_percentiles=1'
                ]
            ]
        else:
            raise ValueError("Invalid test mode specified.")

    def execute_fio_test(self, test_mode, disk_path, test_size_gb, monitor=None):
        """
        Executes fio tests for the given mode with real-time live updates.
        Key fix: Use separate JSON files, not stdout redirect, for proper live updates
        """
        job_commands = self._get_fio_parameters(test_mode, disk_path, test_size_gb)
        all_results = []

        for i, cmd_parts in enumerate(job_commands):
            # Remove --output parameter if it exists, as we'll capture stdout
            cmd_parts_no_output = [p for p in cmd_parts if not p.startswith('--output=')]
            
            job_name = next((p.split('=')[1] for p in cmd_parts_no_output if p.startswith('--name=')), f"Job {i+1}")
            runtime = int(next((p.split('=')[1] for p in cmd_parts_no_output if p.startswith('--runtime=')), '0'))
            
            if monitor:
                monitor.set_test_phase(f"Fio: {job_name}", runtime)
            
            print(f"\nRunning fio test: {job_name}...")
            print(f"Fio command: {' '.join(cmd_parts_no_output)}") # Print the exact command
            try:
                # Start fio process - capture both stdout and stderr
                process = subprocess.Popen(
                    cmd_parts_no_output, 
                    stdout=subprocess.PIPE,  # Capture stdout for JSON
                    stderr=subprocess.PIPE,  # Capture stderr for live updates
                    text=True, 
                    bufsize=1  # Line buffered
                )

                json_buffer = []
                json_started = False
                
                # Read stdout and stderr simultaneously
                while True:
                    reads = []
                    if process.stdout:
                        reads.append(process.stdout.fileno())
                    if process.stderr:
                        reads.append(process.stderr.fileno())

                    if not reads: # No more pipes to read from
                        break

                    ret = select.select(reads, [], [], 0.1) # Add a timeout to prevent blocking indefinitely

                    if not ret[0] and process.poll() is not None: # No data and process finished
                        break

                    for fd in ret[0]:
                        if fd == process.stdout.fileno():
                            line = process.stdout.readline()
                            if line:
                                # Look for JSON start/end markers
                                if line.strip().startswith('{'):
                                    json_started = True
                                if json_started:
                                    json_buffer.append(line)
                                if line.strip().endswith('}'):
                                    json_started = False # End of JSON object
                        elif fd == process.stderr.fileno():
                            line = process.stderr.readline()
                            if line:
                                if monitor:
                                    monitor.update_with_fio_data(line)
                    
                    if process.poll() is not None and not json_started: # Process finished and no pending JSON
                        break
                
                process.wait() # Ensure process has fully terminated

                if process.returncode != 0:
                    print(f"fio test failed for job '{job_name}' with return code {process.returncode}")
                    # Capture and print all stderr for debugging
                    remaining_stderr = process.stderr.read()
                    if remaining_stderr:
                        print(f"Fio stderr: {remaining_stderr}")
                    else:
                        print("No stderr output from fio")
                    
                    # Also try to get any stdout that might contain error info
                    remaining_stdout = process.stdout.read()
                    if remaining_stdout:
                        print(f"Fio stdout: {remaining_stdout}")
                    
                    if monitor:
                        monitor.log_error(f"FIO test '{job_name}' failed with return code {process.returncode}")
                        if remaining_stderr:
                            monitor.log_error(f"FIO stderr: {remaining_stderr}")
                        if remaining_stdout:
                            monitor.log_error(f"FIO stdout: {remaining_stdout}")
                    continue

                # Parse JSON results from captured stdout
                full_json_output = "".join(json_buffer)
                try:
                    result_json = json.loads(full_json_output)
                    all_results.append(result_json)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON for job '{job_name}': {e}")
                    print(f"Raw Fio stdout (attempted JSON): {full_json_output}") # Print raw output for debugging
                    continue

            except FileNotFoundError:
                print("Error: fio command not found. Please ensure fio is installed and in your PATH.")
                return None
            except Exception as e:
                print(f"An unexpected error occurred during fio execution: {e}")
                return None
            finally:
                if monitor:
                    monitor.print_live_status(force_newline=True)

        return all_results

    def cleanup_test_files(self, disk_path):
        """Removes the fio test file from the disk."""
        file_to_remove = os.path.join(disk_path, os.path.basename(self.test_file_path))
        if os.path.exists(file_to_remove):
            try:
                os.remove(file_to_remove)
                print(f"Cleaned up test file: {file_to_remove}")
            except Exception as e:
                print(f"Error cleaning up test file {file_to_remove}: {e}")

if __name__ == "__main__":
    # Example Usage:
    engine = FioEngine()
    
    # Example: Quick Test on /tmp
    print("--- Running Quick Test on /tmp ---")
    results = engine.execute_fio_test("setup_check", "/tmp", 1)
    if results:
        print(json.dumps(results, indent=2))
    
    # Clean up after examples
    engine.cleanup_test_files("/tmp")
