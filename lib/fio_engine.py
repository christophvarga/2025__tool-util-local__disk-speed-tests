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
        # Key insight: Don't redirect JSON to stdout, use separate file for JSON
        # This allows FIO to send live updates via stderr
        base_params = [
            self.fio_path,
            '--output-format=json',
            '--status-interval=2',     # Status updates every 2 seconds
            '--eta=always',            # Always show ETA
            '--eta-newline=1',         # Force newline every 1 second for live updates
            '--eta-interval=500',      # ETA update frequency 500ms
            '--direct=1',              # Essential for accurate disk performance testing
            f'--filename={disk_path}/{os.path.basename(self.test_file_path)}',
            f'--size={test_size_bytes}',
            '--ioengine=posixaio',     # Optimal for macOS (not sync)
            '--randrepeat=0',          # Ensure non-repeating random patterns
            '--norandommap',           # Ensure non-repeating random patterns
            '--group_reporting',       # Report aggregate statistics for all jobs
            # Don't use --output=- as it breaks live updates
            # Instead use temp file which will be set per job
        ]

        if test_mode == "setup_check":
            # Setup Check (30s) - Quick test to verify basic functionality
            return [
                base_params + [
                    '--name=setup_read',
                    '--rw=read',
                    '--bs=1M',
                    '--numjobs=1',
                    '--runtime=30',
                    '--time_based',
                    '--iodepth=1'
                ],
                base_params + [
                    '--name=setup_write',
                    '--rw=write',
                    '--bs=1M',
                    '--numjobs=1',
                    '--runtime=30',
                    '--time_based',
                    '--iodepth=1'
                ]
            ]
        elif test_mode == "baseline_streaming":
            # Baseline Streaming Test (1h)
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
            # QLab-Pattern mit Random Seeks (2h)
            return [
                base_params + [
                    '--name=qlab_pattern',
                    '--rw=randrw',
                    '--rwmixread=95',
                    '--bs=1M',
                    '--numjobs=6',
                    '--time_based',
                    '--runtime=7200',
                    '--rate=800M,200M',
                    '--iodepth=32',
                    '--random_generator=tausworthe64',
                    '--log_avg_msec=100',
                    '--write_bw_log=qlab_pattern_bw',
                    '--write_lat_log=qlab_pattern_lat'
                ]
            ]
        elif test_mode == "crossfade_stress":
            # Stress Test - Überblendungs-Peaks (2h)
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
            # Create temp JSON file for this job
            temp_json_file = f"/tmp/fio_job_{int(time.time())}_{i}.json"
            cmd_parts_with_output = cmd_parts + [f'--output={temp_json_file}']
            
            job_name = next((p.split('=')[1] for p in cmd_parts_with_output if p.startswith('--name=')), f"Job {i+1}")
            runtime = int(next((p.split('=')[1] for p in cmd_parts_with_output if p.startswith('--runtime=')), '0'))
            
            if monitor:
                monitor.set_test_phase(f"Fio: {job_name}", runtime)
            
            print(f"\nRunning fio test: {job_name}...")
            try:
                # Start fio process - no stdout redirection to allow live stderr
                process = subprocess.Popen(
                    cmd_parts_with_output, 
                    stdout=subprocess.DEVNULL,  # Ignore stdout
                    stderr=subprocess.PIPE, 
                    text=True, 
                    bufsize=1  # Line buffered
                )

                # Simple real-time monitoring - read stderr line by line
                if monitor:
                    for line in iter(process.stderr.readline, ''):
                        if line.strip():  # Process all non-empty lines
                            monitor.update_with_fio_data(line)
                
                # Wait for completion
                process.wait()

                if process.returncode != 0:
                    print(f"fio test failed for job '{job_name}'")
                    continue

                # Read JSON results from temp file
                try:
                    if os.path.exists(temp_json_file):
                        with open(temp_json_file, 'r') as f:
                            result_json = json.load(f)
                        all_results.append(result_json)
                        os.remove(temp_json_file)  # Clean up
                    else:
                        print(f"No JSON output file found for job '{job_name}'")
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Failed to parse JSON for job '{job_name}': {e}")
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
