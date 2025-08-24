"""
FIO runner for diskbench helper binary - Pure Homebrew FIO only.
"""

import logging
import subprocess
import os
import json
import tempfile
import shutil
import signal
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.security import validate_fio_parameters, get_safe_test_directory, check_available_space

logger = logging.getLogger(__name__)

class FioRunner:
    """Manages FIO execution and result processing - Homebrew FIO only."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fio_path = self._find_fio_binary()
        self.fio_process = None # Initialize fio_process to None
    
    def _find_fio_binary(self) -> Optional[str]:
        """Find optimal FIO binary - prioritizing no-SHM version for macOS compatibility."""
        
        # Priority order: no-SHM version first to avoid shared memory issues
        fio_candidates = [
            '/usr/local/bin/fio-noshm',   # Compiled no-SHM version (HIGHEST priority)
            '/usr/local/bin/fio-noshm',   # Alternative no-SHM name
            '/opt/homebrew/bin/fio',      # Apple Silicon Homebrew (standard)
            '/usr/local/bin/fio',         # Intel Homebrew (standard)
        ]
        
        for fio_path in fio_candidates:
            if os.path.exists(fio_path) and os.access(fio_path, os.X_OK):
                if 'nosmh' in fio_path or 'noshm' in fio_path:
                    self.logger.info(f"✅ Found macOS-compatible no-SHM FIO at: {fio_path}")
                else:
                    self.logger.info(f"⚠️ Found standard FIO at: {fio_path} (may have SHM issues)")
                return fio_path
        
        # System PATH FIO (backup for other installations)
        try:
            result = subprocess.run(['which', 'fio'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                fio_path = result.stdout.strip()
                # Only accept if it's not already checked above
                if fio_path not in fio_candidates:
                    self.logger.info(f"Found system FIO at: {fio_path}")
                    return fio_path
        except Exception:
            pass
        
        self.logger.error("❌ FIO not found. Options:")
        self.logger.error("  1. Install standard FIO: brew install fio")
        self.logger.error("  2. Use bridge server to compile no-SHM version for better macOS compatibility")
        return None
    
    def get_fio_status(self) -> Dict[str, Any]:
        """Get FIO availability status."""
        if not self.fio_path:
            return {
                'available': False,
                'error': 'FIO binary not found',
                'path': None,
                'version': None
            }
        
        try:
            result = subprocess.run([self.fio_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                return {
                    'available': True,
                    'error': None,
                    'path': self.fio_path,
                    'version': version
                }
        except Exception as e:
            return {
                'available': False,
                'error': f'Failed to get FIO version: {e}',
                'path': self.fio_path,
                'version': None
            }
        
        return {
            'available': False,
            'error': 'FIO execution failed',
            'path': self.fio_path,
            'version': None
        }
    
    
    def run_fio_test(self, config_content: str, test_directory: str, 
                     estimated_duration: int, progress_callback=None) -> Optional[Dict[str, Any]]:
        """
        Run FIO test with given configuration.
        
        Args:
            config_content: FIO configuration content
            test_directory: Directory for test files
            progress_callback: Optional callback for progress updates
        
        Returns:
            Test results or None on error
        """
        if not self.fio_path:
            self.logger.error("FIO binary not available")
            return None
        
        try:
            # Create test directory
            os.makedirs(test_directory, exist_ok=True)
            
            # Write config file
            config_file = os.path.join(test_directory, 'fio_config.ini')
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            # Prepare FIO command
            output_file = os.path.join(test_directory, 'fio_output.json')
            cmd = [
                self.fio_path,
                '--output-format=json',
                f'--output={output_file}',
                config_file
            ]
            
            # Validate command parameters
            safe_cmd = validate_fio_parameters(cmd)
            if len(safe_cmd) != len(cmd):
                self.logger.warning("Some FIO parameters were filtered for security")
            
            self.logger.info(f"Running FIO command: {' '.join(safe_cmd)}")
            
            # Run FIO with clean environment - no sandbox workarounds
            env = os.environ.copy()
            
            self.fio_process = subprocess.Popen(
                safe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=test_directory,
                start_new_session=True # Start in a new process group
            )
            
            stdout, stderr = self.fio_process.communicate()
            
            if self.fio_process.returncode != 0:
                error_msg = f"FIO failed with return code {self.fio_process.returncode}"
                if stderr:
                    error_msg += f". Error: {stderr}"
                
                self.logger.error(f"FIO failed: {stderr}")
                return {
                    'error': error_msg,
                    'fio_stdout': stdout,
                    'fio_stderr': stderr,
                    'return_code': self.fio_process.returncode
                }
            
            # Parse results with robust error handling
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        content = f.read()
                        self.logger.info(f"Raw FIO output length: {len(content)} chars")
                        
                        # Log first few lines for debugging
                        lines = content.split('\n')[:5]
                        self.logger.info(f"First 5 lines: {lines}")
                        
                        # Parse JSON and log structure for debugging
                        fio_results = json.loads(content)
                        
                        # DEBUG: Log the actual FIO JSON structure
                        if 'jobs' in fio_results and len(fio_results['jobs']) > 0:
                            first_job = fio_results['jobs'][0]
                            self.logger.info(f"DEBUG: First job keys: {list(first_job.keys())}")
                            if 'read' in first_job:
                                self.logger.info(f"DEBUG: Read stats keys: {list(first_job['read'].keys())}")
                                self.logger.info(f"DEBUG: Read stats sample: {dict(list(first_job['read'].items())[:10])}")
                            if 'write' in first_job:
                                self.logger.info(f"DEBUG: Write stats keys: {list(first_job['write'].keys())}")
                    
                    # Process and enhance results
                    processed_results = self._process_fio_results(fio_results)
                    return processed_results
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON parse error at line {e.lineno}, column {e.colno}")
                    self.logger.error(f"Error message: {e.msg}")
                    
                    # Try to clean and retry
                    try:
                        cleaned_content = self._clean_json_output(content)
                        self.logger.info("Attempting to parse cleaned JSON content")
                        fio_results = json.loads(cleaned_content)
                        processed_results = self._process_fio_results(fio_results)
                        return processed_results
                    except Exception as clean_error:
                        self.logger.error(f"Cleaned JSON parsing also failed: {clean_error}")
                        
                        # Return error with diagnostic info
                        return {
                            'error': f'JSON parsing failed: {e.msg}',
                            'json_error_line': e.lineno,
                            'json_error_column': e.colno,
                            'fio_stdout': stdout,
                            'fio_stderr': stderr,
                            'raw_output_preview': content[:1000] if content else 'No content'
                        }
                        
                except Exception as e:
                    error_msg = f"Error reading FIO output file: {e}"
                    self.logger.error(error_msg)
                    return {
                        'error': error_msg,
                        'fio_stdout': stdout,
                        'fio_stderr': stderr
                    }
            else:
                error_msg = "FIO output file not found"
                self.logger.error(error_msg)
                return {
                    'error': error_msg,
                    'fio_stdout': stdout,
                    'fio_stderr': stderr
                }
                
        except Exception as e:
            error_msg = f"Error running FIO test: {e}"
            self.logger.error(error_msg)
            return {
                'error': error_msg,
                'exception': str(e)
            }
        finally:
            # Cleanup
            try:
                if os.path.exists(test_directory):
                    shutil.rmtree(test_directory)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup test directory: {e}")
            self.fio_process = None # Clear the process reference
    
    def stop_fio_test(self):
        """Terminates the running FIO process."""
        if self.fio_process and self.fio_process.poll() is None:
            self.logger.info(f"Attempting to stop FIO process (PID: {self.fio_process.pid})")
            try:
                # Send SIGTERM to the process group
                os.killpg(self.fio_process.pid, signal.SIGTERM)
                self.fio_process.wait(timeout=5) # Wait for graceful exit
                self.logger.info(f"FIO process {self.fio_process.pid} terminated gracefully.")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"FIO process {self.fio_process.pid} did not terminate gracefully, force killing.")
                # Send SIGKILL to the process group
                os.killpg(self.fio_process.pid, signal.SIGKILL)
                self.fio_process.wait()
                self.logger.info(f"FIO process {self.fio_process.pid} force killed.")
            except ProcessLookupError:
                self.logger.warning(f"FIO process {self.fio_process.pid} already gone.")
            except Exception as e:
                self.logger.error(f"Error stopping FIO process {self.fio_process.pid}: {e}")
            finally:
                self.fio_process = None # Clear the process reference
                return True
        self.logger.info("No FIO process to stop.")
        return False

    
    def _process_fio_results(self, fio_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw FIO results into structured format."""
        try:
            processed = {
                'fio_version': fio_results.get('fio version', 'unknown'),
                'timestamp': fio_results.get('timestamp', 0),
                'jobs': [],
                'summary': {},
                'engine': 'homebrew_fio'
            }
            
            # Process each job
            for job in fio_results.get('jobs', []):
                job_result = {
                    'jobname': job.get('jobname', 'unknown'),
                    'read': self._extract_io_stats(job.get('read', {})),
                    'write': self._extract_io_stats(job.get('write', {})),
                    'trim': self._extract_io_stats(job.get('trim', {})),
                    'sync': job.get('sync', {}),
                    'job_runtime': job.get('job_runtime', 0),
                    'usr_cpu': job.get('usr_cpu', 0),
                    'sys_cpu': job.get('sys_cpu', 0),
                    'ctx': job.get('ctx', 0),
                    'majf': job.get('majf', 0),
                    'minf': job.get('minf', 0)
                }
                processed['jobs'].append(job_result)
            
            # Calculate summary statistics
            processed['summary'] = self._calculate_summary(processed['jobs'])
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error processing FIO results: {e}")
            return {'error': str(e)}
    
    def _extract_io_stats(self, io_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract I/O statistics from FIO job data with backward-compatibility for newer FIO JSON fields."""
        # FIO 3.35+ has switched from KiB/s ``bw`` to bytes/s ``bw_bytes``
        bw_bytes = io_data.get('bw_bytes', 0)
        bw_kib = io_data.get('bw', 0)
        if (not bw_kib or bw_kib == 0) and bw_bytes:
            # Convert bytes/s -> KiB/s to keep existing logic untouched
            bw_kib = bw_bytes / 1024

        return {
            'io_bytes': io_data.get('io_bytes', 0),
            'io_kbytes': io_data.get('io_kbytes', 0),
            'bw_bytes': bw_bytes,
            'bw': bw_kib,
            'iops': io_data.get('iops', io_data.get('iops_mean', 0)),
            'runtime': io_data.get('runtime', 0),
            'total_ios': io_data.get('total_ios', 0),
            'short_ios': io_data.get('short_ios', 0),
            'drop_ios': io_data.get('drop_ios', 0),
            'slat_ns': io_data.get('slat_ns', {}),
            'clat_ns': io_data.get('clat_ns', {}),
            'lat_ns': io_data.get('lat_ns', {}),
            'bw_min': io_data.get('bw_min', 0),
            'bw_max': io_data.get('bw_max', 0),
            'bw_agg': io_data.get('bw_agg', 0),
            'bw_mean': io_data.get('bw_mean', bw_kib),
            'bw_dev': io_data.get('bw_dev', 0)
        }
    
    def _calculate_summary(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics across all jobs, handling both old and new FIO field names."""
        if not jobs:
            return {}

        summary = {
            'total_read_iops': 0,
            'total_write_iops': 0,
            'total_read_bw': 0,
            'total_write_bw': 0,
            'avg_read_latency': 0,
            'avg_write_latency': 0,
            'total_runtime': 0
        }

        read_latencies: List[float] = []
        write_latencies: List[float] = []

        for job in jobs:
            # ---- IOPS ----
            summary['total_read_iops'] += job['read'].get('iops', 0)
            summary['total_write_iops'] += job['write'].get('iops', 0)

            # ---- Bandwidth (KiB/s) ----
            def _bw(io: Dict[str, Any]):
                bw = io.get('bw', 0)
                if not bw or bw == 0:
                    bw = io.get('bw_bytes', 0) / 1024  # bytes/s → KiB/s
                return bw

            summary['total_read_bw'] += _bw(job['read'])
            summary['total_write_bw'] += _bw(job['write'])

            # ---- Runtime ----
            summary['total_runtime'] = max(summary['total_runtime'], job.get('job_runtime', 0))

            # ---- Latency (ns) ----
            read_lat = job['read'].get('lat_ns', {}).get('mean', 0)
            write_lat = job['write'].get('lat_ns', {}).get('mean', 0)

            if read_lat > 0:
                read_latencies.append(read_lat)
            if write_lat > 0:
                write_latencies.append(write_lat)

        # Average latencies -> ms
        if read_latencies:
            summary['avg_read_latency'] = sum(read_latencies) / len(read_latencies) / 1_000_000
        if write_latencies:
            summary['avg_write_latency'] = sum(write_latencies) / len(write_latencies) / 1_000_000

        return summary
    
    def _clean_json_output(self, content: str) -> str:
        """Clean FIO JSON output of common contamination issues."""
        try:
            lines = content.split('\n')
            json_lines = []
            in_json = False
            brace_count = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines and obvious non-JSON content
                if not stripped:
                    continue
                    
                # Skip FIO status/error messages that might contaminate JSON
                if any(skip_pattern in stripped.lower() for skip_pattern in [
                    'fio-', 'starting', 'jobs:', 'run status', 'error:', 'warning:'
                ]):
                    continue
                
                # Start collecting when we see opening brace
                if stripped.startswith('{') and not in_json:
                    in_json = True
                    brace_count = 0
                
                if in_json:
                    json_lines.append(line)
                    
                    # Count braces to detect end of JSON
                    brace_count += stripped.count('{') - stripped.count('}')
                    
                    # Stop when we've closed all braces
                    if brace_count == 0 and stripped.endswith('}'):
                        break
            
            cleaned_content = '\n'.join(json_lines)
            self.logger.debug(f"Cleaned JSON content length: {len(cleaned_content)} chars")
            
            return cleaned_content
            
        except Exception as e:
            self.logger.error(f"Error cleaning JSON output: {e}")
            return content  # Return original if cleaning fails
