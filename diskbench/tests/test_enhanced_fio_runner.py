"""
Unit tests for EnhancedFioRunner with monitoring integration.
"""
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from diskbench.core.enhanced_fio_runner import EnhancedFioRunner
from diskbench.core.health_checks import HealthStatus, HealthCheckResult


class TestEnhancedFioRunner:
    """Test enhanced FIO runner with monitoring capabilities."""
    
    @pytest.fixture
    def mock_fio_result(self):
        """Mock FIO test result."""
        return {
            'fio_version': 'fio-3.16',
            'timestamp': 1640995200,
            'jobs': [{
                'jobname': 'test_job',
                'read': {
                    'bw': 1024.0,
                    'iops': 256.0,
                    'lat_ns': {'mean': 1000000},
                    'runtime': 30000
                },
                'write': {
                    'bw': 512.0,
                    'iops': 128.0,
                    'lat_ns': {'mean': 2000000},
                    'runtime': 30000
                },
                'job_runtime': 30000,
                'usr_cpu': 5.5,
                'sys_cpu': 2.1
            }],
            'summary': {
                'total_read_bw': 1024.0,
                'total_write_bw': 512.0,
                'total_read_iops': 256.0,
                'total_write_iops': 128.0
            }
        }
    
    def test_enhanced_runner_initialization_with_monitoring(self):
        """Test enhanced runner initialization with monitoring enabled."""
        with patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__'):
            runner = EnhancedFioRunner(enable_monitoring=True, enable_health_checks=True)
            
            assert runner.monitoring_enabled is True
            assert runner.health_checks_enabled is True
            assert runner.monitor is not None
            assert runner.health_checker is not None
    
    def test_enhanced_runner_initialization_without_monitoring(self):
        """Test enhanced runner initialization with monitoring disabled."""
        with patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__'):
            runner = EnhancedFioRunner(enable_monitoring=False, enable_health_checks=False)
            
            assert runner.monitoring_enabled is False
            assert runner.health_checks_enabled is False
            assert runner.monitor is None
            assert runner.health_checker is None
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.run_fio_test')
    def test_run_fio_test_enhanced_success(self, mock_run_fio_test, mock_init, mock_fio_result):
        """Test successful enhanced FIO test execution."""
        # Setup mocks
        mock_init.return_value = None
        mock_run_fio_test.return_value = mock_fio_result
        
        runner = EnhancedFioRunner(enable_monitoring=True, enable_health_checks=True)
        runner.fio_path = '/usr/local/bin/fio'  # Mock FIO path
        
        # Mock health checker
        mock_health_result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="All healthy",
            details={},
            timestamp=time.time(),
            duration_ms=10.0
        )
        runner.health_checker.check_fio_dependency = Mock(return_value=mock_health_result)
        runner.health_checker.check_disk_space = Mock(return_value=mock_health_result)
        runner.health_checker.check_memory_usage = Mock(return_value=mock_health_result)
        runner.health_checker.check_cpu_usage = Mock(return_value=mock_health_result)
        
        # Run enhanced test
        config_content = "[global]\nrw=read\nbs=4k\nsize=1M\nruntime=10\n"
        result = runner.run_fio_test_enhanced(
            config_content=config_content,
            test_directory="/tmp/test",
            estimated_duration=30,
            test_name="test_read"
        )
        
        # Verify result
        assert result is not None
        assert 'error' not in result
        assert 'monitoring' in result
        assert result['monitoring']['monitoring_enabled'] is True
        assert 'test_id' in result['monitoring']
        assert 'system_metrics' in result['monitoring']
        
        # Verify health checks were called
        runner.health_checker.check_fio_dependency.assert_called_once()
        runner.health_checker.check_disk_space.assert_called_once()
        runner.health_checker.check_memory_usage.assert_called_once()
        runner.health_checker.check_cpu_usage.assert_called_once()
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_run_fio_test_enhanced_health_check_failure(self, mock_init):
        """Test enhanced FIO test with critical health check failure."""
        mock_init.return_value = None
        
        runner = EnhancedFioRunner(enable_monitoring=True, enable_health_checks=True)
        runner.fio_path = '/usr/local/bin/fio'
        
        # Mock critical health check failure
        critical_health_result = HealthCheckResult(
            name="fio_dependency",
            status=HealthStatus.CRITICAL,
            message="FIO not found",
            details={'error': 'FIO executable not found'},
            timestamp=time.time(),
            duration_ms=5.0
        )
        
        runner.health_checker.check_fio_dependency = Mock(return_value=critical_health_result)
        runner.health_checker.check_disk_space = Mock(return_value=critical_health_result)
        runner.health_checker.check_memory_usage = Mock(return_value=critical_health_result)
        runner.health_checker.check_cpu_usage = Mock(return_value=critical_health_result)
        
        # Run enhanced test
        config_content = "[global]\nrw=read\nbs=4k\n"
        result = runner.run_fio_test_enhanced(
            config_content=config_content,
            test_directory="/tmp/test",
            estimated_duration=30
        )
        
        # Verify result shows health check failure
        assert result is not None
        assert 'error' in result
        assert result['error'] == 'Pre-test health checks failed'
        assert 'critical_issues' in result
        assert len(result['critical_issues']) > 0
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_extract_test_tags(self, mock_init):
        """Test extraction of test tags from FIO config."""
        mock_init.return_value = None
        runner = EnhancedFioRunner()
        
        config_content = """
[global]
rw=randread
bs=4k
size=100M
runtime=30
numjobs=4
iodepth=32

[test_job]
directory=/tmp/test
"""
        
        tags = runner._extract_test_tags(config_content, "/tmp/test_dir")
        
        assert tags['test_directory'] == 'test_dir'
        assert tags['rw_pattern'] == 'randread'
        assert tags['block_size'] == '4k'
        assert tags['test_size'] == '100M'
        assert tags['runtime'] == '30'
        assert tags['num_jobs'] == '4'
        assert tags['io_depth'] == '32'
        assert 'config_size_bytes' in tags
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_log_test_performance_metrics(self, mock_init, mock_fio_result):
        """Test logging of performance metrics from FIO results."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=True)
        
        # Mock monitor
        runner.monitor = Mock()
        
        tags = {'test_id': 'test123', 'rw_pattern': 'read'}
        runner._log_test_performance_metrics(mock_fio_result, tags)
        
        # Verify metrics were logged
        assert runner.monitor.log_metric.called
        
        # Check some specific metrics were logged
        call_args_list = runner.monitor.log_metric.call_args_list
        metric_names = [call.args[0] for call in call_args_list]
        
        assert 'fio_read_bandwidth_kbs' in metric_names
        assert 'fio_write_bandwidth_kbs' in metric_names
        assert 'fio_read_iops' in metric_names
        assert 'fio_write_iops' in metric_names
        assert 'fio_cpu_user_percent' in metric_names
        assert 'fio_cpu_system_percent' in metric_names
        assert 'fio_total_read_bandwidth_kbs' in metric_names
        assert 'fio_total_write_bandwidth_kbs' in metric_names
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_enhance_results_with_monitoring(self, mock_init, mock_fio_result):
        """Test enhancement of results with monitoring data."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=True)
        
        # Mock monitor
        runner.monitor = Mock()
        runner.monitor.get_system_metrics.return_value = {
            'cpu': {'percent': 25.5},
            'memory': {'percent_used': 60.0}
        }
        runner.monitor.metrics = {
            'test123_duration_seconds': [{'value': 30.5}],
            'fio_read_bandwidth_kbs': [{'value': 1024.0}]
        }
        runner.monitor.get_metric_summary.return_value = {
            'count': 1,
            'avg': 30.5,
            'min': 30.5,
            'max': 30.5
        }
        
        enhanced_result = runner._enhance_results_with_monitoring(
            mock_fio_result, 'test123', 'fio_test_test123'
        )
        
        # Verify monitoring data was added
        assert 'monitoring' in enhanced_result
        monitoring_data = enhanced_result['monitoring']
        
        assert monitoring_data['test_id'] == 'test123'
        assert monitoring_data['operation_name'] == 'fio_test_test123'
        assert monitoring_data['monitoring_enabled'] is True
        assert 'system_metrics' in monitoring_data
        assert 'metrics_collected' in monitoring_data
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_perform_pre_test_health_checks(self, mock_init):
        """Test pre-test health checks execution."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=True, enable_health_checks=True)
        
        # Mock health checker methods
        healthy_result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="Check passed",
            details={},
            timestamp=time.time(),
            duration_ms=5.0
        )
        
        runner.health_checker.check_fio_dependency = Mock(return_value=healthy_result)
        runner.health_checker.check_disk_space = Mock(return_value=healthy_result)
        runner.health_checker.check_memory_usage = Mock(return_value=healthy_result)
        runner.health_checker.check_cpu_usage = Mock(return_value=healthy_result)
        
        # Mock monitor
        runner.monitor = Mock()
        
        results = runner._perform_pre_test_health_checks('test123')
        
        # Verify all checks were called
        assert len(results) == 4
        assert all(r.status == HealthStatus.HEALTHY for r in results)
        
        # Verify metrics were logged
        assert runner.monitor.log_metric.called
        call_args_list = runner.monitor.log_metric.call_args_list
        metric_names = [call.args[0] for call in call_args_list]
        
        assert 'pre_test_health_checks_healthy' in metric_names
        assert 'pre_test_health_checks_warnings' in metric_names
        assert 'pre_test_health_checks_critical' in metric_names
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_get_monitoring_status(self, mock_init):
        """Test getting monitoring system status."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=True, enable_health_checks=True)
        runner.fio_path = '/usr/local/bin/fio'
        
        # Mock monitor
        runner.monitor = Mock()
        runner.monitor.metrics = {'metric1': [1, 2, 3], 'metric2': [4, 5, 6]}
        runner.monitor.log_dir = Path('/tmp/logs')
        
        # Mock health checker
        runner.health_checker = Mock()
        runner.health_checker.run_all_checks.return_value = []
        runner.health_checker.get_health_summary.return_value = {
            'overall_status': 'healthy',
            'healthy': 5,
            'warnings': 1,
            'critical': 0,
            'timestamp': time.time()
        }
        
        status = runner.get_monitoring_status()
        
        assert status['monitoring_enabled'] is True
        assert status['health_checks_enabled'] is True
        assert status['fio_available'] is True
        assert status['metrics_collected'] == 2
        assert status['log_directory'] == '/tmp/logs'
        assert 'health_summary' in status
        assert status['health_summary']['overall_status'] == 'healthy'
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_export_monitoring_data(self, mock_init):
        """Test exporting monitoring data."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=True)
        
        # Mock monitor
        runner.monitor = Mock()
        runner.monitor.export_metrics.return_value = '/tmp/export.json'
        
        export_path = runner.export_monitoring_data()
        
        assert export_path == '/tmp/export.json'
        runner.monitor.export_metrics.assert_called_once_with(None)
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_export_monitoring_data_disabled(self, mock_init):
        """Test exporting monitoring data when monitoring is disabled."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=False)
        
        export_path = runner.export_monitoring_data()
        
        assert export_path is None
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_clear_monitoring_data(self, mock_init):
        """Test clearing monitoring data."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=True)
        
        # Mock monitor
        runner.monitor = Mock()
        
        runner.clear_monitoring_data()
        
        runner.monitor.clear_metrics.assert_called_once()
    
    @patch('diskbench.core.enhanced_fio_runner.FioRunner.__init__')
    def test_clear_monitoring_data_disabled(self, mock_init):
        """Test clearing monitoring data when monitoring is disabled."""
        mock_init.return_value = None
        runner = EnhancedFioRunner(enable_monitoring=False)
        
        # Should not raise an exception
        runner.clear_monitoring_data()


if __name__ == '__main__':
    pytest.main([__file__])
