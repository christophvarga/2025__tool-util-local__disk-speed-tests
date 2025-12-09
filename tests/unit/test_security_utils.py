import os
from types import SimpleNamespace

import pytest

from diskbench.utils import security


def test_validate_disk_path_rejects_traversal():
    assert security.validate_disk_path('../etc/passwd') is False
    assert security.validate_disk_path('~/disk') is False


def test_validate_disk_path_accepts_dev_disk(monkeypatch):
    path = '/dev/disk9s1'
    original_exists = os.path.exists

    def fake_exists(candidate):
        if candidate == path:
            return True
        return original_exists(candidate)

    monkeypatch.setattr(os.path, 'exists', fake_exists)
    assert security.validate_disk_path(path) is True


def test_validate_disk_path_accepts_volume(monkeypatch):
    path = '/Volumes/TestVolume'
    original_exists = os.path.exists
    original_ismount = os.path.ismount

    def fake_exists(candidate):
        if candidate == path:
            return True
        return original_exists(candidate)

    def fake_ismount(candidate):
        if candidate == path:
            return True
        return original_ismount(candidate)

    monkeypatch.setattr(os.path, 'exists', fake_exists)
    monkeypatch.setattr(os.path, 'ismount', fake_ismount)

    assert security.validate_disk_path(path) is True


@pytest.mark.parametrize(
    'unsafe,expected',
    [
        ('results.json', 'results.json'),
        ('../weird\\name?:.json', 'weird_name__.json'),
        ('   ', 'output'),
        ('a'*300 + '.json', 'a'*250 + '.json'),
    ],
)
def test_sanitize_filename_outputs_safe_names(unsafe, expected):
    assert security.sanitize_filename(unsafe) == expected


def test_validate_fio_parameters_filters_dangerous():
    args = [
        '--name=test',
        '--exec-prerun=rm -rf /',
        '--rw=read',
        '--trigger=/tmp/script.sh',
        '--iodepth=32',
        '--client=malicious',
        '--size=1G',
        '--output=/tmp/out',
        '--write_iops_log=foo',
        '--script=bad',
    ]

    filtered = security.validate_fio_parameters(args)

    assert '--name=test' in filtered
    assert '--rw=read' in filtered
    assert '--iodepth=32' in filtered
    assert '--size=1G' in filtered
    assert '--output=/tmp/out' in filtered
    # Dangerous options removed
    assert '--exec-prerun=rm -rf /' not in filtered
    assert '--trigger=/tmp/script.sh' not in filtered
    assert '--client=malicious' not in filtered
    assert '--script=bad' not in filtered


def test_validate_file_path_writable(tmp_path):
    target = tmp_path / 'result.json'
    assert security.validate_file_path(str(target), must_exist=False, must_be_writable=True) is True
    target.write_text('data')
    assert security.validate_file_path(str(target), must_exist=True, must_be_writable=True) is True


def test_get_safe_test_directory_generates_unique_path(tmp_path):
    result = security.get_safe_test_directory(str(tmp_path), 'My Test/Pattern')
    assert result.startswith(str(tmp_path))
    basename = os.path.basename(result)
    assert basename.startswith('diskbench_Pattern_')


def test_check_available_space_respects_statvfs(monkeypatch, tmp_path):
    def fake_statvfs(_):
        return SimpleNamespace(f_bavail=1000, f_frsize=1024)

    monkeypatch.setattr(os, 'statvfs', fake_statvfs)
    assert security.check_available_space(str(tmp_path), required_gb=1) is False


def test_check_available_space_dev_disk_short_circuits():
    assert security.check_available_space('/dev/disk1', required_gb=500) is True


def test_is_system_path_detection(tmp_path):
    assert security.is_system_path('/System/Library') is True
    assert security.is_system_path(str(tmp_path)) is False
