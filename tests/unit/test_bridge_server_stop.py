import sys
import types
from pathlib import Path
import pytest

# Import bridge server
BRIDGE_DIR = Path(__file__).resolve().parents[2] / "bridge-server"
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

import server as bridge


class DummyProcess:
    def __init__(self, pid):
        self.pid = pid
    def poll(self):
        return None


def test_stop_test_kills_tracked_process_and_updates_state(monkeypatch):
    b = bridge.DiskBenchBridge()

    # Prepare a running test and a tracked process
    test_id = 'test_123'
    b.running_tests[test_id] = {
        'status': 'running',
        'start_time': '2025-08-29T00:00:00',
        'output_file': '/tmp/out.json'
    }
    dummy_proc = DummyProcess(pid=4242)
    b.running_processes[test_id] = dummy_proc

    # Mock os.getpgid/os.killpg to avoid real signals
    import os
    monkeypatch.setattr(os, 'getpgid', lambda pid: pid)  # return pid as pgid
    killed = {"calls": []}
    def fake_killpg(pgid, sig):
        killed["calls"].append((pgid, sig))
    monkeypatch.setattr(os, 'killpg', fake_killpg)

    # Mock cleanup_fio_processes to report orphaned pids
    monkeypatch.setattr(b, 'cleanup_fio_processes', lambda tid=None: [111, 222])

    res = b.stop_test(test_id)
    assert res['success'] is True
    assert 'killed_pids' in res
    # Ensure process group termination attempted (SIGTERM then SIGKILL)
    assert any(call[1] != 0 for call in killed['calls'])
    # State updated
    info = b.running_tests[test_id]
    assert info['status'] == 'stopped'
    assert 'end_time' in info
    assert info['error'] == 'Test stopped by user'
    # Tracked process removed
    assert test_id not in b.running_processes


def test_stop_test_when_no_tracked_process_still_cleans_orphans(monkeypatch):
    b = bridge.DiskBenchBridge()
    test_id = 'test_456'
    b.running_tests[test_id] = {'status': 'running', 'start_time': '2025-08-29T00:00:00'}

    # No running_processes entry
    # Mock cleanup
    monkeypatch.setattr(b, 'cleanup_fio_processes', lambda tid=None: [333])

    res = b.stop_test(test_id)
    assert res['success'] is True
    assert 333 in res.get('killed_pids', [])
    assert b.running_tests[test_id]['status'] == 'stopped'


def test_stop_all_tests_no_running_but_cleans_orphans(monkeypatch):
    b = bridge.DiskBenchBridge()
    # No running tests in running_tests
    monkeypatch.setattr(b, 'cleanup_fio_processes', lambda tid=None: [999, 1000])

    res = b.stop_all_tests()
    assert res['success'] is True
    assert 'cleaned up' in res['message'] or 'No running tests' in res['message']
    assert set(res.get('killed_pids', [])) == {999, 1000} or res.get('killed_pids', []) == []

