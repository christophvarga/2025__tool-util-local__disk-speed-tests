import sys
import types
import pytest
from pathlib import Path

# Ensure diskbench package is importable
TEST_DIR = Path(__file__).resolve().parent
# tests/unit -> parent is tests; parent of that is repo root
DISKBENCH_DIR = TEST_DIR.parents[1] / "diskbench"
if str(DISKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(DISKBENCH_DIR))

from commands.test import DiskTestCommand


@pytest.fixture()
def cmd(monkeypatch):
    """Provide a DiskTestCommand with heavy dependencies mocked."""
    c = DiskTestCommand()

    # Mock out FioRunner.run_fio_test to avoid real execution
    class DummyFioRunner:
        def run_fio_test(self, cfg, test_dir, estimated_duration, progress_callback=None):
            # Return minimal plausible FIO-like structure
            return {
                "summary": {
                    "total_read_iops": 1000.0,
                    "total_write_iops": 800.0,
                    "avg_read_latency": 0.5,
                    "avg_write_latency": 0.7,
                    "total_runtime": 1000
                }
            }
        def stop_fio_test(self):
            return {"stopped": True}

    monkeypatch.setattr(c, "fio_runner", DummyFioRunner())

    # Mock get_system_info to deterministic value
    from utils import system_info as si
    monkeypatch.setattr(si, "get_system_info", lambda: {"os": "macOS", "arch": "arm64"})

    # Provide a minimal qlab pattern
    class DummyQLabPatterns:
        def get_test_config(self, test_mode, disk_path, size_gb):
            return {
                "name": f"Test {test_mode}",
                "description": "desc",
                "duration": 60,
                "fio_config": "[job]\nfilename=/tmp/file\nsize=1G\nrw=read\n"
            }
        def analyze_results(self, test_mode, fio_results):
            return {"overall_performance": "good"}

    monkeypatch.setattr(c, "qlab_patterns", DummyQLabPatterns())

    return c


def test_execute_builtin_invalid_disk_path_returns_none(cmd, monkeypatch):
    # Mock validation functions
    import commands.test as cmd_mod
    monkeypatch.setattr(cmd_mod, "validate_disk_path", lambda p: False)

    res = cmd.execute_builtin_test(
        disk_path="/Volumes/Invalid",
        test_mode="quick_max_speed",
        test_size_gb=10,
        output_file="/tmp/out.json",
        show_progress=False,
        json_output=True
    )
    assert res is None


def test_execute_builtin_insufficient_space_returns_none(cmd, monkeypatch):
    import commands.test as cmd_mod
    monkeypatch.setattr(cmd_mod, "validate_disk_path", lambda p: True)
    monkeypatch.setattr(cmd_mod, "check_available_space", lambda p, gb: False)

    res = cmd.execute_builtin_test(
        disk_path="/Volumes/Test",
        test_mode="quick_max_speed",
        test_size_gb=10,
        output_file="/tmp/out.json",
        show_progress=False,
        json_output=True
    )
    assert res is None


def test_execute_builtin_deprecated_mapping_and_success(cmd, monkeypatch):
    # Valid path and enough space
    import commands.test as cmd_mod
    monkeypatch.setattr(cmd_mod, "validate_disk_path", lambda p: True)
    monkeypatch.setattr(cmd_mod, "check_available_space", lambda p, gb: True)

    # Spy on qlab_patterns.get_test_config to inspect called test_mode
    called = {}
    orig_get = cmd.qlab_patterns.get_test_config
    def spy_get_test_config(test_mode, disk_path, size_gb):
        called['test_mode'] = test_mode
        return orig_get(test_mode, disk_path, size_gb)
    monkeypatch.setattr(cmd.qlab_patterns, "get_test_config", spy_get_test_config)

    res = cmd.execute_builtin_test(
        disk_path="/Volumes/Test",
        test_mode="quick_max_speed",  # deprecated
        test_size_gb=5,
        output_file="/tmp/out.json",
        show_progress=False,
        json_output=True
    )

    assert res is not None
    # Mapping quick_max_speed -> quick_max_mix should have occurred
    assert called.get('test_mode') == 'quick_max_mix'

    # Verify result metadata flags original mode
    info = res.get('test_info', {})
    assert info.get('test_mode') == 'quick_max_mix'
    assert info.get('original_test_mode') == 'quick_max_speed'
    assert info.get('deprecated_mapping') is True

    # Minimal invariants in result
    assert 'system_info' in res
    assert 'fio_results' in res
    assert 'qlab_analysis' in res

