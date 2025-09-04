import sys
from pathlib import Path
import json
import pytest

BRIDGE_DIR = Path(__file__).resolve().parents[2] / "bridge-server"
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

import server as bridge


def test_extract_json_from_output_no_json_returns_original():
    b = bridge.DiskBenchBridge()
    text = "no json here\njust logs"
    extracted = b._extract_json_from_output(text)
    assert extracted == text


def test_execute_diskbench_command_parses_json(monkeypatch, tmp_path):
    b = bridge.DiskBenchBridge()

    # Fake subprocess.run result to emulate diskbench outputting JSON
    class Result:
        def __init__(self, rc, out, err):
            self.returncode = rc
            self.stdout = out
            self.stderr = err

    def fake_run(cmd, cwd=None, capture_output=True, text=True, timeout=30, env=None):
        payload = {"success": True, "data": {"answer": 42}}
        return Result(0, json.dumps(payload), "")

    monkeypatch.setattr(bridge.subprocess, 'run', fake_run)

    res = b.execute_diskbench_command(['--version'])
    assert isinstance(res, dict)
    assert res.get('success') is True
    assert res.get('data', {}).get('answer') == 42


def test_execute_diskbench_command_error_path(monkeypatch):
    b = bridge.DiskBenchBridge()

    class Result:
        def __init__(self, rc, out, err):
            self.returncode = rc
            self.stdout = out
            self.stderr = err

    def fake_run(cmd, cwd=None, capture_output=True, text=True, timeout=30, env=None):
        return Result(1, "", "something went wrong")

    monkeypatch.setattr(bridge.subprocess, 'run', fake_run)

    res = b.execute_diskbench_command(['--list-disks'])
    assert res['success'] is False
    assert 'something went wrong' in res['error']
