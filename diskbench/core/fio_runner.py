"""
FIO runner for diskbench helper binary.
"""

import logging
import subprocess
import os
import json
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.security import validate_fio_parameters, get_safe_test_directory, check_available_space

logger = logging.getLogger(__name__)

class FioRunner:
    """Manages FIO execution and result processing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fio_path = self._find_fio_binary()
    
    def _find_fio_binary(self) -> Optional[str]:
        """Find FIO binary (bundled or system)."""
        # Check for bundled FIO first
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundled_paths = [
            os.path.join(script_dir, '..', 'fio-3.37', 'fio'),
            os.path.join(script_dir, '..', 'resources', 'fio-3.37', 'fio'),
            '/usr/local/share/qlab-disk-tester/fio-3.37/fio'
        ]
        
        for path in bundled_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                self.logger.info(f"Found bundled FIO at: {path}")
                return path
        
        # Check system FIO
        try:
            result = subprocess.run(['which', 'fio'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                fio_path = result.stdout.strip()
                self.logger.info(f"Found system FIO at: {fio_path}")
                return fio_path
        except Exception:
            pass
        
        self.logger.error("FIO binary not found")
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
                     progress_callback=None) -> Optional[Dict[str, Any]]:
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
            
            # Run FIO
            process = subprocess.Popen(
                safe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=test_directory
            )
            
            # Monitor progress if callback provided
            if progress_callback:
                self._monitor_progress(process, progress_callback)
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"FIO failed with return code {process.returncode}")
                self.logger.error(f"STDERR: {stderr}")
                return None
            
            # Parse results
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    fio_results = json.load(f)
                
                # Process and enhance results
                processed_results = self._process_fio_results(fio_results)
                return processed_results
            else:
                self.logger.error("FIO output file not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error running FIO test: {e}")
            return None
        finally:
            # Cleanup
            try:
                if os.path.exists(test_directory):
                    shutil.rmtree(test_directory)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup test directory: {e}")
    
    def _monitor_progress(self, process, progress_callback):
        """Monitor FIO progress and call callback."""
        try:
            # Simple progress monitoring - could be enhanced
            # FIO doesn't provide easy progress info, so this is basic
            import time
            start_time = time.time()
            
            while process.poll() is None:
                elapsed = time.time() - start_time
                # Estimate progress based on time (very rough)
                estimated_duration = 60  # Assume 60 seconds for basic test
                progress = min(elapsed / estimated_duration * 100, 95)
                
                progress_callback({
                    'progress': progress,
                    'elapsed_time': elapsed,
                    'status': 'running'
                })
                
                time.sleep(1)
            
            # Final progress update
            progress_callback({
                'progress': 100,
                'elapsed_time': time.time() - start_time,
                'status': 'completed'
            })
            
        except Exception as e:
            self.logger.warning(f"Progress monitoring failed: {e}")
    
    def _process_fio_results(self, fio_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw FIO results into structured format."""
        try:
            processed = {
                'fio_version': fio_results.get('fio version', 'unknown'),
                'timestamp': fio_results.get('timestamp', 0),
                'jobs': [],
                'summary': {}
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
        """Extract I/O statistics from FIO job data."""
        return {
            'io_bytes': io_data.get('io_bytes', 0),
            'io_kbytes': io_data.get('io_kbytes', 0),
            'bw_bytes': io_data.get('bw_bytes', 0),
            'bw': io_data.get('bw', 0),
            'iops': io_data.get('iops', 0),
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
            'bw_mean': io_data.get('bw_mean', 0),
            'bw_dev': io_data.get('bw_dev', 0)
        }
    
    def _calculate_summary(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics across all jobs."""
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
        
        read_latencies = []
        write_latencies = []
        
        for job in jobs:
            summary['total_read_iops'] += job['read'].get('iops', 0)
            summary['total_write_iops'] += job['write'].get('iops', 0)
            summary['total_read_bw'] += job['read'].get('bw', 0)
            summary['total_write_bw'] += job['write'].get('bw', 0)
            summary['total_runtime'] = max(summary['total_runtime'], job.get('job_runtime', 0))
            
            # Collect latencies for averaging
            read_lat = job['read'].get('lat_ns', {}).get('mean', 0)
            write_lat = job['write'].get('lat_ns', {}).get('mean', 0)
            
            if read_lat > 0:
                read_latencies.append(read_lat)
            if write_lat > 0:
                write_latencies.append(write_lat)
        
        # Calculate average latencies
        if read_latencies:
            summary['avg_read_latency'] = sum(read_latencies) / len(read_latencies) / 1000000  # Convert to ms
        if write_latencies:
            summary['avg_write_latency'] = sum(write_latencies) / len(write_latencies) / 1000000  # Convert to ms
        
        return summary
