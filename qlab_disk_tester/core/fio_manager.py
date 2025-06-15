import subprocess
import json
import os
import sys
import time
import select
import threading
from typing import Optional, Dict, Any, Callable

class FioManager:
    """
    Production-safe FIO manager that only performs real disk tests.
    No fallbacks, no dummy values - either real tests or clear errors.
    """
    
    def __init__(self):
        self.fio_path = self._detect_fio_binary()
        self.current_process = None
        self.stop_requested = False
    
    def _detect_fio_binary(self) -> Optional[str]:
        """Detect available FIO binary with strict validation."""
        # Check for bundled fio binary first (for .app bundles)
        bundle_fio = self._get_bundled_fio_path()
        if bundle_fio and os.path.exists(bundle_fio) and os.access(bundle_fio, os.X_OK):
            if self._validate_fio_binary(bundle_fio):
                return bundle_fio
        
        # Check for system-installed fio
        try:
            result = subprocess.run(['which', 'fio'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                fio_path = result.stdout.strip()
                if self._validate_fio_binary(fio_path):
                    return fio_path
        except:
            pass
        
        # Check for local fio binary (development)
        local_fio = os.path.join(os.getcwd(), 'fio-3.37', 'fio')
        if os.path.exists(local_fio) and os.access(local_fio, os.X_OK):
            if self._validate_fio_binary(local_fio):
                return local_fio
        
        return None
    
    def _get_bundled_fio_path(self) -> Optional[str]:
        """Get the path to the bundled FIO binary in .app bundle."""
        try:
            # Check if we're running from a PyInstaller bundle
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller bundle - look in the temporary directory
                bundle_fio = os.path.join(sys._MEIPASS, 'fio-3.37', 'fio')
                return bundle_fio
            
            # Check if we're in a .app bundle structure
            current_path = os.path.abspath(__file__)
            if '.app/Contents/' in current_path:
                # Extract the .app path
                app_path = current_path.split('.app/Contents/')[0] + '.app'
                
                # Try both possible locations
                locations = [
                    os.path.join(app_path, 'Contents', 'Frameworks', 'fio-3.37', 'fio'),
                    os.path.join(app_path, 'Contents', 'Resources', 'fio-3.37', 'fio')
                ]
                
                for bundle_fio in locations:
                    if os.path.exists(bundle_fio):
                        return bundle_fio
            
            return None
        except:
            return None
    
    def _validate_fio_binary(self, fio_path: str) -> bool:
        """Validate that FIO binary works correctly."""
        try:
            result = subprocess.run([fio_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and 'fio-' in result.stdout
        except:
            return False
    
    def is_fio_available(self) -> bool:
        """Check if FIO is available for testing."""
        return self.fio_path is not None
    
    def get_fio_status(self) -> Dict[str, Any]:
        """Get detailed FIO status information."""
        if not self.fio_path:
            return {
                'available': False,
                'error': 'FIO binary not found',
                'path': None,
                'version': None,
                'installation_guide': [
                    'Install FIO using Homebrew:',
                    '  brew install fio',
                    '',
                    'Or download from: https://github.com/axboe/fio'
                ]
            }
        
        try:
            result = subprocess.run([self.fio_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            version = result.stdout.strip() if result.returncode == 0 else 'Unknown'
            
            return {
                'available': True,
                'error': None,
                'path': self.fio_path,
                'version': version,
                'installation_guide': None
            }
        except Exception as e:
            return {
                'available': False,
                'error': f'FIO validation failed: {e}',
                'path': self.fio_path,
                'version': None,
                'installation_guide': ['FIO binary found but not working properly']
            }
    
    def execute_real_disk_test(self, test_mode: str, disk_path: str, test_size_gb: int, 
                              monitor: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
        """
        Execute REAL disk tests using FIO. No fallbacks, no dummy values.
        Returns None if FIO is not available or test fails.
        """
        if not self.is_fio_available():
            if monitor:
                monitor.log_error("FIO not available - cannot perform real disk tests")
                monitor.log_error(f"FIO path attempted: {self.fio_path}")
                monitor.log_error(f"FIO status: {self.get_fio_status()}")
            return None
        
        try:
            if monitor:
                # Enhanced debug logging for terminal
                if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                    terminal = monitor.parent_window.debug_terminal
                    terminal.log_info(f"FIO Binary found: {self.fio_path}")
                    terminal.log_debug(f"Target directory: {disk_path}")
                    terminal.log_debug(f"Test mode: {test_mode}")
                    terminal.log_debug(f"Test size: {test_size_gb}GB")
                
                monitor.update_with_fio_data(f"✅ FIO Binary found: {self.fio_path}")
                monitor.update_with_fio_data(f"📂 Target directory: {disk_path}")
                monitor.update_with_fio_data(f"🔧 Test mode: {test_mode}")
                monitor.update_with_fio_data(f"💾 Test size: {test_size_gb}GB")
            
            job_commands = self._get_production_fio_parameters(test_mode, disk_path, test_size_gb)
            
            if monitor:
                if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                    terminal = monitor.parent_window.debug_terminal
                    terminal.log_debug(f"Generated {len(job_commands)} FIO job(s)")
                    for i, cmd in enumerate(job_commands):
                        terminal.log_debug(f"Job {i+1} command: {' '.join(cmd)}")
                
                monitor.update_with_fio_data(f"📋 Generated {len(job_commands)} FIO job(s)")
            
            all_results = []
            
            for i, cmd_parts in enumerate(job_commands):
                if self.stop_requested:
                    if monitor:
                        monitor.update_with_fio_data("⏹️ Test stopped by user")
                    break
                
                job_name = next((p.split('=')[1] for p in cmd_parts if p.startswith('--name=')), f"Job {i+1}")
                runtime = int(next((p.split('=')[1] for p in cmd_parts if p.startswith('--runtime=')), '0'))
                
                if monitor:
                    monitor.set_test_phase(f"FIO: {job_name}", runtime)
                    monitor.update_with_fio_data(f"🚀 Starting FIO job: {job_name}")
                    monitor.update_with_fio_data(f"⏱️ Expected runtime: {runtime}s")
                    # Log the actual FIO command for debugging
                    cmd_str = ' '.join(cmd_parts)
                    monitor.update_with_fio_data(f"🔧 FIO Command: {cmd_str}")
                
                result = self._execute_single_fio_job(cmd_parts, monitor)
                if result:
                    all_results.append(result)
                    if monitor:
                        monitor.update_with_fio_data(f"✅ Job '{job_name}' completed successfully")
                else:
                    if monitor:
                        monitor.log_error(f"❌ FIO job '{job_name}' failed - stopping test")
                    return None
            
            if all_results:
                if monitor:
                    monitor.update_with_fio_data(f"🎉 All {len(all_results)} FIO jobs completed successfully")
                
                return {
                    'test_mode': test_mode,
                    'jobs': all_results,
                    'engine': 'fio',
                    'real_test': True
                }
            else:
                if monitor:
                    monitor.log_error("❌ No FIO jobs completed successfully")
                return None
            
        except Exception as e:
            if monitor:
                monitor.log_error(f"❌ Real disk test failed with exception: {e}")
                import traceback
                monitor.log_error(f"📋 Traceback: {traceback.format_exc()}")
            return None
    
    def _execute_single_fio_job(self, cmd_parts, monitor) -> Optional[Dict[str, Any]]:
        """Execute a single FIO job with real-time monitoring."""
        try:
            # Enhanced debug logging for subprocess creation
            if monitor:
                if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                    terminal = monitor.parent_window.debug_terminal
                    terminal.log_subprocess(f"About to start FIO subprocess...")
                    terminal.log_subprocess(f"Command: {' '.join(cmd_parts)}")
                    terminal.log_subprocess(f"FIO binary path: {cmd_parts[0]}")
                    
                    # Check if FIO binary exists and is executable
                    fio_binary = cmd_parts[0]
                    if os.path.exists(fio_binary):
                        terminal.log_debug(f"FIO binary exists: {fio_binary}")
                        if os.access(fio_binary, os.X_OK):
                            terminal.log_debug(f"FIO binary is executable")
                        else:
                            terminal.log_error(f"FIO binary NOT executable - fixing permissions...")
                            try:
                                os.chmod(fio_binary, 0o755)
                                terminal.log_info(f"Fixed FIO binary permissions")
                            except Exception as chmod_error:
                                terminal.log_error(f"Failed to fix permissions: {chmod_error}")
                    else:
                        terminal.log_error(f"FIO binary does not exist: {fio_binary}")
                        return None
                
                monitor.update_with_fio_data(f"🚀 Starting FIO subprocess...")
            
            # Start FIO process
            if monitor:
                if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                    terminal = monitor.parent_window.debug_terminal
                    terminal.log_subprocess(f"Creating subprocess.Popen...")
            
            try:
                self.current_process = subprocess.Popen(
                    cmd_parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # Log successful process creation
                if monitor:
                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                        terminal = monitor.parent_window.debug_terminal
                        terminal.log_subprocess(f"Subprocess created successfully (PID: {self.current_process.pid})")
                    monitor.update_with_fio_data(f"✅ FIO process started (PID: {self.current_process.pid})")
                    
            except FileNotFoundError as e:
                if monitor:
                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                        terminal = monitor.parent_window.debug_terminal
                        terminal.log_error(f"FIO binary not found: {e}")
                    monitor.log_error(f"FileNotFoundError: {e}")
                return None
            except PermissionError as e:
                if monitor:
                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                        terminal = monitor.parent_window.debug_terminal
                        terminal.log_error(f"Permission denied for FIO binary: {e}")
                    monitor.log_error(f"PermissionError: {e}")
                return None
            except OSError as e:
                if monitor:
                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                        terminal = monitor.parent_window.debug_terminal
                        terminal.log_error(f"OS error starting FIO: {e}")
                    monitor.log_error(f"OSError: {e}")
                return None
            except Exception as e:
                if monitor:
                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                        terminal = monitor.parent_window.debug_terminal
                        terminal.log_error(f"Unexpected error starting FIO subprocess: {e}")
                        import traceback
                        terminal.log_error(f"Traceback: {traceback.format_exc()}")
                    monitor.log_error(f"Subprocess creation failed: {e}")
                return None
            
            json_buffer = []
            json_started = False
            
            # Enhanced debug logging for output reading
            if monitor:
                if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                    terminal = monitor.parent_window.debug_terminal
                    terminal.log_subprocess(f"Starting output reading loop...")
                    terminal.log_subprocess(f"Process PID: {self.current_process.pid}")
                    terminal.log_subprocess(f"Process poll status: {self.current_process.poll()}")
            
            # Read output in real-time with enhanced debugging
            loop_count = 0
            while True:
                loop_count += 1
                
                if self.stop_requested:
                    if monitor:
                        if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                            terminal = monitor.parent_window.debug_terminal
                            terminal.log_subprocess(f"Stop requested - terminating process")
                    self.current_process.terminate()
                    return None
                
                # Check process status
                poll_result = self.current_process.poll()
                if monitor and loop_count % 50 == 0:  # Log every 50 iterations
                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                        terminal = monitor.parent_window.debug_terminal
                        terminal.log_subprocess(f"Loop {loop_count}: Process poll = {poll_result}")
                
                reads = []
                if self.current_process.stdout:
                    reads.append(self.current_process.stdout.fileno())
                if self.current_process.stderr:
                    reads.append(self.current_process.stderr.fileno())
                
                if not reads:
                    if monitor:
                        if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                            terminal = monitor.parent_window.debug_terminal
                            terminal.log_error(f"No file descriptors available for reading")
                    break
                
                # Log file descriptors on first few iterations
                if monitor and loop_count <= 3:
                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                        terminal = monitor.parent_window.debug_terminal
                        terminal.log_subprocess(f"File descriptors for select(): {reads}")
                
                try:
                    ret = select.select(reads, [], [], 0.1)
                    
                    # Log select results on first few iterations
                    if monitor and loop_count <= 5 and ret[0]:
                        if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                            terminal = monitor.parent_window.debug_terminal
                            terminal.log_subprocess(f"select() returned: {ret[0]}")
                    
                except Exception as select_error:
                    if monitor:
                        if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                            terminal = monitor.parent_window.debug_terminal
                            terminal.log_error(f"select() error: {select_error}")
                    break
                
                if not ret[0] and poll_result is not None:
                    if monitor:
                        if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                            terminal = monitor.parent_window.debug_terminal
                            terminal.log_subprocess(f"Process finished (exit code: {poll_result}), breaking loop")
                    break
                
                for fd in ret[0]:
                    try:
                        if fd == self.current_process.stdout.fileno():
                            line = self.current_process.stdout.readline()
                            if line:
                                if monitor and loop_count <= 10:  # Log first few stdout lines
                                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                                        terminal = monitor.parent_window.debug_terminal
                                        terminal.log_subprocess(f"STDOUT: {line.strip()}")
                                
                                if line.strip().startswith('{'):
                                    json_started = True
                                if json_started:
                                    json_buffer.append(line)
                                if line.strip().endswith('}'):
                                    json_started = False
                                    
                        elif fd == self.current_process.stderr.fileno():
                            line = self.current_process.stderr.readline()
                            if line:
                                if monitor:
                                    if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                                        terminal = monitor.parent_window.debug_terminal
                                        terminal.log_stderr(f"STDERR: {line.strip()}")
                                    monitor.update_with_fio_data(line.strip())
                                    
                    except Exception as read_error:
                        if monitor:
                            if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                                terminal = monitor.parent_window.debug_terminal
                                terminal.log_error(f"Error reading from fd {fd}: {read_error}")
                
                if poll_result is not None and not json_started:
                    if monitor:
                        if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                            terminal = monitor.parent_window.debug_terminal
                            terminal.log_subprocess(f"Process finished and no JSON in progress, breaking")
                    break
                
                # Safety break for infinite loops
                if loop_count > 10000:
                    if monitor:
                        if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                            terminal = monitor.parent_window.debug_terminal
                            terminal.log_error(f"Breaking loop after {loop_count} iterations (safety)")
                    break
            
            if monitor:
                if hasattr(monitor, 'parent_window') and hasattr(monitor.parent_window, 'debug_terminal'):
                    terminal = monitor.parent_window.debug_terminal
                    terminal.log_subprocess(f"Output reading loop finished after {loop_count} iterations")
            
            self.current_process.wait()
            
            if self.current_process.returncode != 0:
                if monitor:
                    monitor.log_error(f"FIO process failed with return code {self.current_process.returncode}")
                return None
            
            # Parse JSON results
            full_json_output = "".join(json_buffer)
            if not full_json_output.strip():
                if monitor:
                    monitor.log_error("No JSON output from FIO")
                return None
            
            try:
                result_json = json.loads(full_json_output)
                return result_json
            except json.JSONDecodeError as e:
                if monitor:
                    monitor.log_error(f"Failed to parse FIO JSON output: {e}")
                return None
                
        except Exception as e:
            if monitor:
                monitor.log_error(f"FIO execution error: {e}")
            return None
        finally:
            self.current_process = None
    
    def _get_production_fio_parameters(self, test_mode: str, disk_path: str, test_size_gb: int):
        """Get production-ready FIO parameters for real QLab testing."""
        test_size_bytes = test_size_gb * 1024 * 1024 * 1024
        
        base_params = [
            self.fio_path,
            '--output-format=json',
            '--eta=never',
            f'--filename={disk_path}/qlab_fio_test_file',
            f'--size={test_size_bytes}',
            '--ioengine=psync',  # Use POSIX pread/pwrite - more compatible with macOS
            '--thread',  # Use threads instead of processes - avoids shared memory issues
        ]
        
        if test_mode == "setup_check":
            # Quick 30-second validation test
            return [
                base_params + [
                    '--name=setup_write',
                    '--rw=write',
                    '--bs=64k',
                    '--numjobs=1',
                    '--runtime=15',
                    '--time_based',
                    '--iodepth=1'
                ],
                base_params + [
                    '--name=setup_read',
                    '--rw=read',
                    '--bs=4k',
                    '--numjobs=1',
                    '--runtime=15',
                    '--time_based',
                    '--iodepth=1'
                ]
            ]
        
        elif test_mode == "qlab_pattern":
            # QLab ProRes 422 pattern (2.5 hours real test)
            return [
                base_params + [
                    '--name=qlab_prores_422_normal',
                    '--rw=read',
                    '--bs=1M',
                    '--numjobs=4',
                    '--time_based',
                    '--runtime=1800',  # 30 minutes
                    '--rate=656M',     # ProRes 422 baseline
                    '--iodepth=8'
                ],
                base_params + [
                    '--name=qlab_prores_422_crossfade',
                    '--rw=read',
                    '--bs=2M',
                    '--numjobs=6',
                    '--time_based',
                    '--runtime=5400',  # 1.5 hours
                    '--rate=2100M',    # Crossfade peaks
                    '--rate_process=poisson',
                    '--iodepth=16'
                ],
                base_params + [
                    '--name=qlab_prores_422_recovery',
                    '--rw=read',
                    '--bs=1M',
                    '--numjobs=4',
                    '--time_based',
                    '--runtime=1800',  # 30 minutes
                    '--rate=656M',
                    '--iodepth=8'
                ],
                base_params + [
                    '--name=qlab_prores_422_max_speed',
                    '--rw=read',
                    '--bs=4M',
                    '--numjobs=8',
                    '--time_based',
                    '--runtime=300',   # 5 minutes
                    '--iodepth=32'     # No rate limit - max speed
                ]
            ]
        
        elif test_mode == "qlab_hq_pattern":
            # QLab ProRes HQ pattern (2.5 hours real test)
            return [
                base_params + [
                    '--name=qlab_prores_hq_normal',
                    '--rw=read',
                    '--bs=1M',
                    '--numjobs=4',
                    '--time_based',
                    '--runtime=1800',  # 30 minutes
                    '--rate=950M',     # ProRes HQ baseline
                    '--iodepth=8'
                ],
                base_params + [
                    '--name=qlab_prores_hq_crossfade',
                    '--rw=read',
                    '--bs=2M',
                    '--numjobs=8',
                    '--time_based',
                    '--runtime=5400',  # 1.5 hours
                    '--rate=3200M',    # HQ Crossfade peaks
                    '--rate_process=poisson',
                    '--iodepth=24'
                ],
                base_params + [
                    '--name=qlab_prores_hq_recovery',
                    '--rw=read',
                    '--bs=1M',
                    '--numjobs=4',
                    '--time_based',
                    '--runtime=1800',  # 30 minutes
                    '--rate=950M',
                    '--iodepth=8'
                ],
                base_params + [
                    '--name=qlab_prores_hq_max_speed',
                    '--rw=read',
                    '--bs=4M',
                    '--numjobs=12',
                    '--time_based',
                    '--runtime=300',   # 5 minutes
                    '--iodepth=48'     # No rate limit - max speed
                ]
            ]
        
        elif test_mode == "baseline_streaming":
            # 2-hour sustained max throughput test
            return [
                base_params + [
                    '--name=baseline_streaming_max',
                    '--rw=read',
                    '--bs=4M',
                    '--numjobs=8',
                    '--time_based',
                    '--runtime=7200',  # 2 hours
                    '--iodepth=32'     # No rate limit - sustained max
                ]
            ]
        
        else:
            raise ValueError(f"Unknown test mode: {test_mode}")
    
    def stop_test(self):
        """Stop the currently running test."""
        self.stop_requested = True
        if self.current_process:
            try:
                self.current_process.terminate()
                # Give it 5 seconds to terminate gracefully
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                self.current_process.kill()
                self.current_process.wait()
    
    def cleanup_test_files(self, disk_path: str):
        """Clean up FIO test files."""
        test_file = os.path.join(disk_path, 'qlab_fio_test_file')
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
                print(f"Cleaned up FIO test file: {test_file}")
            except Exception as e:
                print(f"Error cleaning up test file: {e}")

if __name__ == "__main__":
    # Test FIO manager
    manager = FioManager()
    status = manager.get_fio_status()
    print("FIO Status:", json.dumps(status, indent=2))
    
    if status['available']:
        print("FIO is ready for production testing!")
    else:
        print("FIO not available - no real tests possible")
