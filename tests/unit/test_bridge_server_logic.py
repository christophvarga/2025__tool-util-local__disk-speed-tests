import os
import sys
import types
import pytest

from pathlib import Path

# Ensure bridge-server is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_DIR = REPO_ROOT / "bridge-server"
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

import server as bridge  # bridge-server/server.py


class DummyThread:
    """A dummy replacement for threading.Thread that does not start."""
    def __init__(self, target=None, args=()):
        self.target = target
        self.args = args
        self.daemon = False
    def start(self):
        # Do not execute the target; tests will inspect state only
        return


def test_extract_json_from_output_mixed_logs():
    b = bridge.DiskBenchBridge()
    mixed = """
    INFO: starting test
    some logs...
    {"success": true, "value": 42}
    trailing text that should be ignored
    """.strip()

    extracted = b._extract_json_from_output(mixed)
    assert extracted.strip().endswith('}')
    data = __import__('json').loads(extracted)
    assert data["success"] is True
    assert data["value"] == 42


def test_start_test_rejects_when_already_running(monkeypatch):
    b = bridge.DiskBenchBridge()

    # Pretend fio is available
    monkeypatch.setattr(b, "_verify_fio", lambda: {"path": "/usr/local/bin/fio", "version": "fio-3.40"})

    # Insert a running test
    b.running_tests["test_1"] = {"status": "running"}
    result = b.start_test({"test_type": "quick_max_speed", "disk_path": "/Volumes/Test", "size_gb": 1})
    assert result["success"] is False
    assert "already running" in result["error"]


def test_start_test_mapping_and_validation(monkeypatch):
    b = bridge.DiskBenchBridge()

    # Pretend fio is available
    monkeypatch.setattr(b, "_verify_fio", lambda: {"path": "/usr/local/bin/fio", "version": "fio-3.40"})

    # Prevent background thread from starting
    import threading
    monkeypatch.setattr(threading, "Thread", DummyThread)

    # Use known legacy GUI id that should map to diskbench id
    params = {"test_type": "quick_max_speed", "disk_path": "/Volumes/Test", "size_gb": 1, "show_progress": False}
    result = b.start_test(params)
    assert result["success"] is True
    assert result["diskbench_test_type"] == "quick_max_mix"
    test_id = result["test_id"]
    assert test_id in b.running_tests
    assert b.running_tests[test_id]["status"] in {"starting", "running"}

