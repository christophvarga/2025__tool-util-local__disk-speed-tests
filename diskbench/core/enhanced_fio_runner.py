"""
Enhanced FIO runner with integrated monitoring and health checks.

This extends the existing FioRunner with comprehensive monitoring,
health checks, and performance tracking capabilities.
"""
import json
import logging
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

from .fio_runner import FioRunner
from .monitoring import PerformanceMonitor
from .health_checks import SystemHealthChecker, HealthStatus, HealthCheckResult


class EnhancedFioRunner(FioRunner):
    """Enhanced FIO runner with monitoring and health check capabilities."""
    
    def __init__(self, enable_monitoring: bool = True, enable_health_checks: bool = True):
        """
        Initialize enhanced FIO runner.
        
        Args:
            enable_monitoring: Enable performance monitoring and metrics collection
            enable_health_checks: Enable system health checks before tests
        """
        # Ensure logger exists even if base __init__ is patched in tests
        self.logger = logging.getLogger(__name__)
        
        # Initialize base FioRunner
        super().__init__()
        
        # Initialize monitoring components
        self.monitoring_enabled = enable_monitoring
        self.health_checks_enabled = enable_health_checks
        
        if enable_monitoring:
            self.monitor = PerformanceMonitor()
            self.logger.info("Performance monitoring enabled")
        else:
            self.monitor = None
            
        if enable_health_checks:
            self.health_checker = SystemHealthChecker(self.monitor)
            self.logger.info("Health checks enabled")
        else:
            self.health_checker = None
    
    def run_fio_test_enhanced(self, config_content: str, test_directory: str,
                            estimated_duration: int, progress_callback=None,
                            test_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Enhanced FIO test execution with monitoring and health checks.
        
        Args:
            config_content: FIO configuration content
            test_directory: Directory for test files
            estimated_duration: Estimated test duration in seconds
            progress_callback: Optional callback for progress updates
            test_name: Optional test name for better tracking
        
        Returns:
            Enhanced test results with monitoring data or None on error
        """
        # Generate test ID
        test_id = str(uuid.uuid4())[:8]
        if test_name:
            operation_name = f"{test_name}_{test_id}"
        else:
            operation_name = f"fio_test_{test_id}"
        
        self.logger.info(f"Starting enhanced FIO test: {operation_name}")
        
        # Pre-test health checks
        if self.health_checks_enabled:
            health_results = self._perform_pre_test_health_checks(test_id)
            if any(r.status == HealthStatus.CRITICAL for r in health_results):
                critical_issues = [r.message for r in health_results if r.status == HealthStatus.CRITICAL]
                self.logger.error(f"Critical health issues detected: {critical_issues}")
                return {
                    'error': 'Pre-test health checks failed',
                    'critical_issues': critical_issues,
                    'health_results': [r.__dict__ for r in health_results]
                }
        
        # Extract test parameters for monitoring tags
        tags = self._extract_test_tags(config_content, test_directory)
        tags['test_id'] = test_id
        
        try:
            # Run test with monitoring
            if self.monitoring_enabled:
                with self.monitor.measure_operation(operation_name, tags=tags):
                    result = super().run_fio_test(config_content, test_directory, 
                                                 estimated_duration, progress_callback)
            else:
                result = super().run_fio_test(config_content, test_directory,
                                            estimated_duration, progress_callback)
            
            # Enhance results with monitoring data
            if result and self.monitoring_enabled:
                result = self._enhance_results_with_monitoring(result, test_id, operation_name)
            
            # Log test completion metrics
            if self.monitoring_enabled:
                if result and 'error' not in result:
                    self.monitor.log_metric('fio_test_success', 1,
                                          tags=tags, unit='count')
                    self._log_test_performance_metrics(result, tags)
                else:
                    self.monitor.log_metric('fio_test_failure', 1,
                                          tags=tags, unit='count')
            
            self.logger.info(f"Enhanced FIO test completed: {operation_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Enhanced FIO test failed: {e}")
            
            # Log failure metrics
            if self.monitoring_enabled:
                self.monitor.log_metric('fio_test_exception', 1,
                                      tags={**tags, 'exception_type': type(e).__name__},
                                      unit='count')
            
            return {
                'error': f'Test execution failed: {e}',
                'exception_type': type(e).__name__,
                'test_id': test_id
            }
    
    def _perform_pre_test_health_checks(self, test_id: str) -> List[HealthCheckResult]:
        """Perform comprehensive health checks before test execution."""
        if not self.health_checker:
            return []
        
        self.logger.info(f"Running pre-test health checks for test {test_id}")
        
        # Run critical health checks
        critical_checks = [
            self.health_checker.check_fio_dependency,
            self.health_checker.check_disk_space,
            self.health_checker.check_memory_usage,
            self.health_checker.check_cpu_usage
        ]
        
        results = []
        for check_func in critical_checks:
            try:
                result = check_func()
                results.append(result)
                
                if result.status == HealthStatus.CRITICAL:
                    self.logger.warning(f"Critical health issue: {result.message}")
                elif result.status == HealthStatus.WARNING:
                    self.logger.info(f"Health warning: {result.message}")
                else:
                    self.logger.debug(f"Health check passed: {result.name}")
                    
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                results.append(HealthCheckResult(
                    name=check_func.__name__.replace('check_', ''),
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {e}",
                    details={'exception': str(e)},
                    timestamp=time.time(),
                    duration_ms=0
                ))
        
        # Log health check summary
        if self.monitoring_enabled:
            healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
            warning_count = sum(1 for r in results if r.status == HealthStatus.WARNING)
            critical_count = sum(1 for r in results if r.status == HealthStatus.CRITICAL)
            
            self.monitor.log_metric('pre_test_health_checks_healthy', healthy_count, unit='count')
            self.monitor.log_metric('pre_test_health_checks_warnings', warning_count, unit='count')
            self.monitor.log_metric('pre_test_health_checks_critical', critical_count, unit='count')
        
        return results
    
    def _extract_test_tags(self, config_content: str, test_directory: str) -> Dict[str, str]:
        """Extract test parameters for monitoring tags."""
        tags = {
            'test_directory': str(Path(test_directory).name),
            'config_size_bytes': str(len(config_content))
        }
        
        # Try to extract key parameters from config
        try:
            lines = config_content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('rw='):
                    tags['rw_pattern'] = line.split('=')[1]
                elif line.startswith('bs='):
                    tags['block_size'] = line.split('=')[1]
                elif line.startswith('size='):
                    tags['test_size'] = line.split('=')[1]
                elif line.startswith('runtime='):
                    tags['runtime'] = line.split('=')[1]
                elif line.startswith('numjobs='):
                    tags['num_jobs'] = line.split('=')[1]
                elif line.startswith('iodepth='):
                    tags['io_depth'] = line.split('=')[1]
        except Exception as e:
            self.logger.debug(f"Could not extract all config tags: {e}")
        
        return tags
    
    def _enhance_results_with_monitoring(self, result: Dict[str, Any], 
                                       test_id: str, operation_name: str) -> Dict[str, Any]:
        """Enhance test results with monitoring data."""
        if not self.monitor:
            return result
        
        # Get system metrics
        current_metrics = self.monitor.get_system_metrics()
        
        # Add monitoring metadata
        result['monitoring'] = {
            'test_id': test_id,
            'operation_name': operation_name,
            'system_metrics': current_metrics,
            'metrics_collected': list(self.monitor.metrics.keys()),
            'monitoring_enabled': True
        }
        
        # Add performance summaries if available
        for metric_name in self.monitor.metrics.keys():
            if test_id in metric_name or operation_name in metric_name:
                summary = self.monitor.get_metric_summary(metric_name)
                if 'error' not in summary:
                    result['monitoring'][f'{metric_name}_summary'] = summary
        
        return result
    
    def _log_test_performance_metrics(self, result: Dict[str, Any], tags: Dict[str, str]):
        """Log detailed performance metrics from test results."""
        if not self.monitor or 'jobs' not in result:
            return
        
        try:
            # Log metrics for each job
            for i, job in enumerate(result.get('jobs', [])):
                job_tags = {**tags, 'job_index': str(i), 'jobname': job.get('jobname', f'job_{i}')}
                
                # Read performance metrics
                if 'read' in job:
                    read_stats = job['read']
                    self.monitor.log_metric('fio_read_bandwidth_kbs', read_stats.get('bw', 0),
                                          tags={**job_tags, 'io_type': 'read'}, unit='kbs')
                    self.monitor.log_metric('fio_read_iops', read_stats.get('iops', 0),
                                          tags={**job_tags, 'io_type': 'read'}, unit='iops')
                    self.monitor.log_metric('fio_read_latency_ns', read_stats.get('lat_ns', {}).get('mean', 0),
                                          tags={**job_tags, 'io_type': 'read'}, unit='nanoseconds')
                
                # Write performance metrics
                if 'write' in job:
                    write_stats = job['write']
                    self.monitor.log_metric('fio_write_bandwidth_kbs', write_stats.get('bw', 0),
                                          tags={**job_tags, 'io_type': 'write'}, unit='kbs')
                    self.monitor.log_metric('fio_write_iops', write_stats.get('iops', 0),
                                          tags={**job_tags, 'io_type': 'write'}, unit='iops')
                    self.monitor.log_metric('fio_write_latency_ns', write_stats.get('lat_ns', {}).get('mean', 0),
                                          tags={**job_tags, 'io_type': 'write'}, unit='nanoseconds')
                
                # System utilization metrics
                self.monitor.log_metric('fio_cpu_user_percent', job.get('usr_cpu', 0),
                                      tags=job_tags, unit='percent')
                self.monitor.log_metric('fio_cpu_system_percent', job.get('sys_cpu', 0),
                                      tags=job_tags, unit='percent')
                self.monitor.log_metric('fio_runtime_seconds', job.get('job_runtime', 0) / 1000.0,
                                      tags=job_tags, unit='seconds')
            
            # Overall test metrics
            if 'summary' in result:
                summary = result['summary']
                self.monitor.log_metric('fio_total_read_bandwidth_kbs', 
                                      summary.get('total_read_bw', 0),
                                      tags=tags, unit='kbs')
                self.monitor.log_metric('fio_total_write_bandwidth_kbs',
                                      summary.get('total_write_bw', 0),
                                      tags=tags, unit='kbs')
                self.monitor.log_metric('fio_total_read_iops',
                                      summary.get('total_read_iops', 0),
                                      tags=tags, unit='iops')
                self.monitor.log_metric('fio_total_write_iops',
                                      summary.get('total_write_iops', 0),
                                      tags=tags, unit='iops')
                
        except Exception as e:
            self.logger.error(f"Failed to log performance metrics: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status."""
        status = {
            'monitoring_enabled': self.monitoring_enabled,
            'health_checks_enabled': self.health_checks_enabled,
            'fio_available': self.fio_path is not None
        }
        
        if self.monitoring_enabled and self.monitor:
            status['metrics_collected'] = len(self.monitor.metrics)
            status['log_directory'] = str(self.monitor.log_dir)
            
        if self.health_checks_enabled and self.health_checker:
            # Run quick health summary
            try:
                health_results = self.health_checker.run_all_checks()
                health_summary = self.health_checker.get_health_summary(health_results)
                status['health_summary'] = {
                    'overall_status': health_summary['overall_status'],
                    'healthy': health_summary['healthy'],
                    'warnings': health_summary['warnings'],
                    'critical': health_summary['critical'],
                    'last_check': health_summary['timestamp']
                }
            except Exception as e:
                status['health_check_error'] = str(e)
        
        return status
    
    def export_monitoring_data(self, output_file: Optional[str] = None) -> Optional[str]:
        """Export collected monitoring data to file."""
        if not self.monitoring_enabled or not self.monitor:
            self.logger.warning("Monitoring not enabled, cannot export data")
            return None
        
        try:
            export_path = self.monitor.export_metrics(output_file)
            self.logger.info(f"Monitoring data exported to: {export_path}")
            return export_path
        except Exception as e:
            self.logger.error(f"Failed to export monitoring data: {e}")
            return None
    
    def clear_monitoring_data(self):
        """Clear collected monitoring data."""
        if self.monitoring_enabled and self.monitor:
            self.monitor.clear_metrics()
            self.logger.info("Monitoring data cleared")
        else:
            self.logger.warning("Monitoring not enabled, no data to clear")
