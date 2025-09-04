"""
Unit tests for monitoring and health checks modules.
"""
import pytest
import json
import time
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from diskbench.core.monitoring import PerformanceMonitor, JSONFormatter
from diskbench.core.health_checks import (
    SystemHealthChecker, HealthStatus, HealthCheckResult
)


class TestJSONFormatter:
    """Test JSON formatter for structured logging."""
    
    def test_basic_formatting(self):
        """Test basic log record formatting."""
        formatter = JSONFormatter()
        
        # Create a mock log record
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='/test/file.py',
            lineno=123,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.module = 'test_module'
        record.funcName = 'test_function'
        record.created = 1640995200.0  # Fixed timestamp
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['level'] == 'INFO'
        assert data['logger'] == 'test_logger'
        assert data['message'] == 'Test message'
        assert data['module'] == 'test_module'
        assert data['function'] == 'test_function'
        assert data['line'] == 123
        assert 'log_ts' in data
    
    def test_formatting_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='/test/file.py',
            lineno=123,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.module = 'test_module'
        record.funcName = 'test_function'
        record.created = 1640995200.0
        record.extra_fields = {
            'test_id': 'test-123',
            'operation': 'disk_test'
        }
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['test_id'] == 'test-123'
        assert data['operation'] == 'disk_test'
    
    def test_formatting_with_context_fields(self):
        """Test formatting with context fields."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='/test/file.py',
            lineno=123,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.module = 'test_module'
        record.funcName = 'test_function'
        record.created = 1640995200.0
        record.test_id = 'ctx-test-123'
        record.duration = 5.25
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data['test_id'] == 'ctx-test-123'
        assert data['duration'] == 5.25


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_monitor_initialization(self, temp_log_dir):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        assert monitor.log_dir == Path(temp_log_dir)
        assert monitor.log_dir.exists()
        assert len(monitor.metrics) == 0
        assert hasattr(monitor, '_system_baseline')
    
    @patch('diskbench.core.monitoring.psutil')
    def test_get_system_metrics(self, mock_psutil, temp_log_dir):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.cpu_count.return_value = 8
        mock_cpu_freq = Mock()
        mock_cpu_freq.current = 2800
        mock_psutil.cpu_freq.return_value = mock_cpu_freq
        
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_swap = Mock()
        mock_swap.total = 4 * 1024**3
        mock_swap.used = 1 * 1024**3
        mock_psutil.swap_memory.return_value = mock_swap
        
        # Mock process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.num_threads.return_value = 8
        mock_memory_info = Mock()
        mock_memory_info.rss = 256 * 1024**2
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process
        
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        metrics = monitor.get_system_metrics()
        
        assert metrics['cpu']['percent'] == 25.5
        assert metrics['cpu']['count'] == 8
        assert metrics['cpu']['frequency_mhz'] == 2800
        assert metrics['memory']['total_gb'] == 16.0
        assert metrics['memory']['percent_used'] == 50.0
        assert metrics['process']['pid'] == 12345
        assert metrics['process']['memory_mb'] == 256.0
        assert 'uptime_seconds' in metrics
        assert 'timestamp' in metrics
    
    def test_log_metric(self, temp_log_dir):
        """Test metric logging."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        monitor.log_metric(
            'test_metric',
            42.5,
            tags={'test': 'value'},
            unit='seconds'
        )
        
        assert 'test_metric' in monitor.metrics
        assert len(monitor.metrics['test_metric']) == 1
        
        metric_data = monitor.metrics['test_metric'][0]
        assert metric_data['metric'] == 'test_metric'
        assert metric_data['value'] == 42.5
        assert metric_data['tags'] == {'test': 'value'}
        assert metric_data['unit'] == 'seconds'
        assert 'event_ts' in metric_data
    
    def test_measure_operation_success(self, temp_log_dir):
        """Test successful operation measurement."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        with monitor.measure_operation('test_operation', tags={'test': 'tag'}):
            time.sleep(0.1)  # Small delay to measure
        
        # Check that metrics were logged
        metric_name = 'test_operation_duration_seconds'
        assert metric_name in monitor.metrics
        metric = monitor.metrics[metric_name][0]
        assert metric['tags']['status'] == 'success'
        assert metric['value'] > 0.05  # Should be at least 0.05 seconds
    
    def test_measure_operation_failure(self, temp_log_dir):
        """Test operation measurement with exception."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        with pytest.raises(ValueError):
            with monitor.measure_operation('failing_operation'):
                raise ValueError("Test error")
        
        # Check that failure metrics were logged
        metric_name = 'failing_operation_duration_seconds'
        assert metric_name in monitor.metrics
        metric = monitor.metrics[metric_name][0]
        assert metric['tags']['status'] == 'failure'
    
    def test_get_metric_summary(self, temp_log_dir):
        """Test metric summary calculation."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        # Log several metrics
        for i in range(5):
            monitor.log_metric('test_metric', float(i + 1))
        
        summary = monitor.get_metric_summary('test_metric')
        
        assert summary['count'] == 5
        assert summary['min'] == 1.0
        assert summary['max'] == 5.0
        assert summary['avg'] == 3.0
        assert summary['latest'] == 5.0
    
    def test_get_metric_summary_nonexistent(self, temp_log_dir):
        """Test metric summary for nonexistent metric."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        summary = monitor.get_metric_summary('nonexistent_metric')
        assert 'error' in summary
    
    def test_export_metrics(self, temp_log_dir):
        """Test metrics export to JSON."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        # Add some metrics
        monitor.log_metric('test_metric1', 10.0, unit='seconds')
        monitor.log_metric('test_metric2', 20.0, unit='bytes')
        
        export_file = monitor.export_metrics()
        
        assert Path(export_file).exists()
        
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        assert 'export_timestamp' in data
        assert 'system_baseline' in data
        assert 'current_system_metrics' in data
        assert 'collected_metrics' in data
        assert 'metric_summaries' in data
        
        assert 'test_metric1' in data['collected_metrics']
        assert 'test_metric2' in data['collected_metrics']
    
    def test_clear_metrics(self, temp_log_dir):
        """Test metrics clearing."""
        monitor = PerformanceMonitor(log_dir=temp_log_dir)
        
        # Add some metrics
        monitor.log_metric('test_metric1', 10.0)
        monitor.log_metric('test_metric2', 20.0)
        
        assert len(monitor.metrics) == 2
        
        monitor.clear_metrics()
        
        assert len(monitor.metrics) == 0


class TestSystemHealthChecker:
    """Test system health checking functionality."""
    
    @pytest.fixture
    def health_checker(self):
        """Create health checker instance."""
        return SystemHealthChecker()
    
    def test_health_checker_initialization(self, health_checker):
        """Test health checker initialization."""
        assert health_checker.monitor is None
        assert health_checker.last_check_time == 0
        assert health_checker.check_interval == 60
        assert 'disk_space_warning_percent' in health_checker.thresholds
        assert health_checker.thresholds['disk_space_warning_percent'] == 85
    
    @patch('diskbench.core.health_checks.psutil')
    def test_check_memory_usage_healthy(self, mock_psutil, health_checker):
        """Test healthy memory usage check."""
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 10 * 1024**3
        mock_memory.percent = 50.0
        mock_memory.free = 6 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_swap = Mock()
        mock_swap.total = 4 * 1024**3
        mock_swap.used = 1 * 1024**3
        mock_swap.percent = 25.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        result = health_checker.check_memory_usage()
        
        assert result.name == "memory_usage"
        assert result.status == HealthStatus.HEALTHY
        assert "50.0%" in result.message
        assert result.details['memory']['used_percent'] == 50.0
        assert result.details['swap']['used_percent'] == 25.0
    
    @patch('diskbench.core.health_checks.psutil')
    def test_check_memory_usage_critical(self, mock_psutil, health_checker):
        """Test critical memory usage check."""
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 1 * 1024**3
        mock_memory.percent = 97.0
        mock_memory.free = 0.5 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_swap = Mock()
        mock_swap.total = 4 * 1024**3
        mock_swap.used = 3.8 * 1024**3
        mock_swap.percent = 95.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        result = health_checker.check_memory_usage()
        
        assert result.status == HealthStatus.CRITICAL
        assert "Critical memory usage" in result.message
    
    @patch('diskbench.core.health_checks.psutil')
    def test_check_cpu_usage_healthy(self, mock_psutil, health_checker):
        """Test healthy CPU usage check."""
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.cpu_count.return_value = 8
        
        # Mock load average
        with patch('os.getloadavg', return_value=(2.0, 1.5, 1.0)):
            result = health_checker.check_cpu_usage()
        
        assert result.name == "cpu_usage"
        assert result.status == HealthStatus.HEALTHY
        assert "25.5%" in result.message
        assert "Load: 25.0%" in result.message  # (2.0 / 8) * 100 = 25%
    
    @patch('diskbench.core.health_checks.psutil')
    def test_check_cpu_usage_critical(self, mock_psutil, health_checker):
        """Test critical CPU usage check."""
        mock_psutil.cpu_percent.return_value = 99.5
        mock_psutil.cpu_count.return_value = 4
        
        result = health_checker.check_cpu_usage()
        
        assert result.status == HealthStatus.CRITICAL
        assert "Critical CPU usage: 99.5%" in result.message
    
    @patch('diskbench.core.health_checks.shutil')
    @patch('diskbench.core.health_checks.subprocess')
    def test_check_fio_dependency_available(self, mock_subprocess, mock_shutil, health_checker):
        """Test FIO dependency check when FIO is available."""
        mock_shutil.which.return_value = '/usr/local/bin/fio'
        
        # Mock version check
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = 'fio-3.16'
        
        # Mock help check
        help_result = Mock()
        help_result.returncode = 0
        
        mock_subprocess.run.side_effect = [version_result, help_result]
        
        result = health_checker.check_fio_dependency()
        
        assert result.name == "fio_dependency"
        assert result.status == HealthStatus.HEALTHY
        assert "fio-3.16" in result.message
        assert result.details['fio_path'] == '/usr/local/bin/fio'
        assert result.details['version_check_success'] is True
    
    @patch('diskbench.core.health_checks.shutil')
    def test_check_fio_dependency_missing(self, mock_shutil, health_checker):
        """Test FIO dependency check when FIO is missing."""
        mock_shutil.which.return_value = None
        
        result = health_checker.check_fio_dependency()
        
        assert result.status == HealthStatus.CRITICAL
        assert "FIO not found" in result.message
    
    @patch('diskbench.core.health_checks.psutil')
    def test_check_disk_space_healthy(self, mock_psutil, health_checker):
        """Test healthy disk space check."""
        # Mock partition
        mock_partition = Mock()
        mock_partition.device = '/dev/sda1'
        mock_partition.mountpoint = '/'
        mock_partition.fstype = 'ext4'
        mock_psutil.disk_partitions.return_value = [mock_partition]
        
        # Mock usage - 60% used
        mock_usage = Mock()
        mock_usage.total = 1000 * 1024**3
        mock_usage.used = 600 * 1024**3
        mock_usage.free = 400 * 1024**3
        mock_psutil.disk_usage.return_value = mock_usage
        
        result = health_checker.check_disk_space()
        
        assert result.status == HealthStatus.HEALTHY
        assert "healthy on all 1 disk(s)" in result.message
        assert len(result.details['disks']) == 1
        assert result.details['disks'][0]['used_percent'] == 60.0
    
    @patch('diskbench.core.health_checks.psutil')
    def test_check_disk_space_critical(self, mock_psutil, health_checker):
        """Test critical disk space check."""
        # Mock partition
        mock_partition = Mock()
        mock_partition.device = '/dev/sda1'
        mock_partition.mountpoint = '/'
        mock_partition.fstype = 'ext4'
        mock_psutil.disk_partitions.return_value = [mock_partition]
        
        # Mock usage - 96% used (critical)
        mock_usage = Mock()
        mock_usage.total = 1000 * 1024**3
        mock_usage.used = 960 * 1024**3
        mock_usage.free = 40 * 1024**3
        mock_psutil.disk_usage.return_value = mock_usage
        
        result = health_checker.check_disk_space()
        
        assert result.status == HealthStatus.CRITICAL
        assert "Critical disk space" in result.message
        assert len(result.details['critical_disks']) == 1
    
    def test_run_all_checks(self, health_checker):
        """Test running all health checks."""
        with patch.object(health_checker, 'check_disk_health') as mock_disk_health, \
             patch.object(health_checker, 'check_memory_usage') as mock_memory, \
             patch.object(health_checker, 'check_cpu_usage') as mock_cpu:
            
            # Mock return values
            mock_disk_health.return_value = HealthCheckResult(
                name="disk_health",
                status=HealthStatus.HEALTHY,
                message="All disks healthy",
                details={},
                timestamp=time.time(),
                duration_ms=10.0
            )
            
            mock_memory.return_value = HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.WARNING,
                message="High memory usage",
                details={},
                timestamp=time.time(),
                duration_ms=5.0
            )
            
            mock_cpu.return_value = HealthCheckResult(
                name="cpu_usage",
                status=HealthStatus.HEALTHY,
                message="CPU usage normal",
                details={},
                timestamp=time.time(),
                duration_ms=8.0
            )
            
            # Run checks
            results = health_checker.run_all_checks()
            
            # Should have run 9 checks (even if some are mocked)
            assert len(results) == 9
            assert health_checker.last_check_time > 0
    
    def test_get_health_summary(self, health_checker):
        """Test health summary generation."""
        # Create test results
        results = [
            HealthCheckResult(
                name="test1",
                status=HealthStatus.HEALTHY,
                message="All good",
                details={},
                timestamp=time.time(),
                duration_ms=10.0
            ),
            HealthCheckResult(
                name="test2",
                status=HealthStatus.WARNING,
                message="Warning detected",
                details={},
                timestamp=time.time(),
                duration_ms=15.0
            ),
            HealthCheckResult(
                name="test3",
                status=HealthStatus.CRITICAL,
                message="Critical issue",
                details={},
                timestamp=time.time(),
                duration_ms=20.0
            )
        ]
        
        summary = health_checker.get_health_summary(results)
        
        assert summary['total_checks'] == 3
        assert summary['healthy'] == 1
        assert summary['warnings'] == 1
        assert summary['critical'] == 1
        assert summary['unknown'] == 0
        assert summary['overall_status'] == 'critical'  # Critical takes precedence
        assert len(summary['details']) == 3
    
    def test_determine_overall_status(self, health_checker):
        """Test overall status determination logic."""
        # All healthy
        healthy_results = [
            HealthCheckResult("test", HealthStatus.HEALTHY, "msg", {}, time.time(), 10.0)
        ]
        assert health_checker._determine_overall_status(healthy_results) == "healthy"
        
        # Has warning
        warning_results = [
            HealthCheckResult("test1", HealthStatus.HEALTHY, "msg", {}, time.time(), 10.0),
            HealthCheckResult("test2", HealthStatus.WARNING, "msg", {}, time.time(), 10.0)
        ]
        assert health_checker._determine_overall_status(warning_results) == "warning"
        
        # Has critical
        critical_results = [
            HealthCheckResult("test1", HealthStatus.HEALTHY, "msg", {}, time.time(), 10.0),
            HealthCheckResult("test2", HealthStatus.WARNING, "msg", {}, time.time(), 10.0),
            HealthCheckResult("test3", HealthStatus.CRITICAL, "msg", {}, time.time(), 10.0)
        ]
        assert health_checker._determine_overall_status(critical_results) == "critical"


if __name__ == '__main__':
    pytest.main([__file__])
