"""Tests for the refactored cleanup_fio_processes() PID-based tracking logic.

Covers:
- Targeted cleanup by test_id (primary path)
- General sweep of all tracked processes
- ps aux fallback for untracked orphans
- Edge cases: already-exited processes, permission errors
"""
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BRIDGE_DIR = Path(__file__).resolve().parents[2] / "bridge-server"
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

import server as bridge


class FakePopen:
    """Minimal subprocess.Popen stand-in for tests."""

    def __init__(self, pid: int):
        self.pid = pid

    def poll(self):
        return None


def _make_bridge(monkeypatch) -> bridge.DiskBenchBridge:
    """Create a DiskBenchBridge with startup side-effects suppressed."""
    b = bridge.DiskBenchBridge()
    b.running_processes.clear()
    b.running_tests.clear()
    return b


# ---- targeted cleanup (test_id given) ----

def test_cleanup_targeted_kills_tracked_process(monkeypatch):
    """When test_id is given and the process is alive, it should be killed."""
    b = _make_bridge(monkeypatch)
    proc = FakePopen(pid=5555)
    b.running_processes["t1"] = proc

    kill_calls = []

    def fake_kill(pid, sig):
        kill_calls.append((pid, sig))
        if sig == 0:
            return  # alive
    monkeypatch.setattr(os, "kill", fake_kill)

    killed = b.cleanup_fio_processes(test_id="t1")
    assert 5555 in killed
    # Should have sent signal 0 (alive check), 15 (SIGTERM), 0 (alive check), maybe 9
    sigs = [s for _, s in kill_calls if _ == 5555]
    assert 0 in sigs
    assert 15 in sigs
    # Process removed from registry
    assert "t1" not in b.running_processes


def test_cleanup_targeted_already_exited(monkeypatch):
    """When test_id is given but the process already exited, return empty."""
    b = _make_bridge(monkeypatch)
    proc = FakePopen(pid=6666)
    b.running_processes["t2"] = proc

    def fake_kill(pid, sig):
        raise ProcessLookupError("No such process")
    monkeypatch.setattr(os, "kill", fake_kill)

    killed = b.cleanup_fio_processes(test_id="t2")
    assert killed == []
    assert "t2" not in b.running_processes


def test_cleanup_targeted_no_tracked_process(monkeypatch):
    """When test_id has no tracked process, return empty list."""
    b = _make_bridge(monkeypatch)
    killed = b.cleanup_fio_processes(test_id="nonexistent")
    assert killed == []


# ---- general sweep (test_id=None) ----

def test_cleanup_sweep_kills_all_tracked(monkeypatch):
    """Without test_id, all tracked processes should be killed."""
    b = _make_bridge(monkeypatch)
    b.running_processes["a"] = FakePopen(pid=1001)
    b.running_processes["b"] = FakePopen(pid=1002)

    kill_calls = []

    def fake_kill(pid, sig):
        kill_calls.append((pid, sig))
        if sig == 0:
            return
    monkeypatch.setattr(os, "kill", fake_kill)

    # Suppress ps aux fallback
    monkeypatch.setattr(b, "_find_orphan_fio_pids", lambda: [])

    killed = b.cleanup_fio_processes()
    assert 1001 in killed
    assert 1002 in killed
    assert len(b.running_processes) == 0


def test_cleanup_sweep_includes_orphan_fallback(monkeypatch):
    """General sweep should also pick up untracked orphans via ps aux."""
    b = _make_bridge(monkeypatch)

    # No tracked processes
    monkeypatch.setattr(b, "_find_orphan_fio_pids", lambda: [7777, 8888])

    kill_calls = []

    def fake_kill(pid, sig):
        kill_calls.append((pid, sig))
        if sig == 0:
            return
    monkeypatch.setattr(os, "kill", fake_kill)

    killed = b.cleanup_fio_processes()
    assert 7777 in killed
    assert 8888 in killed


def test_cleanup_sweep_deduplicates_tracked_and_orphan(monkeypatch):
    """If an orphan PID matches a tracked PID, it should not be killed twice."""
    b = _make_bridge(monkeypatch)
    b.running_processes["x"] = FakePopen(pid=9999)

    kill_calls = []

    def fake_kill(pid, sig):
        kill_calls.append((pid, sig))
        if sig == 0:
            return
    monkeypatch.setattr(os, "kill", fake_kill)

    # Orphan fallback returns the same PID
    monkeypatch.setattr(b, "_find_orphan_fio_pids", lambda: [9999])

    killed = b.cleanup_fio_processes()
    # PID should appear only once
    assert killed.count(9999) == 1


# ---- _find_orphan_fio_pids ----

def test_find_orphan_excludes_tracked_pids(monkeypatch):
    """Orphan finder should exclude PIDs that are already tracked."""
    b = _make_bridge(monkeypatch)
    b.running_processes["z"] = FakePopen(pid=2222)

    ps_output = (
        "user  2222  0.0  fio --filename=/tmp/diskbench-test_1\n"
        "user  3333  0.0  fio --filename=/tmp/diskbench-test_2\n"
    )
    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = ps_output
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_result)

    orphans = b._find_orphan_fio_pids()
    assert 2222 not in orphans
    assert 3333 in orphans


def test_find_orphan_ignores_non_diskbench_fio(monkeypatch):
    """Lines with 'fio' but without diskbench markers should be ignored."""
    b = _make_bridge(monkeypatch)

    ps_output = "user  4444  0.0  fio --filename=/home/user/data\n"
    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = ps_output
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_result)

    orphans = b._find_orphan_fio_pids()
    assert orphans == []


# ---- _pid_alive ----

def test_pid_alive_true(monkeypatch):
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    assert bridge.DiskBenchBridge._pid_alive(12345) is True


def test_pid_alive_false_not_found(monkeypatch):
    def fake_kill(pid, sig):
        raise ProcessLookupError
    monkeypatch.setattr(os, "kill", fake_kill)
    assert bridge.DiskBenchBridge._pid_alive(12345) is False


def test_pid_alive_false_permission(monkeypatch):
    def fake_kill(pid, sig):
        raise PermissionError
    monkeypatch.setattr(os, "kill", fake_kill)
    assert bridge.DiskBenchBridge._pid_alive(12345) is False
