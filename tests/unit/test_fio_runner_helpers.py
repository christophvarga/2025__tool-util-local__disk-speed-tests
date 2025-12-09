import json
from types import SimpleNamespace

import pytest

from diskbench.core.fio_runner import FioRunner, FIOExecutionError


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.setattr(FioRunner, "_find_fio_binary", lambda self: "/tmp/fio")
    return FioRunner()


def test_extract_io_stats_prefers_bw_bytes(runner):
    stats = runner._extract_io_stats({'bw_bytes': 2048, 'iops_mean': 5})
    assert stats['bw'] == 2
    assert stats['iops'] == 5


def test_calculate_summary_aggregates(runner):
    jobs = [{
        'read': {'iops': 100, 'bw_bytes': 1024 * 1024, 'lat_ns': {'mean': 2_000_000}},
        'write': {'iops': 50, 'bw': 2048, 'lat_ns': {'mean': 4_000_000}},
        'job_runtime': 2000
    }]
    summary = runner._calculate_summary(jobs)
    assert summary['total_read_iops'] == 100
    assert summary['total_write_iops'] == 50
    assert summary['total_read_bw'] == 1024
    assert summary['total_write_bw'] == 2048
    assert summary['avg_read_latency'] == pytest.approx(2.0)
    assert summary['avg_write_latency'] == pytest.approx(4.0)
    assert summary['total_runtime'] == 2000


def test_process_fio_results_wraps_jobs_and_summary(runner):
    fio_json = {
        'fio version': 'fio-3.40',
        'timestamp': 123,
        'jobs': [{
            'jobname': 'job1',
            'read': {'bw_bytes': 1024, 'iops': 10, 'lat_ns': {'mean': 1_000_000}},
            'write': {'bw': 512, 'iops': 5, 'lat_ns': {'mean': 2_000_000}},
            'trim': {},
            'sync': {},
            'job_runtime': 1000,
            'usr_cpu': 10,
            'sys_cpu': 5,
        }]
    }

    result = runner._process_fio_results(fio_json)

    assert result['fio_version'] == 'fio-3.40'
    assert result['summary']['total_read_iops'] == 10
    assert result['jobs'][0]['read']['bw'] == 1.0
    assert result['jobs'][0]['write']['bw'] == 512
    assert result['engine'] == 'homebrew_fio'


def test_clean_json_output_filters_noise(runner):
    raw_output = """
fio-3.40
Starting 1 job
{
  "fio version": "fio-3.40",
  "jobs": []
}
"""

    cleaned = runner._clean_json_output(raw_output)
    assert cleaned.startswith('{')
    assert 'Starting' not in cleaned


def test_run_fio_test_without_binary_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(FioRunner, "_find_fio_binary", lambda self: None)
    runner = FioRunner()
    with pytest.raises(Exception) as exc:
        runner.run_fio_test('[global]', str(tmp_path / 't'), 0)
    assert isinstance(exc.value, (FIOExecutionError, TypeError))


def test_get_fio_status_success(monkeypatch, runner):
    def fake_run(cmd, capture_output, text, timeout):
        assert cmd == ['/tmp/fio', '--version']
        return SimpleNamespace(returncode=0, stdout='fio-3.40\n')

    monkeypatch.setattr('diskbench.core.fio_runner.subprocess.run', fake_run)

    status = runner.get_fio_status()
    assert status['available'] is True
    assert status['version'] == 'fio-3.40'


def test_stop_fio_test_without_process_returns_false(runner):
    assert runner.stop_fio_test() is False
