"""
List disks command for diskbench helper binary.
"""

import logging
import subprocess
import json
import os
from typing import Dict, Any, List, Optional

from diskbench.utils.system_info import get_disk_info

logger = logging.getLogger(__name__)


class ListDisksCommand:
    """Command to list available disks for testing."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def execute(self, json_output: bool = False) -> Optional[Dict[str, Any]]:
        """
        Execute the list disks command.

        Args:
            json_output: Whether to format output as JSON

        Returns:
            Dict containing disk information or None on error
        """
        try:
            # Get basic disk info from system_profiler
            disk_info = get_disk_info()

            if disk_info.get('error'):
                self.logger.error(f"Failed to get disk info: {disk_info['error']}")
                return None

            # Enhance disk information with additional details
            enhanced_disks = []
            for disk in disk_info.get('disks', []):
                enhanced_disk = self._enhance_disk_info(disk)
                if enhanced_disk:
                    enhanced_disks.append(enhanced_disk)

            # NOTE: Raw devices removed for QLab testing - we only test filesystem performance
            # QLab reads files from mounted volumes, not raw devices

            # Sort disks by type and name - prioritize mounted volumes
            enhanced_disks.sort(key=lambda x: (x.get('type', 'unknown'), x.get('name', '')))

            result = {
                'disks': enhanced_disks,
                'count': len(enhanced_disks),
                'timestamp': self._get_timestamp(),
                'note': 'Showing mounted filesystems only - tests realistic QLab performance'
            }

            return result

        except Exception as e:
            self.logger.error(f"Error listing disks: {e}")
            return None

    def _enhance_disk_info(self, disk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enhance disk information with additional details.

        Args:
            disk: Basic disk information

        Returns:
            Enhanced disk information or None if invalid
        """
        try:
            mount_point = disk.get('mount_point', '')
            if not mount_point:
                return None

            # Get device path from mount point
            device_path = self._get_device_path(mount_point)

            enhanced = {
                'name': disk.get('name', 'Unknown'),
                'device': device_path or mount_point,
                'mount_point': mount_point,
                'size': self._format_size(disk.get('size', 0)),
                'size_bytes': disk.get('size', 0),
                'free_space': self._format_size(disk.get('free_space', 0)),
                'free_space_bytes': disk.get('free_space', 0),
                'file_system': disk.get('file_system', 'Unknown'),
                'type': self._determine_disk_type(disk),
                'writable': disk.get('writable', False),
                'removable': disk.get('removable', False),
                'suitable_for_testing': self._is_suitable_for_testing(disk)
            }

            return enhanced

        except Exception as e:
            self.logger.warning(f"Failed to enhance disk info: {e}")
            return None

    def _get_raw_devices(self) -> List[Dict[str, Any]]:
        """
        Get raw device information from /dev/disk*, filtering to main disks only.

        Returns:
            List of raw device information for main physical disks
        """
        raw_devices = []

        try:
            # Only get main disk devices (disk0, disk1, disk2, etc.) - no partitions
            dev_path = '/dev'
            if os.path.exists(dev_path):
                for item in os.listdir(dev_path):
                    # Only include main disk devices (disk0, disk1, etc.) - no partitions (disk0s1, disk0s2, etc.)
                    if item.startswith('disk') and 's' not in item and item[4:].isdigit():
                        device_path = os.path.join(dev_path, item)
                        if os.path.exists(device_path):
                            device_info = self._get_raw_device_info(device_path)
                            if device_info and device_info['size_bytes'] > 1024 * 1024 * 1024:  # Only disks > 1GB
                                raw_devices.append(device_info)

        except Exception as e:
            self.logger.warning(f"Failed to get raw devices: {e}")

        return raw_devices

    def _get_raw_device_info(self, device_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a raw device.

        Args:
            device_path: Path to the raw device

        Returns:
            Device information or None if unavailable
        """
        try:
            # Get device size using diskutil
            result = subprocess.run(['diskutil', 'info', device_path],
                                    capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return None

            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()

            # Extract relevant information
            device_info = {
                'name': info.get('Device / Media Name', os.path.basename(device_path)),
                'device': device_path,
                'mount_point': '',
                'size': info.get('Disk Size', '0 B'),
                'size_bytes': self._parse_size(info.get('Disk Size', '0 B')),
                'free_space': 'N/A (Raw Device)',
                'free_space_bytes': 0,
                'file_system': 'Raw Device',
                'type': self._determine_device_type(info),
                'writable': True,  # Assume raw devices are writable
                'removable': info.get('Removable Media', 'No') == 'Yes',
                'suitable_for_testing': True
            }

            return device_info

        except Exception as e:
            self.logger.warning(f"Failed to get raw device info for {device_path}: {e}")
            return None

    def _get_device_path(self, mount_point: str) -> Optional[str]:
        """
        Get device path from mount point.

        Args:
            mount_point: Mount point path

        Returns:
            Device path or None if not found
        """
        try:
            result = subprocess.run(['df', mount_point],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    device = lines[1].split()[0]
                    return device
        except Exception as e:
            self.logger.warning(f"Failed to get device path for {mount_point}: {e}")

        return None

    def _determine_disk_type(self, disk: Dict[str, Any]) -> str:
        """
        Determine disk type (SSD, HDD, etc.).

        Args:
            disk: Disk information

        Returns:
            Disk type string
        """
        name = disk.get('name', '').lower()
        mount_point = disk.get('mount_point', '')

        # Check for common SSD indicators
        if any(indicator in name for indicator in ['ssd', 'flash', 'nvme']):
            return 'SSD'

        # Check for external/removable indicators
        if disk.get('removable', False) or '/Volumes/' in mount_point:
            return 'External'

        # Check for network mounts
        if mount_point.startswith('/Network/') or 'afp' in name or 'smb' in name:
            return 'Network'

        # Default to HDD for internal drives
        if mount_point in ['/', '/System/Volumes/Data']:
            return 'SSD'  # Modern Macs typically have SSDs as boot drives

        return 'HDD'

    def _determine_device_type(self, info: Dict[str, str]) -> str:
        """
        Determine device type from diskutil info.

        Args:
            info: diskutil info output

        Returns:
            Device type string
        """
        media_type = info.get('Media Type', '').lower()
        device_name = info.get('Device / Media Name', '').lower()

        if 'ssd' in media_type or 'ssd' in device_name or 'flash' in media_type:
            return 'SSD'
        elif 'external' in info.get('Device Location', '').lower():
            return 'External'
        else:
            return 'HDD'

    def _is_suitable_for_testing(self, disk: Dict[str, Any]) -> bool:
        """
        Determine if disk is suitable for testing.

        Args:
            disk: Disk information

        Returns:
            True if suitable for testing
        """
        # Must be writable
        if not disk.get('writable', False):
            return False

        # Must have sufficient free space (at least 1GB)
        free_space = disk.get('free_space', 0)
        if free_space < 1024 * 1024 * 1024:  # 1GB
            return False

        # Avoid system-critical mounts
        mount_point = disk.get('mount_point', '')
        if mount_point in ['/System', '/usr', '/bin', '/sbin']:
            return False

        return True

    def _format_size(self, size_bytes: int) -> str:
        """
        Format size in bytes to human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"

    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string to bytes.

        Args:
            size_str: Size string (e.g., "500.1 GB")

        Returns:
            Size in bytes
        """
        try:
            # Extract number and unit
            parts = size_str.strip().split()
            if len(parts) < 2:
                return 0

            size = float(parts[0])
            unit = parts[1].upper()

            multipliers = {
                'B': 1,
                'KB': 1024,
                'MB': 1024 ** 2,
                'GB': 1024 ** 3,
                'TB': 1024 ** 4
            }

            return int(size * multipliers.get(unit, 1))

        except (ValueError, IndexError):
            return 0

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
