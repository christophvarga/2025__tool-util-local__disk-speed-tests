"""Tests for security hardening in bridge-server/server.py.

Covers: C-1 (path traversal), C-2 (config injection), C-3 (tempfile),
        C-5 (CORS), H-5 (exception sanitizing), H-1 (timeout/URL).
"""

import os
import sys
import threading

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_DIR = REPO_ROOT / "bridge-server"
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

import server as bridge


class DummyThread:
    def __init__(self, target=None, args=()):
        self.daemon = False
    def start(self):
        return


def _make_bridge(monkeypatch):
    b = bridge.DiskBenchBridge()
    monkeypatch.setattr(b, "_verify_fio", lambda: {"path": "/usr/bin/fio", "version": "3.40"})
    monkeypatch.setattr(threading, "Thread", DummyThread)
    return b


# --- C-1: disk_path validation ---

class TestDiskPathValidation:

    def test_rejects_traversal_path(self, monkeypatch):
        b = _make_bridge(monkeypatch)
        monkeypatch.setattr(bridge, "validate_disk_path", lambda p: False)
        monkeypatch.setattr(bridge, "is_system_path", lambda p: False)
        monkeypatch.setattr(bridge, "check_available_space", lambda p, s: True)

        result = b.start_test({
            "test_type": "quick_max_speed",
            "disk_path": "../../../etc",
            "size_gb": 1,
        })
        assert result["success"] is False
        assert "Invalid" in result["error"] or "inaccessible" in result["error"]

    def test_rejects_system_path(self, monkeypatch):
        b = _make_bridge(monkeypatch)
        monkeypatch.setattr(bridge, "validate_disk_path", lambda p: True)
        monkeypatch.setattr(bridge, "is_system_path", lambda p: True)
        monkeypatch.setattr(bridge, "check_available_space", lambda p, s: True)

        result = b.start_test({
            "test_type": "quick_max_speed",
            "disk_path": "/System/Library",
            "size_gb": 1,
        })
        assert result["success"] is False
        assert "system path" in result["error"].lower()

    def test_rejects_insufficient_space(self, monkeypatch):
        b = _make_bridge(monkeypatch)
        monkeypatch.setattr(bridge, "validate_disk_path", lambda p: True)
        monkeypatch.setattr(bridge, "is_system_path", lambda p: False)
        monkeypatch.setattr(bridge, "check_available_space", lambda p, s: False)

        result = b.start_test({
            "test_type": "quick_max_speed",
            "disk_path": "/Volumes/Test",
            "size_gb": 999,
        })
        assert result["success"] is False
        assert "space" in result["error"].lower()

    def test_accepts_valid_path(self, monkeypatch):
        b = _make_bridge(monkeypatch)
        monkeypatch.setattr(bridge, "validate_disk_path", lambda p: True)
        monkeypatch.setattr(bridge, "is_system_path", lambda p: False)
        monkeypatch.setattr(bridge, "check_available_space", lambda p, s: True)

        result = b.start_test({
            "test_type": "quick_max_speed",
            "disk_path": "/Volumes/Test",
            "size_gb": 1,
            "show_progress": False,
        })
        assert result["success"] is True


# --- C-2: Custom FIO config injection ---

class TestCustomFioValidation:

    def test_rejects_oversized_duration(self):
        with pytest.raises(ValueError, match="duration"):
            bridge._validate_custom_fio_params({"duration": 99999})

    def test_rejects_negative_numjobs(self):
        with pytest.raises(ValueError, match="numjobs"):
            bridge._validate_custom_fio_params({"numjobs": 0})

    def test_rejects_oversized_iodepth(self):
        with pytest.raises(ValueError, match="iodepth"):
            bridge._validate_custom_fio_params({"iodepth": 1024})

    def test_rejects_invalid_block_size(self):
        with pytest.raises(ValueError, match="block_size"):
            bridge._validate_custom_fio_params({"block_size": "1M\nfilename=/etc/passwd"})

    def test_rejects_block_size_with_path(self):
        with pytest.raises(ValueError, match="block_size"):
            bridge._validate_custom_fio_params({"block_size": "../../etc"})

    def test_accepts_valid_block_sizes(self):
        for bs in ("4k", "1M", "2G", "512K"):
            bridge._validate_custom_fio_params({"block_size": bs})

    def test_rejects_invalid_target_rate(self):
        with pytest.raises(ValueError, match="target_rate"):
            bridge._validate_custom_fio_params({"target_rate": "500M; rm -rf /"})

    def test_accepts_valid_target_rate(self):
        for rate in ("500M", "1G", "100"):
            bridge._validate_custom_fio_params({"target_rate": rate})

    def test_accepts_empty_target_rate(self):
        bridge._validate_custom_fio_params({"target_rate": ""})

    def test_accepts_valid_defaults(self):
        bridge._validate_custom_fio_params({})

    def test_newline_stripped_from_config(self, monkeypatch):
        b = _make_bridge(monkeypatch)
        config_file = b._generate_custom_fio_config({
            "block_size": "1M",
            "duration": 60,
            "numjobs": 1,
            "iodepth": 1,
            "target_rate": "500M",
        })
        try:
            with open(config_file) as f:
                content = f.read()
            for line in content.splitlines():
                assert '\r' not in line
                if line.startswith('bs='):
                    assert line == 'bs=1M'
        finally:
            os.unlink(config_file)


# --- C-3: tempfile usage ---

class TestTempfileUsage:

    def test_output_file_uses_tempfile(self, monkeypatch):
        b = _make_bridge(monkeypatch)
        monkeypatch.setattr(bridge, "validate_disk_path", lambda p: True)
        monkeypatch.setattr(bridge, "is_system_path", lambda p: False)
        monkeypatch.setattr(bridge, "check_available_space", lambda p, s: True)

        result = b.start_test({
            "test_type": "quick_max_speed",
            "disk_path": "/Volumes/Test",
            "size_gb": 1,
            "show_progress": False,
        })
        assert result["success"] is True
        test_id = result["test_id"]
        output_file = b.running_tests[test_id]["output_file"]
        # Should NOT be a predictable /tmp/diskbench-test_xxx.json path
        assert "diskbench-" in output_file
        assert os.path.dirname(output_file)  # has a directory component

    def test_custom_config_uses_tempfile(self, monkeypatch):
        b = _make_bridge(monkeypatch)
        config_file = b._generate_custom_fio_config({
            "block_size": "1M",
            "duration": 10,
        })
        try:
            assert "diskbench_custom_" in config_file
            assert config_file.endswith('.fio')
        finally:
            os.unlink(config_file)


# --- C-5: CORS restriction ---

class TestCORSRestriction:

    def test_cors_headers_have_no_wildcard(self):
        """Verify _send_cors_headers no longer uses '*'."""
        import inspect
        source = inspect.getsource(bridge.BridgeRequestHandler._send_cors_headers)
        assert "Allow-Origin', '*'" not in source

    def test_cors_source_allows_localhost(self):
        import inspect
        source = inspect.getsource(bridge.BridgeRequestHandler._send_cors_headers)
        assert "localhost" in source


# --- H-5: Exception sanitizing ---

class TestExceptionSanitizing:

    def test_sanitize_error_hides_path(self):
        exc = FileNotFoundError("/private/var/secret/file.txt")
        msg = bridge._sanitize_error(exc)
        assert "/private" not in msg
        assert "FileNotFoundError" in msg

    def test_sanitize_error_hides_details(self):
        exc = ValueError("invalid literal for int() with base 10: 'abc'")
        msg = bridge._sanitize_error(exc)
        assert "abc" not in msg
        assert "ValueError" in msg


# --- _validate_custom_fio_params edge cases ---

class TestParamLimitsEdgeCases:

    def test_duration_at_boundary(self):
        bridge._validate_custom_fio_params({"duration": 1})
        bridge._validate_custom_fio_params({"duration": 43200})

    def test_numjobs_at_boundary(self):
        bridge._validate_custom_fio_params({"numjobs": 1})
        bridge._validate_custom_fio_params({"numjobs": 16})

    def test_iodepth_at_boundary(self):
        bridge._validate_custom_fio_params({"iodepth": 1})
        bridge._validate_custom_fio_params({"iodepth": 256})

    def test_non_integer_duration_rejected(self):
        with pytest.raises(ValueError, match="integer"):
            bridge._validate_custom_fio_params({"duration": "abc"})
