import sys
import pytest
from pathlib import Path

# Import the FioRunner from diskbench
DISKBENCH_DIR = Path(__file__).resolve().parents[2] / "diskbench"
if str(DISKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(DISKBENCH_DIR))

from core.fio_runner import FioRunner


@pytest.fixture()
def runner():
    return FioRunner()


def test_process_handles_none_input(runner):
    processed = runner._process_fio_results(None)
    assert isinstance(processed, dict)
    summary = processed.get('summary', {})
    assert summary.get('total_read_bw', 0) == 0
    assert summary.get('total_write_bw', 0) == 0


def test_process_handles_missing_jobs(runner):
    processed = runner._process_fio_results({})
    summary = processed.get('summary', {})
    assert summary.get('total_runtime', 0) == 0


def test_process_handles_non_list_jobs(runner):
    data = {"jobs": {"not": "a list"}}
    processed = runner._process_fio_results(data)
    assert isinstance(processed, dict)
    assert processed.get('summary', {}).get('total_read_iops', 0) == 0


def test_process_negative_values_propagate_but_no_crash(runner):
    data = {
        "jobs": [{
            "read": {"bw": -500, "iops": -10, "lat_ns": {"mean": -1000}},
            "write": {"bw": -400, "iops": -20, "lat_ns": {"mean": -2000}},
            "job_runtime": -5
        }]
    }
    processed = runner._process_fio_results(data)
    s = processed.get('summary', {})
    # Parser sollte nicht crashen und numerische Werte liefern
    for key in [
        'total_read_bw', 'total_write_bw', 'total_read_iops', 'total_write_iops',
        'avg_read_latency', 'avg_write_latency', 'total_runtime']:
        assert key in s
        assert isinstance(s[key], (int, float))


def test_process_missing_latency_structures(runner):
    data = {
        "jobs": [{
            "read": {"bw": 1000, "iops": 10},  # no lat_ns
            "write": {"bw": 500, "iops": 5, "lat_ns": {}},
            "job_runtime": 1000
        }]
    }
    processed = runner._process_fio_results(data)
    s = processed.get('summary', {})
    # read latency default to 0 if missing
    assert s.get('avg_read_latency', 0) >= 0
    assert s.get('avg_write_latency', 0) >= 0

