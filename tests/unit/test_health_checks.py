from types import SimpleNamespace

import pytest

from diskbench.core.health_checks import (
    SystemHealthChecker,
    HealthCheckResult,
    HealthStatus,
)


def test_check_fio_dependency_missing(monkeypatch):
    checker = SystemHealthChecker()
    monkeypatch.setattr('diskbench.core.health_checks.shutil.which', lambda _: None)

    result = checker.check_fio_dependency()

    assert result.status == HealthStatus.CRITICAL
    assert 'FIO not found' in result.message


def test_check_fio_dependency_success(monkeypatch):
    checker = SystemHealthChecker()
    monkeypatch.setattr('diskbench.core.health_checks.shutil.which', lambda _: '/usr/local/bin/fio')

    def fake_run(cmd, capture_output, text, timeout):
        if '--version' in cmd:
            return SimpleNamespace(returncode=0, stdout='fio-3.40\n', stderr='')
        if '--help' in cmd:
            return SimpleNamespace(returncode=0, stdout='usage', stderr='')
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr('diskbench.core.health_checks.subprocess.run', fake_run)

    result = checker.check_fio_dependency()

    assert result.status == HealthStatus.HEALTHY
    assert result.details['fio_version'] == 'fio-3.40'


def test_check_disk_space_thresholds(monkeypatch):
    checker = SystemHealthChecker()

    partitions = [
        SimpleNamespace(device='/dev/disk1', mountpoint='/Volumes/Critical', fstype='apfs'),
        SimpleNamespace(device='/dev/disk2', mountpoint='/Volumes/OK', fstype='apfs'),
    ]

    usage_map = {
        '/Volumes/Critical': SimpleNamespace(total=100 * 1024**3, used=96 * 1024**3, free=4 * 1024**3),
        '/Volumes/OK': SimpleNamespace(total=100 * 1024**3, used=40 * 1024**3, free=60 * 1024**3),
    }

    monkeypatch.setattr('diskbench.core.health_checks.psutil.disk_partitions', lambda: partitions)
    monkeypatch.setattr('diskbench.core.health_checks.psutil.disk_usage', lambda path: usage_map[path])

    result = checker.check_disk_space()

    assert result.status == HealthStatus.CRITICAL
    assert '/Volumes/Critical' in ''.join(result.details['critical_disks'])


def test_check_disk_io_performance(monkeypatch):
    checker = SystemHealthChecker()

    counters = [
        SimpleNamespace(read_bytes=1000, write_bytes=2000, read_count=1, write_count=1),
        SimpleNamespace(read_bytes=2000, write_bytes=5000, read_count=6, write_count=5),
    ]

    monkeypatch.setattr('diskbench.core.health_checks.psutil.disk_io_counters', lambda: counters.pop(0))
    monkeypatch.setattr('diskbench.core.health_checks.time.sleep', lambda sec: None)

    result = checker.check_disk_io_performance()
    assert result.status in {HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL}
    assert 'estimated_avg_latency_ms' in result.details


def test_check_network_connectivity(monkeypatch):
    checker = SystemHealthChecker()

    net_if_addrs = {
        'en0': [SimpleNamespace(family=2, address='192.168.0.10', netmask='255.255.255.0')],
        'lo0': [SimpleNamespace(family=2, address='127.0.0.1', netmask='255.0.0.0')],
    }

    monkeypatch.setattr('diskbench.core.health_checks.psutil.net_if_addrs', lambda: net_if_addrs)
    monkeypatch.setattr('diskbench.core.health_checks.psutil.net_io_counters', lambda: SimpleNamespace(
        bytes_sent=1000,
        bytes_recv=2000,
        packets_sent=10,
        packets_recv=20,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    ))

    result = checker.check_network_connectivity()
    assert result.status == HealthStatus.HEALTHY
    assert len(result.details['active_interfaces']) == 1


def test_check_process_health(monkeypatch):
    checker = SystemHealthChecker()

    class DummyProcess:
        def __init__(self):
            self.pid = 123

        def memory_info(self):
            return SimpleNamespace(rss=200 * 1024**2)

        def cpu_percent(self):
            return 12.5

        def num_threads(self):
            return 8

        def status(self):
            return 'running'

        def create_time(self):
            return 0

    monkeypatch.setattr('diskbench.core.health_checks.psutil.Process', lambda: DummyProcess())
    monkeypatch.setattr('diskbench.core.health_checks.psutil.pids', lambda: [1, 2, 3])

    def process_iter(attrs):
        return iter([
            SimpleNamespace(info={'status': 'running'}),
            SimpleNamespace(info={'status': 'sleeping'}),
        ])

    monkeypatch.setattr('diskbench.core.health_checks.psutil.process_iter', process_iter)

    result = checker.check_process_health()
    assert result.status == HealthStatus.HEALTHY
    assert result.details['current_process']['num_threads'] == 8


def test_run_all_checks_with_monitor(monkeypatch):
    class DummyMonitor:
        def __init__(self):
            self.calls = []

        def log_metric(self, name, value, tags=None, unit=None):
            self.calls.append((name, value, tags, unit))

    checker = SystemHealthChecker(monitor=DummyMonitor())

    def make_result(name, status):
        return HealthCheckResult(
            name=name,
            status=status,
            message='ok',
            details={},
            timestamp=0.0,
            duration_ms=1.0,
        )

    monkeypatch.setattr(checker, 'check_disk_health', lambda: make_result('disk_health', HealthStatus.HEALTHY))
    monkeypatch.setattr(checker, 'check_memory_usage', lambda: make_result('memory_usage', HealthStatus.WARNING))
    monkeypatch.setattr(checker, 'check_cpu_usage', lambda: make_result('cpu_usage', HealthStatus.CRITICAL))
    monkeypatch.setattr(checker, 'check_disk_space', lambda: make_result('disk_space', HealthStatus.HEALTHY))
    monkeypatch.setattr(checker, 'check_fio_dependency', lambda: make_result('fio_dependency', HealthStatus.HEALTHY))
    monkeypatch.setattr(checker, 'check_system_temperatures', lambda: make_result('system_temperatures', HealthStatus.UNKNOWN))
    monkeypatch.setattr(checker, 'check_disk_io_performance', lambda: make_result('disk_io_performance', HealthStatus.WARNING))
    monkeypatch.setattr(checker, 'check_network_connectivity', lambda: make_result('network_connectivity', HealthStatus.HEALTHY))
    monkeypatch.setattr(checker, 'check_process_health', lambda: make_result('process_health', HealthStatus.HEALTHY))

    results = checker.run_all_checks()

    assert len(results) == 9
    statuses = {res.name: res.status for res in results}
    assert statuses['cpu_usage'] == HealthStatus.CRITICAL
    assert checker.monitor.calls  # metrics logged
