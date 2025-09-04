import os
import types
from pathlib import Path

import pytest

from diskbench.core.fio_runner import FioRunner
from diskbench.commands.validate import ValidateCommand


def _fake_machine_arm64():
    return 'arm64'


def test_vendor_fio_precedence(monkeypatch):
    # Arrange: simulate vendored fio exists and is executable
    repo_root = Path(__file__).resolve().parents[2]
    vendor_fio = repo_root / 'vendor' / 'fio' / 'macos' / 'arm64' / 'fio'

    def fake_exists(path):
        path = str(path)
        if path == str(vendor_fio):
            return True
        # Default to False for all others to ensure vendor is chosen
        return False

    def fake_access(path, mode):
        if str(path) == str(vendor_fio):
            return True
        return False

    monkeypatch.setattr('platform.machine', _fake_machine_arm64)
    monkeypatch.setattr(os.path, 'exists', fake_exists)
    monkeypatch.setattr(os, 'access', fake_access)

    # Act
    runner = FioRunner()

    # Assert
    assert runner.fio_path == str(vendor_fio)


def test_validate_accepts_vendor(monkeypatch):
    # Arrange
    repo_root = Path(__file__).resolve().parents[2]
    vendor_fio = repo_root / 'vendor' / 'fio' / 'macos' / 'arm64' / 'fio'

    def fake_exists(path):
        path = str(path)
        if path == str(vendor_fio):
            return True
        return False

    def fake_access(path, mode):
        if str(path) == str(vendor_fio):
            return True
        return False

    class FakeCompleted:
        def __init__(self):
            self.returncode = 0
            self.stdout = 'fio-3.36\n'
            self.stderr = ''

    def fake_run(args, capture_output=False, text=False, timeout=0, **kwargs):
        # Simulate `vendor fio --version` working
        if isinstance(args, (list, tuple)) and len(args) >= 2:
            if args[0] == str(vendor_fio) and args[1] == '--version':
                return FakeCompleted()
        # Default: command not found
        class Fail:
            returncode = 1
            stdout = ''
            stderr = 'not found'
        return Fail()

    monkeypatch.setattr('platform.machine', _fake_machine_arm64)
    monkeypatch.setattr(os.path, 'exists', fake_exists)
    monkeypatch.setattr(os, 'access', fake_access)
    monkeypatch.setattr('subprocess.run', fake_run)

    # Act
    result = ValidateCommand()._check_fio_availability()

    # Assert
    assert result['passed'] is True
    assert 'Vendored FIO available' in result['message']

