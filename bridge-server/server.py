#!/usr/bin/env python3
"""
QLab Disk Performance Tester - Communication Bridge Server

This server provides a bridge between the web GUI and the diskbench helper binary.
It runs a local HTTP server that accepts requests from the web interface and
executes the appropriate diskbench commands.
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
import fcntl
import signal
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

# Add diskbench to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'diskbench'))

class DiskBenchBridge:
    """Bridge between web GUI and diskbench helper binary."""
    
    def __init__(self):
        self.diskbench_path = os.path.join(os.path.dirname(__file__), '..', 'diskbench')
        self.running_tests = {}
        self.running_processes = {}  # Track actual subprocess objects
        self.logger = logging.getLogger(__name__)
        self.state_file = 'memory-bank/diskbench_bridge_state.json'
        
        # Load persistent state on startup
        self._load_persistent_state()
        
        # Discover and cleanup orphaned processes on startup
        self._discover_orphaned_processes()
    
    def _load_persistent_state(self):
        """Load persistent test state from disk."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                # Restore running tests state
                self.running_tests = state_data.get('running_tests', {})
                
                # Mark all previously running tests as 'disconnected' since we lost the process handles
                for test_id, test_info in self.running_tests.items():
                    if test_info.get('status') == 'running':
                        test_info['status'] = 'disconnected'
                        test_info['disconnected_time'] = datetime.now().isoformat()
                
                self.logger.info(f"Loaded persistent state: {len(self.running_tests)} tests")
                
                # Save updated state
                self._save_persistent_state()
            else:
                self.logger.info("No persistent state file found - starting fresh")
                
        except Exception as e:
            self.logger.error(f"Failed to load persistent state: {e}")
            self.running_tests = {}
    
    def _save_persistent_state(self):
        """Save current test state to disk."""
        try:
            state_data = {
                'running_tests': self.running_tests,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save persistent state: {e}")
    
    def _discover_orphaned_processes(self):
        """Discover and handle orphaned FIO processes on startup."""
        try:
            self.logger.info("Discovering orphaned processes on startup...")
            
            # Find any disconnected tests
            disconnected_tests = [tid for tid, info in self.running_tests.items() 
                                 if info.get('status') == 'disconnected']
            
            if disconnected_tests:
                self.logger.warning(f"Found {len(disconnected_tests)} disconnected tests: {disconnected_tests}")
                
                # Try to find corresponding FIO processes
                orphaned_pids = self.cleanup_fio_processes()
                
                if orphaned_pids:
                    self.logger.info(f"Cleaned up {len(orphaned_pids)} orphaned FIO processes")
                    
                    # Mark disconnected tests as stopped
                    for test_id in disconnected_tests:
                        self.running_tests[test_id]['status'] = 'stopped'
                        self.running_tests[test_id]['error'] = f'Process orphaned during server restart - cleaned up {len(orphaned_pids)} FIO processes'
                        self.running_tests[test_id]['end_time'] = datetime.now().isoformat()
                else:
                    # No orphaned processes found - tests may have completed
                    for test_id in disconnected_tests:
                        self.running_tests[test_id]['status'] = 'unknown'
                        self.running_tests[test_id]['error'] = 'Test status unknown after server restart'
                        self.running_tests[test_id]['end_time'] = datetime.now().isoformat()
                
                # Save updated state
                self._save_persistent_state()
            else:
                self.logger.info("No disconnected tests found")
                
        except Exception as e:
            self.logger.error(f"Error discovering orphaned processes: {e}")
    
    def get_background_tests_status(self):
        """Get status of all background/disconnected tests."""
        try:
            background_tests = []
            
            for test_id, test_info in self.running_tests.items():
                if test_info.get('status') in ['disconnected', 'unknown']:
                    background_tests.append({
                        'test_id': test_id,
                        'status': test_info.get('status'),
                        'start_time': test_info.get('start_time'),
                        'disconnected_time': test_info.get('disconnected_time'),
                        'test_type': test_info.get('diskbench_test_type'),
                        'disk_path': test_info.get('params', {}).get('disk_path'),
                        'error': test_info.get('error')
                    })
            
            return {
                'success': True,
                'background_tests': background_tests,
                'count': len(background_tests)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_background_test(self, test_id):
        """Clean up a specific background/disconnected test."""
        try:
            if test_id not in self.running_tests:
                return {
                    'success': False,
                    'error': 'Test not found'
                }
            
            test_info = self.running_tests[test_id]
            
            if test_info.get('status') not in ['disconnected', 'unknown']:
                return {
                    'success': False,
                    'error': f'Test is not in background state (status: {test_info.get("status")})'
                }
            
            # Try to find and kill any related FIO processes
            killed_pids = self.cleanup_fio_processes(test_id)
            
            # Remove from running tests
            del self.running_tests[test_id]
            
            # Save state
            self._save_persistent_state()
            
            message = f'Background test {test_id} cleaned up'
            if killed_pids:
                message += f' (killed {len(killed_pids)} FIO processes)'
            
            return {
                'success': True,
                'message': message,
                'killed_pids': killed_pids
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_all_background_tests(self):
        """Clean up all background/disconnected tests."""
        try:
            background_test_ids = [tid for tid, info in self.running_tests.items() 
                                  if info.get('status') in ['disconnected', 'unknown']]
            
            if not background_test_ids:
                return {
                    'success': True,
                    'message': 'No background tests to clean up',
                    'cleaned_tests': []
                }
            
            cleaned_tests = []
            total_killed_pids = []
            
            for test_id in background_test_ids:
                result = self.cleanup_background_test(test_id)
                if result.get('success'):
                    cleaned_tests.append(test_id)
                    if result.get('killed_pids'):
                        total_killed_pids.extend(result['killed_pids'])
            
            # Run final FIO cleanup
            final_killed_pids = self.cleanup_fio_processes()
            total_killed_pids.extend(final_killed_pids)
            
            message = f'Cleaned up {len(cleaned_tests)} background tests'
            if total_killed_pids:
                message += f' and {len(total_killed_pids)} FIO processes'
            
            return {
                'success': True,
                'message': message,
                'cleaned_tests': cleaned_tests,
                'killed_pids': total_killed_pids
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_json_from_output(self, output):
        """Extract JSON from mixed output (logs + JSON)."""
        try:
            # Find the first line that starts with '{' - this should be the JSON
            lines = output.split('\n')
            json_start = -1
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('{'):
                    json_start = i
                    break
            
            if json_start >= 0:
                # Join all lines from the JSON start
                json_lines = lines[json_start:]
                json_text = '\n'.join(json_lines)
                
                # Try to find the end of the JSON by counting braces
                brace_count = 0
                json_end = 0
                
                for i, char in enumerate(json_text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > 0:
                    return json_text[:json_end]
                else:
                    return json_text
            else:
                # No JSON found, return original output
                return output
                
        except Exception as e:
            self.logger.warning(f"Failed to extract JSON from output: {e}")
            return output

    def execute_diskbench_command(self, args, estimated_duration: int = 0, log_callback=None):
        """Execute a diskbench command and return the result."""
        try:
            # Build command
            cmd = [sys.executable, 'main.py'] + args
            
            # Add estimated duration to args if provided and not already present
            if estimated_duration > 0 and '--estimated-duration' not in args:
                cmd.extend(['--estimated-duration', str(estimated_duration)])
            
            cmd_str = ' '.join(cmd)
            
            if log_callback:
                log_callback('info', f"Executing command: {cmd_str}")
                log_callback('info', f"Working directory: {self.diskbench_path}")
                log_callback('info', f"Process context: Unsandboxed bridge server (PID: {os.getpid()})")
            
            # Only log to file/console, not to stdout that might contaminate JSON
            self.logger.debug(f"Executing: {cmd_str} in {self.diskbench_path}")
            
            # Set up environment for unsandboxed FIO execution
            env = os.environ.copy()
            env['FIO_DISABLE_SHM'] = '1'  # Disable shared memory
            env['TMPDIR'] = '/tmp'        # Use system tmp directory
            env['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"  # Ensure Homebrew FIO is found
            
            if log_callback:
                log_callback('info', f"Environment: FIO_DISABLE_SHM=1, TMPDIR=/tmp")
                log_callback('info', f"PATH includes: /opt/homebrew/bin:/usr/local/bin")
            
            # Execute in diskbench directory with unsandboxed environment
            # Timeout based on test type - long tests need more time
            timeout_seconds = 300  # Default 5 minutes
            if '--test' in args:
                test_idx = args.index('--test')
                if test_idx + 1 < len(args):
                    test_type = args[test_idx + 1]
                    if 'show' in test_type:
                        timeout_seconds = 11000  # 3+ hours for show tests
                    elif 'max_sustained' in test_type:
                        timeout_seconds = 6000   # 1.7 hours for sustained tests
            
            result = subprocess.run(
                cmd,
                cwd=self.diskbench_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env      # Use unsandboxed environment
            )
            
            if log_callback:
                log_callback('info', f"Command completed with return code: {result.returncode}")
                if result.stdout:
                    log_callback('stdout', f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    log_callback('stderr', f"STDERR:\n{result.stderr}")
            
            self.logger.info(f"Command result: returncode={result.returncode}")
            if result.stdout:
                self.logger.info(f"STDOUT: {result.stdout}")
            if result.stderr:
                self.logger.info(f"STDERR: {result.stderr}")
            
            if result.returncode == 0:
                # Clean stdout by extracting only the JSON part
                stdout_clean = self._extract_json_from_output(result.stdout)
                
                # Try to parse as JSON if possible
                try:
                    json_result = json.loads(stdout_clean)
                    # If JSON parsing succeeds, use the JSON result
                    return json_result
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    return {
                        'success': True,
                        'output': stdout_clean,
                        'stderr': result.stderr,
                        'command': cmd_str,
                        'returncode': result.returncode
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout,
                    'returncode': result.returncode,
                    'command': cmd_str
                }
                
        except subprocess.TimeoutExpired:
            timeout_hours = timeout_seconds / 3600
            error_msg = f'Command timed out after {timeout_hours:.1f} hours: {cmd_str}'
            if log_callback:
                log_callback('error', error_msg)
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'command': cmd_str
            }
        except Exception as e:
            error_msg = f'Command execution failed: {str(e)}'
            if log_callback:
                log_callback('error', error_msg)
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'command': cmd_str if 'cmd_str' in locals() else str(cmd)
            }
    
    def start_test(self, test_params):
        """Start a disk performance test with single-instance enforcement."""
        try:
            # Check for running tests - only allow one test at a time
            running_test_ids = [tid for tid, info in self.running_tests.items() 
                               if info.get('status') == 'running']
            
            if running_test_ids:
                return {
                    'success': False,
                    'error': f'Test already running (ID: {running_test_ids[0]}). Stop current test before starting a new one.'
                }
            
            # Generate unique test ID
            test_id = f"test_{int(time.time())}"
            
            # Map test types from web GUI to diskbench - using correct diskbench test names
            test_type_mapping = {
                'quick_max_speed': 'quick_max_speed',
                'qlab_prores_422_show': 'qlab_prores_422_show',
                'qlab_prores_hq_show': 'qlab_prores_hq_show',
                'max_sustained': 'max_sustained'
            }
            
            diskbench_test_type = test_type_mapping.get(
                test_params.get('test_type', 'quick_max_speed'), 
                'quick_max_speed'
            )
            
            # Build command arguments
            args = [
                '--test', diskbench_test_type,
                '--disk', test_params.get('disk_path', '/tmp'),
                '--size', str(test_params.get('size_gb', 1)),
                '--json'
            ]
            
            # Add output file
            output_file = f"/tmp/diskbench-{test_id}.json"
            args.extend(['--output', output_file])
            
            # Add progress flag
            if test_params.get('show_progress', True):
                args.append('--progress')
            
            # Add verbose flag for debugging
            args.append('--verbose')
            
            # Determine estimated duration based on test type
            estimated_duration = 0
            if diskbench_test_type == 'quick_max_speed':
                estimated_duration = 60   # 1 minute
            elif diskbench_test_type == 'qlab_prores_422_show':
                estimated_duration = 9300  # 2.5 hours
            elif diskbench_test_type == 'qlab_prores_hq_show':
                estimated_duration = 9300  # 2.5 hours
            elif diskbench_test_type == 'max_sustained':
                estimated_duration = 5400  # 1.5 hours
            else:
                estimated_duration = 60   # Default to 1 minute for unknown tests

            # Store test info
            self.running_tests[test_id] = {
                'status': 'starting',
                'start_time': datetime.now().isoformat(),
                'params': test_params,
                'output_file': output_file,
                'progress': 0,
                'diskbench_test_type': diskbench_test_type,
                'estimated_duration': estimated_duration # Store estimated duration
            }
            
            # Start test in background thread
            thread = threading.Thread(
                target=self._run_test_thread,
                args=(test_id, args, estimated_duration) # Pass estimated duration
            )
            thread.daemon = True
            thread.start()
            
            return {
                'success': True,
                'test_id': test_id,
                'status': 'started',
                'diskbench_test_type': diskbench_test_type,
                'estimated_duration': estimated_duration
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_fio_processes(self, test_id=None):
        """Find and kill orphaned FIO processes related to our tests."""
        try:
            self.logger.info("Searching for orphaned FIO processes...")
            
            # Get all running processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.logger.warning("Failed to get process list")
                return []
            
            killed_pids = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'fio' in line and ('diskbench-test_' in line or '/tmp/diskbench-' in line):
                    # This looks like one of our FIO processes
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            self.logger.info(f"Found orphaned FIO process: PID {pid}")
                            self.logger.info(f"Command line: {' '.join(parts[10:])}")
                            
                            # Kill the process
                            try:
                                os.kill(pid, 15)  # SIGTERM first
                                time.sleep(2)
                                
                                # Check if still running
                                try:
                                    os.kill(pid, 0)  # Check if process exists
                                    # Still running, force kill
                                    os.kill(pid, 9)  # SIGKILL
                                    self.logger.info(f"Force killed FIO process PID {pid}")
                                except ProcessLookupError:
                                    # Process already terminated
                                    self.logger.info(f"FIO process PID {pid} terminated gracefully")
                                
                                killed_pids.append(pid)
                                
                            except ProcessLookupError:
                                # Process already gone
                                self.logger.info(f"FIO process PID {pid} already terminated")
                            except PermissionError:
                                self.logger.warning(f"Permission denied killing FIO process PID {pid}")
                                
                        except ValueError:
                            # Invalid PID
                            continue
            
            if killed_pids:
                self.logger.info(f"Cleaned up {len(killed_pids)} orphaned FIO processes: {killed_pids}")
            else:
                self.logger.info("No orphaned FIO processes found")
                
            return killed_pids
            
        except Exception as e:
            self.logger.error(f"Error cleaning up FIO processes: {e}")
            return []
    
    def stop_test(self, test_id):
        """Stop a running test and cleanup processes."""
        try:
            if test_id not in self.running_tests:
                return {
                    'success': False,
                    'error': 'Test not found'
                }
            
            test_info = self.running_tests[test_id]
            
            if test_info.get('status') != 'running':
                return {
                    'success': False,
                    'error': f'Test is not running (status: {test_info.get("status")})'
                }
            
            # Try to terminate the tracked process first
            process_killed = False
            if test_id in self.running_processes:
                process = self.running_processes[test_id]
                
                self.logger.info(f"Stopping test {test_id} (PID: {process.pid}, PGID: {os.getpgid(process.pid)})")
                
                try:
                    # Kill the entire process group to ensure fio is terminated
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    time.sleep(2) # Give it time to die
                    # Check if it's still alive
                    os.killpg(os.getpgid(process.pid), 0)
                    # If it is, kill it with fire
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    self.logger.info(f"Force-killed process group for test {test_id}")
                    process_killed = True
                except (ProcessLookupError, OSError):
                    # Process group is already gone
                    self.logger.info(f"Process group for test {test_id} terminated gracefully.")
                    process_killed = True
                except Exception as e:
                    self.logger.error(f"Error stopping process group for test {test_id}: {e}")

                # Clean up process tracking
                del self.running_processes[test_id]
            
            # Always run FIO cleanup to catch any orphaned processes
            self.logger.info(f"Running FIO cleanup for test {test_id}...")
            killed_pids = self.cleanup_fio_processes(test_id)
            
            # Update test status
            self.running_tests[test_id]['status'] = 'stopped'
            self.running_tests[test_id]['end_time'] = datetime.now().isoformat()
            self.running_tests[test_id]['error'] = 'Test stopped by user'
            
            # Build success message
            if process_killed and killed_pids:
                message = f'Test {test_id} stopped successfully. Killed tracked process and {len(killed_pids)} orphaned FIO processes.'
            elif process_killed:
                message = f'Test {test_id} stopped successfully. Killed tracked process.'
            elif killed_pids:
                message = f'Test {test_id} stopped. Killed {len(killed_pids)} orphaned FIO processes.'
            else:
                message = f'Test {test_id} marked as stopped.'
            
            return {
                'success': True,
                'message': message,
                'killed_pids': killed_pids
            }
                
        except Exception as e:
            self.logger.error(f"Exception stopping test {test_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_all_tests(self):
        """Stop all running tests and cleanup processes."""
        try:
            stopped_tests = []
            errors = []
            total_killed_pids = []
            
            # Find all running tests
            running_test_ids = [tid for tid, info in self.running_tests.items() 
                               if info.get('status') == 'running']
            
            if not running_test_ids:
                # Even if no tracked tests, run FIO cleanup to catch orphaned processes
                self.logger.info("No tracked running tests, but checking for orphaned FIO processes...")
                killed_pids = self.cleanup_fio_processes()
                
                if killed_pids:
                    return {
                        'success': True,
                        'message': f'No tracked tests running, but cleaned up {len(killed_pids)} orphaned FIO processes',
                        'stopped_tests': [],
                        'killed_pids': killed_pids
                    }
                else:
                    return {
                        'success': True,
                        'message': 'No running tests to stop',
                        'stopped_tests': []
                    }
            
            # Stop each running test
            for test_id in running_test_ids:
                result = self.stop_test(test_id)
                if result.get('success'):
                    stopped_tests.append(test_id)
                    if result.get('killed_pids'):
                        total_killed_pids.extend(result['killed_pids'])
                else:
                    errors.append(f"Test {test_id}: {result.get('error')}")
            
            # Run one final FIO cleanup to catch any remaining orphaned processes
            self.logger.info("Running final FIO cleanup after stopping all tests...")
            final_killed_pids = self.cleanup_fio_processes()
            total_killed_pids.extend(final_killed_pids)
            
            if errors:
                return {
                    'success': False,
                    'error': f'Some tests failed to stop: {"; ".join(errors)}',
                    'stopped_tests': stopped_tests,
                    'killed_pids': total_killed_pids
                }
            else:
                message = f'Successfully stopped {len(stopped_tests)} tests'
                if total_killed_pids:
                    message += f' and cleaned up {len(total_killed_pids)} FIO processes'
                
                return {
                    'success': True,
                    'message': message,
                    'stopped_tests': stopped_tests,
                    'killed_pids': total_killed_pids
                }
                
        except Exception as e:
            self.logger.error(f"Exception stopping all tests: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _run_test_thread(self, test_id, args, estimated_duration: int):
        """Run test in background thread with enhanced live progress monitoring."""
        process = None
        try:
            self.running_tests[test_id]['status'] = 'running'
            self.running_tests[test_id]['live_metrics'] = {}
            self.running_tests[test_id]['current_phase'] = 'initializing'
            self.logger.info(f"Starting test {test_id} with args: {args}, estimated_duration: {estimated_duration}s")
            
            # Build command
            cmd = [sys.executable, 'main.py'] + args
            
            # Set up environment for unsandboxed FIO execution
            env = os.environ.copy()
            env['FIO_DISABLE_SHM'] = '1'
            env['TMPDIR'] = '/tmp'
            env['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
            
            # Start process with process tracking
            process = subprocess.Popen(
                cmd,
                cwd=self.diskbench_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                start_new_session=True # Detach from parent process group
            )
            
            # Store process for potential termination
            self.running_processes[test_id] = process
            self.logger.info(f"Test {test_id} started with PID: {process.pid}")
            
            # Wait for completion with timeout based on test type
            timeout_seconds = estimated_duration + 120  # Add a 2-minute buffer
            
            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                
                # Process completed successfully
                result = {
                    'success': process.returncode == 0,
                    'output': stdout,
                    'stderr': stderr,
                    'returncode': process.returncode
                }
                
                if process.returncode == 0:
                    # Try to load results from output file
                    output_file = self.running_tests[test_id]['output_file']
                    try:
                        if os.path.exists(output_file):
                            with open(output_file, 'r') as f:
                                file_results = json.load(f)
                            self.running_tests[test_id]['result'] = file_results
                            self.logger.info(f"Loaded test results from {output_file}")
                        else:
                            # Use command output if file doesn't exist
                            self.running_tests[test_id]['result'] = result
                            self.logger.warning(f"Output file {output_file} not found, using command output")
                    except Exception as e:
                        self.logger.error(f"Failed to load results from {output_file}: {e}")
                        self.running_tests[test_id]['result'] = result
                    
                    self.running_tests[test_id]['status'] = 'completed'
                    self.running_tests[test_id]['progress'] = 100
                    self.running_tests[test_id]['current_phase'] = 'completed'
                    self._save_persistent_state()
                else:
                    self.running_tests[test_id]['status'] = 'failed'
                    self.running_tests[test_id]['error'] = stderr or stdout or 'Unknown error'
                    self.running_tests[test_id]['current_phase'] = 'failed'
                    self.logger.error(f"Test {test_id} failed: {stderr}")
                
            except subprocess.TimeoutExpired:
                # Test timed out - terminate the process
                self.logger.warning(f"Test {test_id} timed out after {timeout_seconds} seconds")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Force killing test {test_id}")
                    process.kill()
                    process.wait()
                
                self.running_tests[test_id]['status'] = 'timeout'
                self.running_tests[test_id]['error'] = f'Test timed out after {timeout_seconds} seconds'
                self.running_tests[test_id]['current_phase'] = 'timeout'
                
        except Exception as e:
            self.running_tests[test_id]['status'] = 'failed'
            self.running_tests[test_id]['error'] = str(e)
            self.running_tests[test_id]['current_phase'] = 'failed'
            self.logger.error(f"Exception in test {test_id}: {e}")
            
            # Ensure process is terminated on exception
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                        process.wait()
                    except:
                        pass
        
        finally:
            # Cleanup process tracking
            if test_id in self.running_processes:
                del self.running_processes[test_id]
            
            self.running_tests[test_id]['end_time'] = datetime.now().isoformat()
            self.logger.info(f"Test {test_id} thread completed")
    
    def get_current_test(self):
        """Get the currently running or disconnected test, if any."""
        for test_id, test_info in self.running_tests.items():
            if test_info.get('status') in ['running', 'disconnected']:
                return {
                    'success': True,
                    'test_running': True,
                    'test_info': self.get_test_status(test_id).get('test_info')
                }
        return {'success': True, 'test_running': False}

    def get_test_status(self, test_id):
        """Get enhanced status of a running test with QLab metrics."""
        if test_id not in self.running_tests:
            return {
                'success': False,
                'error': 'Test not found'
            }
        
        test_info = self.running_tests[test_id].copy()
        
        # Enhanced progress calculation for running tests
        if test_info['status'] == 'running':
            elapsed = time.time() - time.mktime(
                datetime.fromisoformat(test_info['start_time']).timetuple()
            )
            test_type = test_info.get('diskbench_test_type', 'quick_max_speed')
            
            # Calculate accurate progress and remaining time
            if test_type == 'qlab_prores_422_show':
                estimated_duration = 9300  # 2.5 hours for ProRes 422 show tests
            elif test_type == 'qlab_prores_hq_show':
                estimated_duration = 9300  # 2.5 hours for ProRes HQ show tests
            elif test_type == 'max_sustained':
                estimated_duration = 5400  # 1.5 hours for sustained tests
            elif test_type == 'quick_max_speed':
                estimated_duration = 60    # 1 minute for quick tests
            else:
                estimated_duration = 60    # Default to 1 minute for unknown tests
            
            progress = min(95, (elapsed / estimated_duration) * 100)
            remaining_time = max(0, estimated_duration - elapsed)
            
            # Enhanced test info with QLab metrics
            test_info.update({
                'progress': progress,
                'elapsed_time': elapsed,
                'remaining_time': remaining_time,
                'estimated_duration': estimated_duration,
                'live_metrics': self._get_live_test_metrics(test_id, test_type, elapsed),
                'qlab_analysis': self._get_qlab_performance_analysis(test_id, test_type, elapsed)
            })
        
        return {
            'success': True,
            'test_info': test_info
        }
    
    def _get_live_test_metrics(self, test_id, test_type, elapsed):
        """Get live performance metrics from actual FIO output with correct status messages."""
        # Generate appropriate status messages based on test type
        if test_type == 'quick_max_speed':
            # Simple 3-minute read speed test
            return {
                'status': 'measuring_max_read_speed',
                'message': f'⚡ Quick Max Speed Test ({elapsed:.0f}s)',
                'description': 'Maximum sequential read speed measurement',
                'phase': 'Single continuous read test',
                'elapsed_time': elapsed,
                'test_type': test_type
            }
        elif 'show' in test_type:
            # Show pattern tests (2.75 hours)
            if elapsed < 1800:  # First 30 minutes
                phase = "Show Preparation"
                description = "Media preload and setup"
            elif elapsed < 7200:  # Next 90 minutes
                phase = "Normal Show Operation" 
                description = "1x4K + 3xHD ProRes continuous playback"
            else:  # Final 30 minutes
                phase = "Show Finale"
                description = "Intensive crossfades and maximum load"
            
            codec = "422" if "422" in test_type else "HQ"
            return {
                'status': 'running_show_pattern',
                'message': f'🎥 {phase} ({elapsed//60:.0f}m {elapsed%60:.0f}s)',
                'description': f'ProRes {codec} show pattern - {description}',
                'phase': phase,
                'elapsed_time': elapsed,
                'test_type': test_type
            }
        elif test_type == 'max_sustained':
            # Sustained performance test (1.5 hours)
            return {
                'status': 'thermal_endurance_test',
                'message': f'🔥 Sustained Performance Test ({elapsed//60:.0f}m {elapsed%60:.0f}s)',
                'description': 'Maximum sustained load for thermal testing',
                'phase': 'Continuous maximum performance',
                'elapsed_time': elapsed,
                'test_type': test_type
            }
        else:
            # Fallback for unknown test types
            return {
                'status': 'running_test',
                'message': f'🔍 Running Test ({elapsed:.0f}s)',
                'description': f'Performance test: {test_type}',
                'phase': 'Test in progress',
                'elapsed_time': elapsed,
                'test_type': test_type
            }
    
    def _get_qlab_performance_analysis(self, test_id, test_type, elapsed):
        """Generate QLab-specific performance analysis."""
        # QLab requirements for different scenarios
        qlab_requirements = {
            'qlab_prores_422_show': {'min_throughput': 220, 'name': 'ProRes 422'},
            'qlab_prores_hq_show': {'min_throughput': 440, 'name': 'ProRes HQ'},
            'quick_max_speed': {'min_throughput': 100, 'name': 'Basic'},
            'max_sustained': {'min_throughput': 300, 'name': 'Sustained'}
        }
        
        requirement = qlab_requirements.get(test_type, qlab_requirements['quick_max_speed'])
        min_required = requirement['min_throughput']
        
        # Since we removed temperature monitoring and live metrics, return placeholder analysis
        return {
            'status': 'pending',
            'status_message': '⏳ Waiting for real test data',
            'requirement_name': requirement['name'],
            'min_required_mbps': min_required,
            'current_margin_percent': 0,
            'min_margin_percent': 0,
            'consistency_score': 100,
            'stutters': 0,
            'dropouts': 0,
            'show_ready': False,
            'note': 'Real performance analysis will be available from FIO test results'
        }
    
    def list_disks(self):
        """List available disks."""
        return self.execute_diskbench_command(['--list-disks', '--json'])
    
    def validate_system(self):
        """Validate system requirements."""
        return self.execute_diskbench_command(['--validate', '--json'])
    
    def get_version(self):
        """Get diskbench version."""
        return self.execute_diskbench_command(['--version'])
    
    def detect_system_status(self):
        """Detect system status and FIO availability."""
        return self.execute_diskbench_command(['--detect', '--json'])
    
    def install_fio(self):
        """Install or fix FIO for macOS."""
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        result = self.execute_diskbench_command(['--install', '--json'], log_callback)
        
        # Add logs to the result
        if isinstance(result, dict):
            result['logs'] = logs
        else:
            result = {
                'success': False,
                'error': 'Unknown result format',
                'logs': logs
            }
        
        return result
    
    def validate_setup(self):
        """Run setup validation tests."""
        result = self.execute_diskbench_command(['--validate', '--json'])
        
        # Transform the validation result to match web GUI expectations
        if result and result.get('checks'):
            tests = []
            for check_name, check_data in result['checks'].items():
                tests.append({
                    'name': check_name.replace('_', ' ').title(),
                    'passed': check_data.get('passed', False),
                    'result': check_data.get('message', 'Unknown')
                })
            
            return {
                'success': True,
                'tests': tests,
                'overall_status': result.get('overall_status', 'unknown')
            }
        elif result and result.get('success') is False:
            return result
        else:
            return {
                'success': False,
                'error': 'Invalid validation result format'
            }
    
    def test_fio_functionality(self):
        """Test FIO functionality from unsandboxed bridge server."""
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        try:
            log_callback('info', 'Starting FIO functionality test from bridge server')
            log_callback('info', f'Process context: Unsandboxed bridge server (PID: {os.getpid()})')
            
            # Find FIO binary
            fio_paths = [
                '/opt/homebrew/bin/fio',  # Apple Silicon Homebrew
                '/usr/local/bin/fio',     # Intel Homebrew
            ]
            
            fio_path = None
            for path in fio_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    fio_path = path
                    break
            
            if not fio_path:
                # Try system PATH
                import shutil
                fio_path = shutil.which('fio')
            
            if not fio_path:
                log_callback('error', 'FIO binary not found')
                return {
                    'success': False,
                    'error': 'FIO binary not found',
                    'logs': logs
                }
            
            log_callback('info', f'Found FIO at: {fio_path}')
            
            # Create test file
            test_file = '/tmp/fio_bridge_test_file'
            log_callback('info', f'Creating test file: {test_file}')
            
            with open(test_file, 'wb') as f:
                f.write(b'0' * (1024 * 1024))  # 1MB file
            
            try:
                # Set up environment for unsandboxed FIO execution
                env = os.environ.copy()
                env['FIO_DISABLE_SHM'] = '1'  # Disable shared memory
                env['TMPDIR'] = '/tmp'        # Use system tmp directory
                env['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
                
                log_callback('info', 'Environment: FIO_DISABLE_SHM=1, TMPDIR=/tmp')
                
                # Build FIO command with maximum shared memory avoidance
                fio_cmd = [
                    fio_path,
                    '--name=bridge_test',
                    f'--filename={test_file}',
                    '--size=1M',
                    '--bs=4k',
                    '--rw=read',
                    '--runtime=3',
                    '--time_based=1',
                    '--ioengine=sync',
                    '--direct=0',
                    '--numjobs=1',
                    '--group_reporting=1',
                    '--output-format=json',
                    '--disable_lat=1',      # Disable latency stats (uses shared memory)
                    '--disable_clat=1',     # Disable completion latency
                    '--disable_slat=1',     # Disable submission latency
                    '--disable_bw_measurement=1',  # Disable bandwidth measurement
                    '--minimal',            # Minimal output
                    '--thread'              # Use threads instead of processes
                ]
                
                log_callback('info', f'Executing FIO command: {" ".join(fio_cmd)}')
                
                # Run FIO test
                result = subprocess.run(
                    fio_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env
                )
                
                log_callback('info', f'FIO test completed with return code: {result.returncode}')
                
                if result.stdout:
                    log_callback('info', f'FIO STDOUT: {result.stdout[:500]}...')
                if result.stderr:
                    log_callback('warning', f'FIO STDERR: {result.stderr}')
                
                if result.returncode == 0:
                    log_callback('info', 'FIO functionality test: PASSED')
                    return {
                        'success': True,
                        'message': 'FIO functionality test passed',
                        'fio_path': fio_path,
                        'test_output': result.stdout,
                        'logs': logs
                    }
                else:
                    # Report honest FIO error - no fallback
                    if 'failed to setup shm segment' in result.stderr:
                        log_callback('error', 'FIO failed: shared memory limitations on macOS')
                        log_callback('error', 'FIO cannot be used reliably on this system')
                        return {
                            'success': False,
                            'error': 'FIO has shared memory limitations on macOS',
                            'fio_path': fio_path,
                            'fio_limited': True,
                            'stderr': result.stderr,
                            'logs': logs
                        }
                    else:
                        log_callback('error', f'FIO test failed with return code {result.returncode}')
                        return {
                            'success': False,
                            'error': f'FIO test failed: {result.stderr}',
                            'fio_path': fio_path,
                            'logs': logs
                        }
                    
            finally:
                # Clean up test file
                if os.path.exists(test_file):
                    os.remove(test_file)
                    log_callback('info', 'Test file cleaned up')
                    
        except Exception as e:
            log_callback('error', f'FIO functionality test exception: {e}')
            return {
                'success': False,
                'error': str(e),
                'logs': logs
            }
    
    def run_direct_fio_test(self, test_params=None):
        """
        Run direct FIO test with recommended macOS-safe parameters.
        Bypasses diskbench completely - direct FIO execution from bridge server.
        """
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        try:
            log_callback('info', '🚀 Starting DIRECT FIO test from bridge server')
            log_callback('info', f'Process context: Unsandboxed bridge server (PID: {os.getpid()})')
            log_callback('info', 'Using recommended macOS-safe FIO parameters')
            
            # Parse test parameters
            if test_params is None:
                test_params = {}
            
            test_size = test_params.get('size', '100M')
            test_type = test_params.get('rw', 'read')
            target_path = test_params.get('target_path', '/tmp')
            duration = test_params.get('duration', None)
            
            log_callback('info', f'Test parameters: size={test_size}, rw={test_type}, target={target_path}')
            
            # Find FIO binary
            fio_paths = [
                '/opt/homebrew/bin/fio',  # Apple Silicon Homebrew
                '/usr/local/bin/fio',     # Intel Homebrew
            ]
            
            fio_path = None
            for path in fio_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    fio_path = path
                    break
            
            if not fio_path:
                # Try system PATH
                import shutil
                fio_path = shutil.which('fio')
            
            if not fio_path:
                log_callback('error', 'FIO binary not found - install with: brew install fio')
                return {
                    'success': False,
                    'error': 'FIO binary not found',
                    'logs': logs
                }
            
            log_callback('info', f'✅ Found FIO at: {fio_path}')
            
            # Create test file path
            if target_path.startswith('/dev/'):
                # For raw devices, create test file in /tmp
                test_file = f'/tmp/direct_fio_test_{test_size}'
            else:
                # For mounted volumes, create test file on the volume
                test_file = f'{target_path}/direct_fio_test_{test_size}'
            
            log_callback('info', f'Test file: {test_file}')
            
            try:
                # Set up environment for unsandboxed FIO execution
                env = os.environ.copy()
                env['FIO_DISABLE_SHM'] = '1'  # Disable shared memory
                env['TMPDIR'] = '/tmp'        # Use system tmp directory
                env['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
                
                log_callback('info', '🔧 Environment: FIO_DISABLE_SHM=1, TMPDIR=/tmp')
                log_callback('info', f'PATH includes: /opt/homebrew/bin:/usr/local/bin')
                
                # Build FIO command with user's recommended macOS-safe parameters
                fio_cmd = [
                    fio_path,
                    '--name=direct_test',
                    f'--filename={test_file}',
                    f'--size={test_size}',
                    f'--rw={test_type}',
                    '--ioengine=posix',     # User's recommended parameter
                    '--direct=0',           # User's recommended parameter
                    '--output-format=json'  # User's recommended parameter
                ]
                
                # Add duration if specified (for longer tests)
                if duration:
                    fio_cmd.extend([
                        f'--runtime={duration}',
                        '--time_based=1'
                    ])
                
                # Additional macOS-safe parameters
                fio_cmd.extend([
                    '--numjobs=1',
                    '--group_reporting=1'
                ])
                
                log_callback('info', f'🚀 Executing FIO command: {" ".join(fio_cmd)}')
                
                # Run FIO test
                start_time = time.time()
                
                result = subprocess.run(
                    fio_cmd,
                    capture_output=True,
                    text=True,
                    timeout=duration + 60 if duration else 120,  # Timeout with buffer
                    env=env
                )
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                log_callback('info', f'✅ FIO test completed in {elapsed_time:.2f} seconds')
                log_callback('info', f'Return code: {result.returncode}')
                
                # Log detailed output
                if result.stdout:
                    log_callback('info', f'FIO STDOUT length: {len(result.stdout)} characters')
                    if len(result.stdout) < 1000:
                        log_callback('stdout', f'FIO STDOUT:\n{result.stdout}')
                    else:
                        log_callback('stdout', f'FIO STDOUT (first 500 chars):\n{result.stdout[:500]}...')
                
                if result.stderr:
                    log_callback('stderr', f'FIO STDERR:\n{result.stderr}')
                
                if result.returncode == 0:
                    log_callback('info', '🎉 DIRECT FIO TEST: SUCCESS!')
                    
                    # Try to parse JSON output
                    fio_results = None
                    try:
                        fio_results = json.loads(result.stdout)
                        log_callback('info', '✅ Successfully parsed FIO JSON output')
                    except json.JSONDecodeError as e:
                        log_callback('warning', f'Failed to parse FIO JSON: {e}')
                    
                    return {
                        'success': True,
                        'message': 'Direct FIO test completed successfully',
                        'fio_path': fio_path,
                        'command': ' '.join(fio_cmd),
                        'elapsed_time': elapsed_time,
                        'raw_output': result.stdout,
                        'fio_results': fio_results,
                        'test_params': test_params,
                        'logs': logs
                    }
                else:
                    log_callback('error', f'❌ FIO test failed with return code {result.returncode}')
                    
                    # Check for specific errors
                    if 'failed to setup shm segment' in result.stderr:
                        log_callback('error', '💥 SHARED MEMORY ERROR DETECTED!')
                        log_callback('error', 'This confirms FIO is hitting macOS shared memory limits')
                        log_callback('error', 'Parameters used were meant to avoid this - investigating...')
                    
                    return {
                        'success': False,
                        'error': f'FIO test failed with return code {result.returncode}',
                        'fio_path': fio_path,
                        'command': ' '.join(fio_cmd),
                        'stderr': result.stderr,
                        'stdout': result.stdout,
                        'elapsed_time': elapsed_time,
                        'logs': logs
                    }
                    
            finally:
                # Clean up test file
                if os.path.exists(test_file):
                    try:
                        os.remove(test_file)
                        log_callback('info', '🧹 Test file cleaned up')
                    except Exception as e:
                        log_callback('warning', f'Failed to cleanup test file: {e}')
                    
        except subprocess.TimeoutExpired:
            timeout_msg = f'FIO test timed out after {duration + 60 if duration else 120} seconds'
            log_callback('error', f'⏰ {timeout_msg}')
            return {
                'success': False,
                'error': timeout_msg,
                'logs': logs
            }
        except Exception as e:
            log_callback('error', f'💥 Direct FIO test exception: {e}')
            return {
                'success': False,
                'error': str(e),
                'logs': logs
            }
    
    def run_qlab_test_direct(self, test_params):
        """
        Run QLab-specific performance tests using direct FIO.
        Implements the 3-minute and 2.75-hour test patterns.
        """
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        try:
            test_type = test_params.get('test_type', 'quick_max_speed')
            target_path = test_params.get('target_path', '/tmp')
            
            log_callback('info', f'🎬 Starting QLab test: {test_type}')
            log_callback('info', f'Target: {target_path}')
            
            # Define QLab test patterns with correct durations
            if test_type == 'quick_max_speed':
                log_callback('info', '⚡ Quick Max Speed Test (3 minutes)')
                fio_params = {
                    'size': '500M',
                    'rw': 'randrw',
                    'target_path': target_path,
                    'duration': 180  # 3 minutes = 180 seconds
                }
            elif test_type == 'qlab_prores_422_show':
                log_callback('info', '🎥 QLab ProRes 422 Show Pattern (2.75 hours)')
                fio_params = {
                    'size': '2G',
                    'rw': 'randrw',
                    'target_path': target_path,
                    'duration': 9900  # 2.75 hours = 9900 seconds
                }
            elif test_type == 'qlab_prores_hq_show':
                log_callback('info', '🎬 QLab ProRes HQ Show Pattern (2.75 hours)')
                fio_params = {
                    'size': '4G',
                    'rw': 'randrw',
                    'target_path': target_path,
                    'duration': 9900  # 2.75 hours = 9900 seconds
                }
            else:
                return {
                    'success': False,
                    'error': f'Unknown test type: {test_type}',
                    'logs': logs
                }
            
            # Run the direct FIO test
            result = self.run_direct_fio_test(fio_params)
            
            # Add QLab-specific analysis
            if result['success'] and result.get('fio_results'):
                log_callback('info', '📊 Analyzing QLab performance metrics...')
                # Add basic QLab performance analysis here
                
            return result
            
        except Exception as e:
            log_callback('error', f'💥 QLab test exception: {e}')
            return {
                'success': False,
                'error': str(e),
                'logs': logs
            }
    
    def detect_fio_shm_support(self):
        """
        Detect if standard FIO has shared memory issues on macOS.
        Tests if FIO fails with shared memory errors.
        """
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        try:
            log_callback('info', '🔍 Testing FIO shared memory support')
            
            # Find standard FIO binary
            fio_paths = [
                '/opt/homebrew/bin/fio',  # Apple Silicon Homebrew
                '/usr/local/bin/fio',     # Intel Homebrew
            ]
            
            fio_path = None
            for path in fio_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    fio_path = path
                    break
            
            if not fio_path:
                import shutil
                fio_path = shutil.which('fio')
            
            if not fio_path:
                log_callback('warning', 'No standard FIO found - will need to compile')
                return {
                    'success': True,
                    'has_shm_issues': True,
                    'reason': 'no_fio_found',
                    'needs_compilation': True,
                    'logs': logs
                }
            
            log_callback('info', f'Testing FIO at: {fio_path}')
            
            # Create minimal test file
            test_file = '/tmp/fio_shm_test'
            with open(test_file, 'wb') as f:
                f.write(b'0' * (1024 * 1024))  # 1MB
            
            try:
                # Run a test that would trigger shared memory usage
                # This test specifically uses features that require shm
                fio_cmd = [
                    fio_path,
                    '--name=shm_test',
                    f'--filename={test_file}',
                    '--size=1M',
                    '--bs=4k',
                    '--rw=read',
                    '--runtime=1',
                    '--time_based=1',
                    '--ioengine=libaio',  # This often triggers shm
                    '--direct=1',         # This often triggers shm  
                    '--numjobs=2',        # Multiple jobs increase shm usage
                    '--group_reporting=1',
                    '--output-format=json'
                ]
                
                log_callback('info', f'Running SHM test: {" ".join(fio_cmd)}')
                
                env = os.environ.copy()
                env['TMPDIR'] = '/tmp'
                
                result = subprocess.run(
                    fio_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env
                )
                
                log_callback('info', f'SHM test completed with return code: {result.returncode}')
                
                if result.stderr:
                    log_callback('info', f'FIO STDERR: {result.stderr}')
                
                # Check for shared memory errors
                shm_error_patterns = [
                    'failed to setup shm segment',
                    'shm_open',
                    'shared memory',
                    'Cannot allocate memory'
                ]
                
                has_shm_issues = False
                for pattern in shm_error_patterns:
                    if pattern in result.stderr:
                        has_shm_issues = True
                        log_callback('warning', f'Detected SHM issue: {pattern}')
                        break
                
                if result.returncode != 0 and has_shm_issues:
                    log_callback('warning', '❌ Standard FIO has shared memory issues')
                    return {
                        'success': True,
                        'has_shm_issues': True,
                        'reason': 'shm_error_detected',
                        'error_details': result.stderr,
                        'needs_compilation': True,
                        'fio_path': fio_path,
                        'logs': logs
                    }
                elif result.returncode == 0:
                    log_callback('info', '✅ Standard FIO works fine')
                    return {
                        'success': True,
                        'has_shm_issues': False,
                        'reason': 'fio_works_fine',
                        'needs_compilation': False,
                        'fio_path': fio_path,
                        'logs': logs
                    }
                else:
                    # FIO failed for other reasons - might still need no-shm version
                    log_callback('warning', f'FIO failed with return code {result.returncode}')
                    log_callback('warning', 'Assuming shared memory issues')
                    return {
                        'success': True,
                        'has_shm_issues': True,
                        'reason': 'fio_failed_unknown',
                        'error_details': result.stderr,
                        'needs_compilation': True,
                        'fio_path': fio_path,
                        'logs': logs
                    }
                    
            finally:
                if os.path.exists(test_file):
                    os.remove(test_file)
                    
        except Exception as e:
            log_callback('error', f'SHM detection failed: {e}')
            return {
                'success': False,
                'error': str(e),
                'logs': logs
            }
    
    def install_build_dependencies(self):
        """Install dependencies needed for FIO compilation."""
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        try:
            log_callback('info', '🔧 Installing build dependencies')
            
            # Check if Homebrew is available
            import shutil
            brew_path = shutil.which('brew')
            if not brew_path:
                log_callback('error', 'Homebrew not found - please install Homebrew first')
                return {
                    'success': False,
                    'error': 'Homebrew not found',
                    'logs': logs
                }
            
            log_callback('info', f'Found Homebrew at: {brew_path}')
            
            # Install required packages
            packages = ['automake', 'libtool', 'pkg-config']
            
            for package in packages:
                log_callback('info', f'Installing {package}...')
                
                result = subprocess.run([
                    brew_path, 'install', package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    log_callback('info', f'✅ {package} installed successfully')
                    if package == 'smartmontools':
                        log_callback('info', '🌡️ smartmontools installed - real SSD temperature monitoring enabled')
                elif 'already installed' in result.stderr or 'already installed' in result.stdout:
                    log_callback('info', f'✅ {package} already installed')
                    if package == 'smartmontools':
                        log_callback('info', '🌡️ smartmontools already available - real temperature monitoring ready')
                else:
                    log_callback('warning', f'⚠️ {package} installation had issues: {result.stderr}')
                    # Continue anyway - might already be installed
            
            # Check for Xcode Command Line Tools
            log_callback('info', 'Checking for Xcode Command Line Tools...')
            result = subprocess.run([
                'xcode-select', '--version'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_callback('info', '✅ Xcode Command Line Tools available')
            else:
                log_callback('warning', 'Xcode Command Line Tools not found')
                log_callback('info', 'Please install with: xcode-select --install')
                return {
                    'success': False,
                    'error': 'Xcode Command Line Tools required',
                    'logs': logs
                }
            
            return {
                'success': True,
                'message': 'Build dependencies installed',
                'logs': logs
            }
            
        except subprocess.TimeoutExpired:
            log_callback('error', 'Dependency installation timed out')
            return {
                'success': False,
                'error': 'Installation timed out',
                'logs': logs
            }
        except Exception as e:
            log_callback('error', f'Dependency installation failed: {e}')
            return {
                'success': False,
                'error': str(e),
                'logs': logs
            }
    
    
    def compile_fio_no_shm(self):
        """
        Download and compile FIO without shared memory support.
        This creates a macOS-compatible version that works in all contexts.
        """
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        try:
            log_callback('info', '🚀 Starting FIO compilation without shared memory')
            
            # Create temporary build directory
            import tempfile
            build_dir = tempfile.mkdtemp(prefix='fio_build_')
            log_callback('info', f'Build directory: {build_dir}')
            
            try:
                # Clone FIO repository
                log_callback('info', '📥 Downloading FIO source code...')
                
                clone_result = subprocess.run([
                    'git', 'clone', '--depth', '1',
                    'https://github.com/axboe/fio.git',
                    os.path.join(build_dir, 'fio')
                ], capture_output=True, text=True, timeout=300)
                
                if clone_result.returncode != 0:
                    log_callback('error', f'Git clone failed: {clone_result.stderr}')
                    return {
                        'success': False,
                        'error': f'Failed to download FIO source: {clone_result.stderr}',
                        'logs': logs
                    }
                
                log_callback('info', '✅ FIO source downloaded')
                
                fio_src_dir = os.path.join(build_dir, 'fio')
                
                # Configure FIO without shared memory
                log_callback('info', '⚙️ Configuring FIO without shared memory...')
                
                configure_result = subprocess.run([
                    './configure', '--disable-shm'
                ], cwd=fio_src_dir, capture_output=True, text=True, timeout=120)
                
                if configure_result.returncode != 0:
                    log_callback('error', f'Configure failed: {configure_result.stderr}')
                    return {
                        'success': False,
                        'error': f'FIO configure failed: {configure_result.stderr}',
                        'logs': logs
                    }
                
                log_callback('info', '✅ FIO configured without shared memory')
                
                # Compile FIO
                log_callback('info', '🔨 Compiling FIO (this may take a few minutes)...')
                
                make_result = subprocess.run([
                    'make', '-j4'  # Use 4 parallel jobs
                ], cwd=fio_src_dir, capture_output=True, text=True, timeout=600)
                
                if make_result.returncode != 0:
                    log_callback('error', f'Make failed: {make_result.stderr}')
                    return {
                        'success': False,
                        'error': f'FIO compilation failed: {make_result.stderr}',
                        'logs': logs
                    }
                
                log_callback('info', '✅ FIO compiled successfully')
                
                # Check if fio binary was created
                fio_binary = os.path.join(fio_src_dir, 'fio')
                if not os.path.exists(fio_binary):
                    log_callback('error', 'FIO binary not found after compilation')
                    return {
                        'success': False,
                        'error': 'FIO binary not created',
                        'logs': logs
                    }
                
                # Test the compiled binary
                log_callback('info', '🧪 Testing compiled FIO binary...')
                
                test_result = subprocess.run([
                    fio_binary, '--version'
                ], capture_output=True, text=True, timeout=10)
                
                if test_result.returncode != 0:
                    log_callback('error', f'Compiled FIO test failed: {test_result.stderr}')
                    return {
                        'success': False,
                        'error': 'Compiled FIO is not functional',
                        'logs': logs
                    }
                
                version_info = test_result.stdout.strip()
                log_callback('info', f'✅ Compiled FIO version: {version_info}')
                
                # Install to system location
                target_path = '/usr/local/bin/fio-nosmh'
                log_callback('info', f'📦 Installing FIO to {target_path}...')
                
                # Copy with sudo if needed
                try:
                    # Try without sudo first
                    import shutil
                    shutil.copy2(fio_binary, target_path)
                    log_callback('info', '✅ FIO installed without sudo')
                except PermissionError:
                    # Need sudo
                    install_result = subprocess.run([
                        'sudo', 'cp', fio_binary, target_path
                    ], capture_output=True, text=True, timeout=30)
                    
                    if install_result.returncode != 0:
                        log_callback('error', f'Installation failed: {install_result.stderr}')
                        return {
                            'success': False,
                            'error': f'Failed to install FIO: {install_result.stderr}',
                            'logs': logs
                        }
                    
                    log_callback('info', '✅ FIO installed with sudo')
                
                # Make executable
                chmod_result = subprocess.run([
                    'chmod', '+x', target_path
                ], capture_output=True, text=True, timeout=10)
                
                if chmod_result.returncode != 0:
                    log_callback('warning', f'chmod failed: {chmod_result.stderr}')
                
                # Final test of installed binary
                log_callback('info', f'🔍 Testing installed FIO at {target_path}...')
                
                final_test = subprocess.run([
                    target_path, '--version'
                ], capture_output=True, text=True, timeout=10)
                
                if final_test.returncode == 0:
                    log_callback('info', '🎉 FIO installation successful!')
                    return {
                        'success': True,
                        'message': 'FIO compiled and installed without shared memory',
                        'fio_path': target_path,
                        'version': final_test.stdout.strip(),
                        'build_dir': build_dir,
                        'logs': logs
                    }
                else:
                    log_callback('error', f'Installed FIO test failed: {final_test.stderr}')
                    return {
                        'success': False,
                        'error': 'Installed FIO is not functional',
                        'logs': logs
                    }
                    
            finally:
                # Cleanup build directory
                try:
                    import shutil
                    shutil.rmtree(build_dir)
                    log_callback('info', '🧹 Build directory cleaned up')
                except Exception as e:
                    log_callback('warning', f'Failed to cleanup build directory: {e}')
                    
        except subprocess.TimeoutExpired:
            log_callback('error', 'FIO compilation timed out')
            return {
                'success': False,
                'error': 'Compilation timed out',
                'logs': logs
            }
        except Exception as e:
            log_callback('error', f'FIO compilation failed: {e}')
            return {
                'success': False,
                'error': str(e),
                'logs': logs
            }
    
    def get_optimal_fio_path(self):
        """
        Get the optimal FIO path, preferring the no-shm version.
        Returns the best available FIO binary path.
        """
        # Priority order: no-shm version > standard homebrew > system
        fio_candidates = [
            '/usr/local/bin/fio-nosmh',   # Our compiled no-shm version (highest priority)
            '/opt/homebrew/bin/fio',      # Apple Silicon Homebrew
            '/usr/local/bin/fio',         # Intel Homebrew
        ]
        
        for fio_path in fio_candidates:
            if os.path.exists(fio_path) and os.access(fio_path, os.X_OK):
                self.logger.info(f"Selected FIO: {fio_path}")
                return fio_path
        
        # Try system PATH as last resort
        import shutil
        fio_path = shutil.which('fio')
        if fio_path:
            self.logger.info(f"Selected system FIO: {fio_path}")
            return fio_path
        
        self.logger.warning("No FIO binary found")
        return None
    
    def auto_fix_fio_shm(self):
        """
        Automatically detect and fix FIO shared memory issues.
        This is the main function that orchestrates the entire process.
        """
        logs = []
        
        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({
                'timestamp': timestamp,
                'level': level,
                'message': message
            })
            self.logger.info(f"[{level.upper()}] {message}")
        
        try:
            log_callback('info', '🚀 Starting automatic FIO shared memory fix')
            
            # Step 1: Check if we already have a no-shm version
            nosmh_path = '/usr/local/bin/fio-nosmh'
            if os.path.exists(nosmh_path) and os.access(nosmh_path, os.X_OK):
                log_callback('info', '✅ FIO no-shm version already installed')
                return {
                    'success': True,
                    'message': 'FIO no-shm version already available',
                    'fio_path': nosmh_path,
                    'action': 'already_installed',
                    'logs': logs
                }
            
            # Step 2: Detect if standard FIO has shared memory issues
            log_callback('info', '🔍 Step 1: Detecting FIO shared memory support...')
            shm_check = self.detect_fio_shm_support()
            
            if not shm_check.get('success', False):
                return {
                    'success': False,
                    'error': shm_check.get('error', 'SHM detection failed'),
                    'logs': logs + shm_check.get('logs', [])
                }
            
            if not shm_check.get('needs_compilation', False):
                log_callback('info', '✅ Standard FIO works fine - no compilation needed')
                return {
                    'success': True,
                    'message': 'Standard FIO works without shared memory issues',
                    'fio_path': shm_check.get('fio_path'),
                    'action': 'no_fix_needed',
                    'logs': logs + shm_check.get('logs', [])
                }
            
            log_callback('warning', '⚠️ Standard FIO has shared memory issues - compilation needed')
            
            # Step 3: Install build dependencies
            log_callback('info', '🔧 Step 2: Installing build dependencies...')
            deps_result = self.install_build_dependencies()
            
            if not deps_result.get('success', False):
                return {
                    'success': False,
                    'error': f"Failed to install dependencies: {deps_result.get('error')}",
                    'logs': logs + deps_result.get('logs', [])
                }
            
            log_callback('info', '✅ Build dependencies installed')
            
            # Step 4: Compile FIO without shared memory
            log_callback('info', '🚀 Step 3: Compiling FIO without shared memory...')
            compile_result = self.compile_fio_no_shm()
            
            if not compile_result.get('success', False):
                return {
                    'success': False,
                    'error': f"FIO compilation failed: {compile_result.get('error')}",
                    'logs': logs + compile_result.get('logs', [])
                }
            
            log_callback('info', '🎉 FIO compilation and installation completed successfully!')
            
            return {
                'success': True,
                'message': 'FIO successfully compiled and installed without shared memory',
                'fio_path': compile_result.get('fio_path'),
                'version': compile_result.get('version'),
                'action': 'compiled_and_installed',
                'logs': logs + compile_result.get('logs', [])
            }
            
        except Exception as e:
            log_callback('error', f'Auto-fix failed: {e}')
            return {
                'success': False,
                'error': str(e),
                'logs': logs
            }
    


class BridgeRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the bridge server."""
    
    def __init__(self, *args, bridge=None, **kwargs):
        self.bridge = bridge
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            if path == '/api/disks':
                self._handle_list_disks()
            elif path == '/api/validate':
                self._handle_validate()
            elif path == '/api/version':
                self._handle_version()
            elif path == '/api/status':
                self._handle_status()
            elif path == '/api/setup/validate':
                self._handle_setup_validate()
            elif path == '/api/test-fio':
                self._handle_test_fio()
            elif path == '/api/test-direct-fio':
                self._handle_direct_fio_test()
            elif path == '/api/fio/detect-shm':
                self._handle_detect_fio_shm()
            elif path == '/api/fio/auto-fix':
                self._handle_auto_fix_fio()
            elif path == '/api/background-tests':
                self._handle_background_tests_status()
            elif path == '/api/test/current':
                self._handle_current_test()
            elif path.startswith('/api/test/'):
                test_id = path.split('/')[-1]
                self._handle_test_status(test_id)
            elif path == '/':
                self._serve_web_gui()
            elif path.startswith('/web-gui/'):
                self._serve_static_file(path)
            elif path in ['/styles.css', '/app.js']:
                self._serve_static_file(path)
            else:
                self._send_error(404, 'Not Found')
                
        except Exception as e:
            self._send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path == '/api/test/start':
                self._handle_start_test()
            elif path.startswith('/api/test/stop/'):
                test_id = path.split('/')[-1]
                self._handle_stop_test(test_id)
            elif path == '/api/test/stop-all':
                self._handle_stop_all_tests()
            elif path == '/api/setup':
                self._handle_setup_action()
            elif path == '/api/validate':
                self._handle_validate_action()
            else:
                self._send_error(404, 'Not Found')
                
        except Exception as e:
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self._send_cors_headers()
        self.end_headers()
    
    def _send_cors_headers(self):
        """Send CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response with improved error handling."""
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            
            # Ensure data is JSON serializable
            try:
                json_data = json.dumps(data, indent=2, default=self._json_serializer)
                self.wfile.write(json_data.encode('utf-8'))
            except (TypeError, ValueError) as e:
                # Fallback for non-serializable data
                error_response = {
                    'success': False,
                    'error': f'JSON serialization error: {str(e)}',
                    'data_type': str(type(data))
                }
                json_data = json.dumps(error_response, indent=2)
                self.wfile.write(json_data.encode('utf-8'))
                
        except (BrokenPipeError, ConnectionResetError):
            # Client closed connection early - this is normal, don't log as error
            pass
        except Exception as e:
            # Last resort error handling
            try:
                error_response = {
                    'success': False,
                    'error': f'Response generation failed: {str(e)}'
                }
                json_data = json.dumps(error_response)
                self.wfile.write(json_data.encode('utf-8'))
            except:
                # If even this fails, send minimal response
                self.wfile.write(b'{"success": false, "error": "Critical response error"}')
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for non-standard objects."""
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        else:
            return str(obj)
    
    def _send_error(self, status_code, message):
        """Send error response."""
        self._send_json_response({
            'success': False,
            'error': message
        }, status_code)
    
    def _handle_list_disks(self):
        """Handle disk listing request."""
        result = self.bridge.list_disks()
        self._send_json_response(result)
    
    def _handle_validate(self):
        """Handle system validation request."""
        result = self.bridge.validate_system()
        self._send_json_response(result)
    
    def _handle_version(self):
        """Handle version request."""
        result = self.bridge.get_version()
        self._send_json_response(result)
    def _handle_status(self):
        """Handle system status request."""
        result = self.bridge.detect_system_status()
        self._send_json_response(result)
    
    def _handle_setup_validate(self):
        """Handle setup validation request."""
        result = self.bridge.validate_setup()
        self._send_json_response(result)
    
    def _handle_test_fio(self):
        """Handle FIO functionality test request."""
        result = self.bridge.test_fio_functionality()
        self._send_json_response(result)
    
    def _handle_direct_fio_test(self):
        """Handle direct FIO test request with macOS-safe parameters."""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Extract test parameters from query string
        test_params = {}
        if 'size' in query_params:
            test_params['size'] = query_params['size'][0]
        if 'rw' in query_params:
            test_params['rw'] = query_params['rw'][0]
        if 'target_path' in query_params:
            test_params['target_path'] = query_params['target_path'][0]
        if 'duration' in query_params:
            try:
                test_params['duration'] = int(query_params['duration'][0])
            except ValueError:
                pass
        
        result = self.bridge.run_direct_fio_test(test_params)
        self._send_json_response(result)
    
    def _handle_detect_fio_shm(self):
        """Handle FIO shared memory detection request."""
        result = self.bridge.detect_fio_shm_support()
        self._send_json_response(result)
    
    def _handle_auto_fix_fio(self):
        """Handle automatic FIO shared memory fix request."""
        result = self.bridge.auto_fix_fio_shm()
        self._send_json_response(result)
    
    def _handle_background_tests_status(self):
        """Handle background tests status request."""
        result = self.bridge.get_background_tests_status()
        self._send_json_response(result)
    
    def _handle_start_test(self):
        """Handle test start request."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            test_params = json.loads(post_data.decode('utf-8'))
            
            result = self.bridge.start_test(test_params)
            self._send_json_response(result)
            
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON data')
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_test_status(self, test_id):
        """Handle test status request."""
        result = self.bridge.get_test_status(test_id)
        self._send_json_response(result)

    def _handle_current_test(self):
        """Handle request for the current running test."""
        result = self.bridge.get_current_test()
        self._send_json_response(result)
    
    def _handle_stop_test(self, test_id):
        """Handle stop test request."""
        result = self.bridge.stop_test(test_id)
        self._send_json_response(result)
    
    def _handle_stop_all_tests(self):
        """Handle stop all tests request."""
        result = self.bridge.stop_all_tests()
        self._send_json_response(result)
    
    def _handle_setup_action(self):
        """Handle setup action POST request."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            action_data = json.loads(post_data.decode('utf-8'))
            
            action = action_data.get('action', '')
            
            if action == 'install_fio':
                result = self.bridge.install_fio()
            else:
                result = {
                    'success': False,
                    'error': f'Unknown setup action: {action}'
                }
            
            self._send_json_response(result)
            
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON data')
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_validate_action(self):
        """Handle validation action POST request."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            action_data = json.loads(post_data.decode('utf-8'))
            
            action = action_data.get('action', '')
            
            if action == 'run_all_tests':
                result = self.bridge.validate_setup()
            else:
                result = {
                    'success': False,
                    'error': f'Unknown validation action: {action}'
                }
            
            self._send_json_response(result)
            
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON data')
        except Exception as e:
            self._send_error(500, str(e))
    
    def _serve_web_gui(self):
        """Serve the main web GUI."""
        web_gui_path = os.path.join(os.path.dirname(__file__), '..', 'web-gui', 'index.html')
        self._serve_file(web_gui_path, 'text/html')
    
    def _serve_static_file(self, path):
        """Serve static files from web-gui directory."""
        # Handle both /web-gui/ prefixed and direct file requests
        if path.startswith('/web-gui/'):
            file_path = path[9:]  # Remove '/web-gui/'
        else:
            file_path = path[1:]  # Remove leading '/'
        
        full_path = os.path.join(os.path.dirname(__file__), '..', 'web-gui', file_path)
        
        # Determine content type
        if file_path.endswith('.css'):
            content_type = 'text/css'
        elif file_path.endswith('.js'):
            content_type = 'application/javascript'
        elif file_path.endswith('.html'):
            content_type = 'text/html'
        else:
            content_type = 'application/octet-stream'
        
        self._serve_file(full_path, content_type)
    
    def _serve_file(self, file_path, content_type):
        """Serve a file with the given content type."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            else:
                self._send_error(404, 'File not found')
        except Exception as e:
            self._send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logging.info(f"{self.address_string()} - {format % args}")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for handling multiple requests."""
    allow_reuse_address = True


def create_request_handler(bridge):
    """Create a request handler with the bridge instance."""
    def handler(*args, **kwargs):
        return BridgeRequestHandler(*args, bridge=bridge, **kwargs)
    return handler


def main():
    """Main server function."""
    print("🚀 QLab Disk Performance Tester Bridge Server starting...")
    
    # Setup logging to stderr only (not stdout) to avoid contaminating JSON responses
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # Force logging to stderr, not stdout
    )
    
    logger = logging.getLogger(__name__)
    
    # Create bridge instance
    bridge = DiskBenchBridge()
    
    # Create server
    server_address = ('localhost', 8765)
    handler_class = create_request_handler(bridge)
    
    try:
        httpd = ThreadedHTTPServer(server_address, handler_class)
        
        logger.info(f"Starting QLab Disk Performance Tester Bridge Server")
        logger.info(f"Server running at http://{server_address[0]}:{server_address[1]}")
        logger.info(f"Web GUI available at http://{server_address[0]}:{server_address[1]}/")
        logger.info(f"Press Ctrl+C to stop the server")
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if 'httpd' in locals():
            httpd.shutdown()
            httpd.server_close()


if __name__ == '__main__':
    main()
