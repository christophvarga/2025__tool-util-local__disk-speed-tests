import sys
from pathlib import Path
import pytest

DISKBENCH_DIR = Path(__file__).resolve().parents[2] / "diskbench"
if str(DISKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(DISKBENCH_DIR))

from core.exceptions import (
    DiskBenchError, FIOExecutionError, DiskNotAvailableError, 
    InsufficientSpaceError, InvalidTestConfigError, JSONParsingError
)


def test_diskbench_error_base():
    err = DiskBenchError("Something went wrong", context={'key': 'value'}, recovery_hint="Try again")
    assert str(err) == "Something went wrong"
    assert err.context == {'key': 'value'}
    assert err.recovery_hint == "Try again"
    assert err.timestamp is not None


def test_diskbench_error_to_dict():
    err = DiskBenchError("Test error")
    d = err.to_dict()
    assert d['error_type'] == 'DiskBenchError'
    assert d['message'] == 'Test error'
    assert 'timestamp' in d


def test_fio_execution_error():
    err = FIOExecutionError("FIO failed", return_code=1, stdout="output", stderr="error")
    assert "FIO failed" in str(err)
    assert err.context['return_code'] == 1
    assert err.context['stdout'] == "output"
    assert err.context['stderr'] == "error"
    assert "Check FIO installation" in err.recovery_hint


def test_disk_not_available_error():
    err = DiskNotAvailableError("/Volumes/Test", "not mounted")
    assert "/Volumes/Test" in str(err)
    assert "not mounted" in str(err)
    assert err.context['disk_path'] == "/Volumes/Test"
    assert err.context['reason'] == "not mounted"


def test_insufficient_space_error():
    err = InsufficientSpaceError(10.0, 5.0, "/Volumes/Test")
    assert "need 10.0GB" in str(err)
    assert "have 5.0GB" in str(err)
    assert err.context['required_gb'] == 10.0
    assert err.context['available_gb'] == 5.0


def test_json_parsing_error():
    err = JSONParsingError("Invalid JSON", line_no=42, column_no=10, content_preview="{'invalid'")
    assert "JSON parsing failed" in str(err)
    assert err.context['line_no'] == 42
    assert err.context['column_no'] == 10
    assert err.context['content_preview'] == "{'invalid'"
