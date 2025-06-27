"""
Validate command for diskbench helper binary.
"""

import logging
import subprocess
import os
import platform
from typing import Dict, Any, Optional

from utils.system_info import get_system_info, check_admin_privileges

logger = logging.getLogger(__name__)


class ValidateCommand:
    """Command to validate system and FIO installation."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def execute(self, json_output: bool = False) -> Optional[Dict[str, Any]]:
        """
        Execute the validate command.

        Args:
            json_output: Whether to format output as JSON

        Returns:
            Dict containing validation results or None on error
        """
        try:
            checks = {}

            # System checks
            checks['system_compatibility'] = self._check_system_compatibility()
            checks['python_version'] = self._check_python_version()
            checks['required_tools'] = self._check_required_tools()
            checks['fio_availability'] = self._check_fio_availability()
            checks['disk_access'] = self._check_disk_access()
            checks['permissions'] = self._check_permissions()
            checks['storage_space'] = self._check_storage_space()

            # Determine overall status
            overall_status = 'passed' if all(check['passed'] for check in checks.values()) else 'failed'

            result = {
                'overall_status': overall_status,
                'checks': checks,
                'timestamp': self._get_timestamp(),
                'system_info': get_system_info()
            }

            return result

        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            return None

    def _check_system_compatibility(self) -> Dict[str, Any]:
        """Check if the system is compatible."""
        try:
            system = platform.system()
            if system != 'Darwin':
                return {
                    'passed': False,
                    'message': f'Unsupported system: {system}. macOS required.',
                    'details': f'This tool is designed for macOS only. Detected: {system}'
                }

            # Check macOS version
            version = platform.mac_ver()[0]
            if version:
                major, minor = map(int, version.split('.')[:2])
                if major < 10 or (major == 10 and minor < 14):
                    return {
                        'passed': False,
                        'message': f'macOS {version} is too old. Requires 10.14+',
                        'details': 'This tool requires macOS 10.14 (Mojave) or later'
                    }

            return {
                'passed': True,
                'message': f'macOS {version} is compatible',
                'details': f'System: {system}, Version: {version}'
            }

        except Exception as e:
            return {
                'passed': False,
                'message': f'Failed to check system compatibility: {e}',
                'details': str(e)
            }

    def _check_python_version(self) -> Dict[str, Any]:
        """Check Python version compatibility."""
        try:
            import sys
            version = sys.version_info

            if version.major < 3 or (version.major == 3 and version.minor < 8):
                return {
                    'passed': False,
                    'message': f'Python {version.major}.{version.minor} is too old. Requires 3.8+',
                    'details': f'Current: {sys.version}'
                }

            return {
                'passed': True,
                'message': f'Python {version.major}.{version.minor}.{version.micro} is compatible',
                'details': f'Version: {sys.version}'
            }

        except Exception as e:
            return {
                'passed': False,
                'message': f'Failed to check Python version: {e}',
                'details': str(e)
            }

    def _check_required_tools(self) -> Dict[str, Any]:
        """Check for required system tools."""
        required_tools = [
            'diskutil',
            'system_profiler',
            'df',
            'vm_stat',
            'sysctl'
        ]

        missing_tools = []
        available_tools = []

        for tool in required_tools:
            try:
                result = subprocess.run(['which', tool],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    available_tools.append(tool)
                else:
                    missing_tools.append(tool)
            except Exception:
                missing_tools.append(tool)

        if missing_tools:
            return {
                'passed': False,
                'message': f'Missing required tools: {", ".join(missing_tools)}',
                'details': f'Available: {available_tools}, Missing: {missing_tools}'
            }

        return {
            'passed': True,
            'message': 'All required system tools are available',
            'details': f'Available tools: {", ".join(available_tools)}'
        }

    def _check_fio_availability(self) -> Dict[str, Any]:
        """Check FIO availability - Homebrew only."""
        try:
            # Check Homebrew FIO paths (Apple Silicon and Intel)
            homebrew_paths = [
                '/opt/homebrew/bin/fio',  # Apple Silicon Homebrew
                '/usr/local/bin/fio',     # Intel Homebrew
            ]

            for fio_path in homebrew_paths:
                if os.path.exists(fio_path) and os.access(fio_path, os.X_OK):
                    try:
                        result = subprocess.run([fio_path, '--version'],
                                                capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            version = result.stdout.strip().split('\n')[0]
                            # NOTE: Do NOT run FIO tests here - that causes sandbox issues
                            # FIO execution only happens from unsandboxed bridge server
                            return {
                                'passed': True,
                                'message': f'Homebrew FIO available: {version}',
                                'details': f'Path: {fio_path}, Version: {version}, Status: Binary found (execution will be tested in bridge server)'}
                    except Exception as e:
                        continue

            # Check system PATH FIO (backup for other installations)
            try:
                result = subprocess.run(['which', 'fio'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    fio_path = result.stdout.strip()
                    # Only accept if it's not already checked above
                    if fio_path not in homebrew_paths:
                        version_result = subprocess.run([fio_path, '--version'],
                                                        capture_output=True, text=True, timeout=10)
                        if version_result.returncode == 0:
                            version = version_result.stdout.strip().split('\n')[0]
                            return {
                                'passed': True,
                                'message': f'System FIO available: {version}',
                                'details': f'Path: {fio_path}, Version: {version}'
                            }
            except Exception:
                pass

            return {
                'passed': False,
                'message': 'FIO not found. Install with: brew install fio',
                'details': 'Homebrew FIO not detected. Run: brew install fio'
            }

        except Exception as e:
            return {
                'passed': False,
                'message': f'Failed to check FIO availability: {e}',
                'details': str(e)
            }

    def _check_disk_access(self) -> Dict[str, Any]:
        """Check disk access capabilities."""
        try:
            # Test basic disk listing
            result = subprocess.run(['diskutil', 'list'],
                                    capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                return {
                    'passed': False,
                    'message': 'Cannot list disks with diskutil',
                    'details': f'diskutil list failed: {result.stderr}'
                }

            # Test system_profiler access
            result = subprocess.run(['system_profiler', 'SPStorageDataType'],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {
                    'passed': False,
                    'message': 'Cannot access storage information',
                    'details': f'system_profiler failed: {result.stderr}'
                }

            return {
                'passed': True,
                'message': 'Disk access is working',
                'details': 'Can list disks and access storage information'
            }

        except Exception as e:
            return {
                'passed': False,
                'message': f'Failed to check disk access: {e}',
                'details': str(e)
            }

    def _check_permissions(self) -> Dict[str, Any]:
        """Check permission requirements."""
        try:
            is_admin = check_admin_privileges()

            # Check write access to common test locations
            test_locations = ['/tmp', os.path.expanduser('~/Desktop')]
            writable_locations = []

            for location in test_locations:
                if os.path.exists(location) and os.access(location, os.W_OK):
                    writable_locations.append(location)

            if not writable_locations:
                return {
                    'passed': False,
                    'message': 'No writable test locations found',
                    'details': f'Tested locations: {test_locations}'
                }

            details = f'Admin: {is_admin}, Writable locations: {writable_locations}'

            if is_admin:
                message = 'Running with administrator privileges'
            else:
                message = 'Running with user privileges (admin needed for raw device access)'

            return {
                'passed': True,
                'message': message,
                'details': details
            }

        except Exception as e:
            return {
                'passed': False,
                'message': f'Failed to check permissions: {e}',
                'details': str(e)
            }

    def _check_storage_space(self) -> Dict[str, Any]:
        """Check available storage space."""
        try:
            # Check space in /tmp
            tmp_stat = os.statvfs('/tmp')
            tmp_available = tmp_stat.f_bavail * tmp_stat.f_frsize
            tmp_gb = tmp_available / (1024 ** 3)

            # Check space in home directory
            home = os.path.expanduser('~')
            home_stat = os.statvfs(home)
            home_available = home_stat.f_bavail * home_stat.f_frsize
            home_gb = home_available / (1024 ** 3)

            min_required_gb = 1.0  # Minimum 1GB for testing

            if tmp_gb < min_required_gb and home_gb < min_required_gb:
                return {
                    'passed': False,
                    'message': f'Insufficient storage space (need {min_required_gb}GB)',
                    'details': f'/tmp: {tmp_gb:.1f}GB, Home: {home_gb:.1f}GB'
                }

            return {
                'passed': True,
                'message': 'Sufficient storage space available',
                'details': f'/tmp: {tmp_gb:.1f}GB, Home: {home_gb:.1f}GB'
            }

        except Exception as e:
            return {
                'passed': False,
                'message': f'Failed to check storage space: {e}',
                'details': str(e)
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
