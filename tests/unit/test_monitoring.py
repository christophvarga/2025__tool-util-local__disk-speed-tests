import json
import logging
from types import SimpleNamespace

import pytest

from diskbench.core.monitoring import JSONFormatter, PerformanceMonitor


@pytest.fixture
def mocked_psutil(monkeypatch):
    monkeypatch.setattr('diskbench.core.monitoring.psutil.cpu_percent', lambda interval=0.1: 12.5)
    monkeypatch.setattr('diskbench.core.monitoring.psutil.cpu_count', lambda: 8)
    monkeypatch.setattr('diskbench.core.monitoring.psutil.cpu_freq', lambda: SimpleNamespace(current=2400))
    monkeypatch.setattr('diskbench.core.monitoring.psutil.virtual_memory', lambda: SimpleNamespace(
        total=8 * 1024**3,
        available=4 * 1024**3,
        percent=50.0,
        used=4 * 1024**3,
        free=4 * 1024**3
    ))
    monkeypatch.setattr('diskbench.core.monitoring.psutil.swap_memory', lambda: SimpleNamespace(
        total=2 * 1024**3,
        used=1 * 1024**3
    ))
    monkeypatch.setattr('diskbench.core.monitoring.psutil.disk_io_counters', lambda: SimpleNamespace(
        read_bytes=1024,
        write_bytes=2048,
        read_count=10,
        write_count=20
    ))
    monkeypatch.setattr('diskbench.core.monitoring.psutil.net_io_counters', lambda: SimpleNamespace(
        bytes_sent=1234,
        bytes_recv=5678
    ))

    class DummyProcess:
        def __init__(self):
            self.pid = 999

        def memory_info(self):
            return SimpleNamespace(rss=256 * 1024**2)

        def cpu_percent(self):
            return 7.5

        def num_threads(self):
            return 5

    monkeypatch.setattr('diskbench.core.monitoring.psutil.Process', lambda: DummyProcess())


def test_json_formatter_includes_extra_fields():
    formatter = JSONFormatter()
    logger = logging.getLogger('diskbench.test')
    record = logger.makeRecord(
        name='diskbench.test',
        level=logging.INFO,
        fn='test.py',
        lno=10,
        msg='Hello',
        args=(),
        exc_info=None,
        func='func',
        sinfo=None,
        extra={'extra_fields': {'metric': 'm1', 'timestamp': 1.0}}
    )

    payload = json.loads(formatter.format(record))
    assert payload['metric'] == 'm1'
    assert 'event_ts' in payload


def test_performance_monitor_collects_metrics(tmp_path, mocked_psutil):
    monitor = PerformanceMonitor(log_dir=str(tmp_path))
    monitor.log_metric('test_metric', 1.23, tags={'a': 'b'}, unit='seconds')
    monitor.log_metric('test_metric', 2.34)

    assert 'test_metric' in monitor.metrics
    assert len(monitor.metrics['test_metric']) == 2
    export_path = monitor.export_metrics(output_file=str(tmp_path / 'export.json'))
    assert export_path.endswith('export.json')
    data = json.loads(tmp_path.joinpath('export.json').read_text())
    assert 'collected_metrics' in data
    monitor.clear_metrics()
    assert monitor.metrics == {}


def test_measure_operation_success(tmp_path, mocked_psutil):
    monitor = PerformanceMonitor(log_dir=str(tmp_path))
    calls = []

    def fake_log_metric(name, value, tags=None, unit=None):
        calls.append((name, value, tags, unit))

    monitor.log_metric = fake_log_metric
    monitor.get_system_metrics = lambda: {'cpu': {'percent': 10}, 'memory': {'total_gb': 8, 'available_gb': 4}}

    with monitor.measure_operation('op_success', tags={'phase': 'test'}):
        pass

    assert calls
    assert calls[-1][0] == 'op_success_duration_seconds'
    assert calls[-1][2]['status'] == 'success'


def test_measure_operation_failure(tmp_path, mocked_psutil):
    monitor = PerformanceMonitor(log_dir=str(tmp_path))
    calls = []

    def fake_log_metric(name, value, tags=None, unit=None):
        calls.append((name, value, tags, unit))

    monitor.log_metric = fake_log_metric
    monitor.get_system_metrics = lambda: {'cpu': {'percent': 10}}

    with pytest.raises(RuntimeError):
        with monitor.measure_operation('op_fail', tags={'id': 1}):
            raise RuntimeError('boom')

    assert calls
    assert calls[-1][2]['status'] == 'failure'


def test_get_metric_summary_errors(tmp_path, mocked_psutil):
    monitor = PerformanceMonitor(log_dir=str(tmp_path))
    assert 'error' in monitor.get_metric_summary('missing')
    monitor.metrics['sample'] = []
    assert 'error' in monitor.get_metric_summary('sample')
    monitor.metrics['sample'] = [{'value': 1, 'unit': 'kbs'}, {'value': 3, 'unit': 'kbs'}]
    summary = monitor.get_metric_summary('sample')
    assert summary['avg'] == 2
    assert summary['unit'] == 'kbs'
