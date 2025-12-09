import json
from types import SimpleNamespace

from diskbench.utils import system_info


def test_parse_size_fallback_variants():
    assert system_info._parse_size_fallback('1T') == 1024 ** 4
    assert system_info._parse_size_fallback('1.5G') == int(1.5 * (1024 ** 3))
    assert system_info._parse_size_fallback('256M') == 256 * (1024 ** 2)
    assert system_info._parse_size_fallback('4096K') == 4096 * 1024
    assert system_info._parse_size_fallback('1024') == 1024
    assert system_info._parse_size_fallback('invalid') == 0


def test_get_disk_info_fallback_parses_df(monkeypatch):
    df_output = (
        "Filesystem   Size   Used  Avail Capacity Mounted\n"
        "/dev/disk2s1  500G   50G   450G    10% /Volumes/Media\n"
        "map auto_home     0B    0B     0B   100% /System/Volumes/Data\n"
    )

    def fake_run(cmd, capture_output, text, timeout):
        assert cmd == ['df', '-h']
        return SimpleNamespace(returncode=0, stdout=df_output)

    monkeypatch.setattr(system_info.subprocess, 'run', fake_run)

    result = system_info._get_disk_info_fallback()

    assert result['error'] is None
    assert len(result['disks']) == 1
    disk = result['disks'][0]
    assert disk['name'] == 'Media'
    assert disk['mount_point'] == '/Volumes/Media'
    assert disk['suitable_for_testing'] is True
    assert disk['free_space_bytes'] == int(450 * (1024 ** 3))


def test_get_disk_info_success(monkeypatch):
    storage_payload = {'SPStorageDataType': [{
        '_name': 'Main Disk',
        'size_in_bytes': 512 * (1024 ** 3),
        'free_space_in_bytes': 256 * (1024 ** 3),
        'mount_point': '/Volumes/Main',
        'file_system': 'APFS',
        'writable': True,
        'removable_media': False,
    }]}

    def fake_run(cmd, capture_output, text, timeout):
        assert cmd == ['system_profiler', 'SPStorageDataType', '-json']
        return SimpleNamespace(returncode=0, stdout=json.dumps(storage_payload))

    monkeypatch.setattr(system_info.subprocess, 'run', fake_run)

    result = system_info.get_disk_info()

    assert result['error'] is None
    assert len(result['disks']) == 1
    disk = result['disks'][0]
    assert disk['name'] == 'Main Disk'
    assert disk['file_system'] == 'APFS'


def test_get_disk_info_fallback_on_timeout(monkeypatch):
    fallback_data = {'disks': [{'name': 'Fallback Disk', 'mount_point': '/Volumes/Fallback'}], 'error': None}

    def fake_run(cmd, capture_output, text, timeout):
        raise system_info.subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(system_info.subprocess, 'run', fake_run)
    monkeypatch.setattr(system_info, '_get_disk_info_fallback', lambda: fallback_data)

    result = system_info.get_disk_info()

    assert result['disks'] == fallback_data['disks']
    assert result['error'] is not None
    assert 'system_profiler failed' in result['error']


def test_get_system_info_macos(monkeypatch):
    hardware_payload = {
        'SPHardwareDataType': [{
            'machine_name': 'MacBook Pro',
            'machine_model': 'Mac15,1',
            'cpu_type': 'Apple M4',
            'current_processor_speed': '3.4 GHz',
            'number_processors': 1,
            'packages': 8,
            'physical_memory': '32 GB',
            'serial_number': 'ABC123'
        }]
    }

    def fake_run(cmd, capture_output, text, timeout):
        if cmd == ['sw_vers']:
            return SimpleNamespace(
                returncode=0,
                stdout='ProductName: macOS\nProductVersion: 14.5\nBuildVersion: 23G80\n'
            )
        if cmd == ['system_profiler', 'SPHardwareDataType', '-json']:
            return SimpleNamespace(returncode=0, stdout=json.dumps(hardware_payload))
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(system_info.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(system_info.platform, 'version', lambda: 'test-version')
    monkeypatch.setattr(system_info.platform, 'release', lambda: 'test-release')
    monkeypatch.setattr(system_info.platform, 'machine', lambda: 'arm64')
    monkeypatch.setattr(system_info.platform, 'processor', lambda: 'Apple M4')
    monkeypatch.setattr(system_info.platform, 'python_version', lambda: '3.12.2')
    monkeypatch.setattr(system_info.platform, 'node', lambda: 'test-host')

    monkeypatch.setattr(system_info.subprocess, 'run', fake_run)

    info = system_info.get_system_info()

    assert info['platform'] == 'Darwin'
    assert info['platform_version'] == 'test-version'
    assert info['macos_info']['ProductVersion'] == '14.5'
    assert info['hardware_info']['model_name'] == 'MacBook Pro'
