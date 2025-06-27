"""
Security utilities for diskbench helper binary.
Provides input validation and sanitization functions.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Union, List


def validate_disk_path(disk_path: str) -> bool:
    """
    Validate that a disk path is safe and accessible.

    Args:
        disk_path: Path to validate (e.g., /dev/disk1s1 or /Volumes/MyDisk)

    Returns:
        bool: True if path is valid and accessible
    """
    if not disk_path or not isinstance(disk_path, str):
        return False

    # Normalize path
    disk_path = os.path.abspath(disk_path)

    # Check for path traversal attempts
    if '..' in disk_path or disk_path.startswith('~'):
        return False

    # Allow /dev/disk* paths (raw devices)
    if disk_path.startswith('/dev/disk'):
        # Validate format: /dev/disk[0-9]+s?[0-9]*
        if re.match(r'^/dev/disk\d+s?\d*$', disk_path):
            return os.path.exists(disk_path)
        return False

    # Allow /Volumes/* paths (mounted volumes)
    if disk_path.startswith('/Volumes/'):
        return os.path.exists(disk_path) and os.path.ismount(disk_path)

    # Allow other mounted filesystems that exist
    if os.path.exists(disk_path):
        # Check if it's a mount point or a directory on a mounted filesystem
        return os.path.ismount(disk_path) or os.path.isdir(disk_path)

    return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        str: Sanitized filename
    """
    if not filename or not isinstance(filename, str):
        return "output"

    # Remove path components
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Ensure it's not empty
    if not filename:
        filename = "output"

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename


def validate_fio_parameters(fio_args: List[str]) -> List[str]:
    """
    Validate and filter FIO parameters to remove dangerous options.

    Args:
        fio_args: List of FIO command-line arguments

    Returns:
        List[str]: Filtered list of safe arguments
    """
    if not fio_args or not isinstance(fio_args, list):
        return []

    # Dangerous FIO options that should be blocked
    dangerous_options = {
        '--exec-prerun', '--exec-postrun',  # Command execution
        '--external',                        # External programs
        '--server',                         # Network server mode
        '--client',                         # Network client mode
        '--remote',                         # Remote execution
        '--trigger',                        # Trigger commands
        '--trigger-file',                   # Trigger file commands
    }

    # Dangerous patterns
    dangerous_patterns = [
        r'--exec.*=.*',                     # Any exec parameter
        r'--.*script.*=.*',                 # Script execution
        r'--.*command.*=.*',                # Command execution
    ]

    filtered_args = []

    for arg in fio_args:
        if not isinstance(arg, str):
            continue

        # Check against dangerous options
        if any(arg.startswith(opt) for opt in dangerous_options):
            continue

        # Check against dangerous patterns
        if any(re.match(pattern, arg, re.IGNORECASE) for pattern in dangerous_patterns):
            continue

        # Check for shell injection attempts
        if any(char in arg for char in ['`', '$', '|', '&', ';', '>', '<']):
            continue

        filtered_args.append(arg)

    return filtered_args


def validate_file_path(file_path: str, must_exist: bool = False, must_be_writable: bool = False) -> bool:
    """
    Validate a file path for safety and accessibility.

    Args:
        file_path: Path to validate
        must_exist: Whether the file must already exist
        must_be_writable: Whether the file/directory must be writable

    Returns:
        bool: True if path is valid
    """
    if not file_path or not isinstance(file_path, str):
        return False

    # Normalize path
    file_path = os.path.abspath(file_path)

    # Check for path traversal
    if '..' in file_path or file_path.startswith('~'):
        return False

    # Check existence requirement
    if must_exist and not os.path.exists(file_path):
        return False

    # Check write permission
    if must_be_writable:
        if os.path.exists(file_path):
            return os.access(file_path, os.W_OK)
        else:
            # Check if parent directory is writable
            parent_dir = os.path.dirname(file_path)
            return os.path.exists(parent_dir) and os.access(parent_dir, os.W_OK)

    return True


def get_safe_test_directory(base_path: str, test_name: str) -> str:
    """
    Generate a safe test directory path.

    Args:
        base_path: Base directory path
        test_name: Name of the test

    Returns:
        str: Safe test directory path
    """
    # Sanitize test name
    safe_test_name = sanitize_filename(test_name)

    # Create safe directory name with timestamp
    import time
    timestamp = int(time.time())
    dir_name = f"diskbench_{safe_test_name}_{timestamp}"

    # Combine with base path
    test_dir = os.path.join(base_path, dir_name)

    return os.path.abspath(test_dir)


def check_available_space(path: str, required_gb: float) -> bool:
    """
    Check if there's enough available space at the given path.

    Args:
        path: Path to check
        required_gb: Required space in GB

    Returns:
        bool: True if enough space is available
    """
    try:
        # For raw devices (/dev/disk*), skip space check as FIO will handle this
        if path.startswith('/dev/disk'):
            return True

        if not os.path.exists(path):
            path = os.path.dirname(path)

        stat = os.statvfs(path)
        available_bytes = stat.f_bavail * stat.f_frsize
        required_bytes = required_gb * 1024 * 1024 * 1024

        return available_bytes >= required_bytes
    except (OSError, AttributeError):
        # If we can't check space, let FIO handle it
        return True


def is_system_path(path: str) -> bool:
    """
    Check if a path is a critical system path that should not be modified.

    Args:
        path: Path to check

    Returns:
        bool: True if path is a system path
    """
    path = os.path.abspath(path)

    system_paths = [
        '/System',
        '/usr/bin',
        '/usr/sbin',
        '/bin',
        '/sbin',
        '/etc',
        '/var/log',
        '/Library/System',
        '/private/etc',
        '/private/var/log'
    ]

    return any(path.startswith(sys_path) for sys_path in system_paths)
