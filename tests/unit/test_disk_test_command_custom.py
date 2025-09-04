import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure diskbench is importable
DISKBENCH_DIR = Path(__file__).resolve().parents[2] / "diskbench"
if str(DISKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(DISKBENCH_DIR))

from commands.test import DiskTestCommand


@pytest.fixture()
def cmd(monkeypatch):
    c = DiskTestCommand()

    # Spy on run_fio_test to capture processed config and directory
    calls = {}
    def fake_run_fio_test(cfg, test_dir, estimated_duration, progress_callback=None):
        calls['cfg'] = cfg
        calls['test_dir'] = test_dir
        return {
            "summary": {
                "total_read_iops": 1000.0,
                "total_write_iops": 800.0,
                "avg_read_latency": 0.5,
                "avg_write_latency": 0.7,
                "total_runtime": 1000
            }
        }
    monkeypatch.setattr(c.fio_runner, "run_fio_test", fake_run_fio_test)
    c._calls = calls
    return c


def test_custom_invalid_disk_path_returns_none(cmd, monkeypatch):
    import commands.test as cmd_mod
    monkeypatch.setattr(cmd_mod, "validate_disk_path", lambda p: False)

    # Create a temp config file to satisfy existence check
    with tempfile.NamedTemporaryFile(mode='w', delete=True) as tf:
        tf.write("[job]\nfilename=${DISK_PATH}/file\nsize=${TEST_SIZE}\n")
        tf.flush()
        res = cmd.execute_custom_test(
            disk_path="/Volumes/Bla",
            config_file=tf.name,
            test_size_gb=2,
            output_file="/tmp/out.json",
            show_progress=False,
            json_output=True
        )
        assert res is None


def test_custom_missing_config_returns_none(cmd, monkeypatch):
    import commands.test as cmd_mod
    monkeypatch.setattr(cmd_mod, "validate_disk_path", lambda p: True)

    # Non-existent file path
    res = cmd.execute_custom_test(
        disk_path="/Volumes/Test",
        config_file="/tmp/does-not-exist-xyz.fio",
        test_size_gb=2,
        output_file="/tmp/out.json",
        show_progress=False,
        json_output=True
    )
    assert res is None


def test_custom_success_placeholders_injected(cmd, monkeypatch):
    import commands.test as cmd_mod
    monkeypatch.setattr(cmd_mod, "validate_disk_path", lambda p: True)
    monkeypatch.setattr(cmd_mod, "check_available_space", lambda p, gb: True)

    cfg = (
        "[job]\n"
        "filename=${DISK_PATH}/data.bin\n"
        "size=${TEST_SIZE}\n"
        "size_mb=${TEST_SIZE_MB}\n"
        "size_kb=${TEST_SIZE_KB}\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
        tf.write(cfg)
        tf.flush()
        temp_path = tf.name

    try:
        disk = "/Volumes/Target"
        size_gb = 3
        res = cmd.execute_custom_test(
            disk_path=disk,
            config_file=temp_path,
            test_size_gb=size_gb,
            output_file="/tmp/out.json",
            show_progress=False,
            json_output=True
        )
        assert res is not None
        processed = cmd._calls['cfg']
        assert f"filename={disk}/data.bin" in processed
        assert f"size={size_gb}G" in processed
        assert f"size_mb={size_gb*1024}" in processed
        assert f"size_kb={size_gb*1024*1024}" in processed

        # Ensure test directory is on the volume for mounted paths
        assert cmd._calls['test_dir'].startswith(disk)
    finally:
        os.unlink(temp_path)

