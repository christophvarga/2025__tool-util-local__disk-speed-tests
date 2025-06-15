"""
System information utilities for diskbench helper binary.
"""

import os
import platform
import subprocess
import json
from typing import Dict, Any

def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.
    
    Returns:
        Dict containing system information
    """
    info = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'platform_release': platform.release(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }
    
    # macOS specific information
    if platform.system() == 'Darwin':
        try:
            # Get macOS version
            result = subprocess.run(['sw_vers'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                sw_vers_info = {}
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        sw_vers_info[key.strip()] = value.strip()
                info['macos_info'] = sw_vers_info
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
        
        try:
            # Get hardware information
            result = subprocess.run(['system_profiler', 'SPHardwareDataType', '-json'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                hardware_data = json.loads(result.stdout)
                if 'SPHardwareDataType' in hardware_data:
                    hardware_info = hardware_data['SPHardwareDataType'][0]
                    info['hardware_info'] = {
                        'model_name': hardware_info.get('machine_name', 'Unknown'),
                        'model_identifier': hardware_info.get('machine_model', 'Unknown'),
                        'processor_name': hardware_info.get('cpu_type', 'Unknown'),
                        'processor_speed': hardware_info.get('current_processor_speed', 'Unknown'),
                        'number_of_processors': hardware_info.get('number_processors', 'Unknown'),
                        'total_number_of_cores': hardware_info.get('packages', 'Unknown'),
                        'memory': hardware_info.get('physical_memory', 'Unknown'),
                        'serial_number': hardware_info.get('serial_number', 'Unknown')
                    }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            pass
    
    return info

def get_disk_info() -> Dict[str, Any]:
    """
    Get disk information using system_profiler.
    
    Returns:
        Dict containing disk information
    """
    disk_info = {
        'disks': [],
        'error': None
    }
    
    try:
        # Get storage information
        result = subprocess.run(['system_profiler', 'SPStorageDataType', '-json'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            storage_data = json.loads(result.stdout)
            if 'SPStorageDataType' in storage_data:
                for storage in storage_data['SPStorageDataType']:
                    disk_info['disks'].append({
                        'name': storage.get('_name', 'Unknown'),
                        'size': storage.get('size_in_bytes', 0),
                        'free_space': storage.get('free_space_in_bytes', 0),
                        'mount_point': storage.get('mount_point', ''),
                        'file_system': storage.get('file_system', 'Unknown'),
                        'writable': storage.get('writable', False),
                        'removable': storage.get('removable_media', False)
                    })
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError) as e:
        disk_info['error'] = str(e)
    
    return disk_info

def get_memory_info() -> Dict[str, Any]:
    """
    Get memory information.
    
    Returns:
        Dict containing memory information
    """
    memory_info = {
        'total': 0,
        'available': 0,
        'used': 0,
        'error': None
    }
    
    try:
        # Get memory information using vm_stat
        result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            page_size = 4096  # Default page size for macOS
            
            # Parse vm_stat output
            stats = {}
            for line in lines[1:]:  # Skip header
                if ':' in line:
                    key, value = line.split(':', 1)
                    # Extract number from value (remove trailing period and spaces)
                    value = value.strip().rstrip('.')
                    try:
                        stats[key.strip()] = int(value)
                    except ValueError:
                        continue
            
            # Calculate memory values
            if 'Pages free' in stats and 'Pages active' in stats and 'Pages inactive' in stats:
                free_pages = stats.get('Pages free', 0)
                active_pages = stats.get('Pages active', 0)
                inactive_pages = stats.get('Pages inactive', 0)
                wired_pages = stats.get('Pages wired down', 0)
                
                memory_info['total'] = (free_pages + active_pages + inactive_pages + wired_pages) * page_size
                memory_info['available'] = free_pages * page_size
                memory_info['used'] = (active_pages + inactive_pages + wired_pages) * page_size
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
        memory_info['error'] = str(e)
    
    return memory_info

def get_cpu_info() -> Dict[str, Any]:
    """
    Get CPU information.
    
    Returns:
        Dict containing CPU information
    """
    cpu_info = {
        'cores': 0,
        'logical_cores': 0,
        'frequency': 0,
        'load_average': [],
        'error': None
    }
    
    try:
        # Get CPU core count
        result = subprocess.run(['sysctl', '-n', 'hw.physicalcpu'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            cpu_info['cores'] = int(result.stdout.strip())
        
        result = subprocess.run(['sysctl', '-n', 'hw.logicalcpu'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            cpu_info['logical_cores'] = int(result.stdout.strip())
        
        # Get CPU frequency
        result = subprocess.run(['sysctl', '-n', 'hw.cpufrequency'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            cpu_info['frequency'] = int(result.stdout.strip())
        
        # Get load average
        load_avg = os.getloadavg()
        cpu_info['load_average'] = list(load_avg)
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, ValueError) as e:
        cpu_info['error'] = str(e)
    
    return cpu_info

def check_admin_privileges() -> bool:
    """
    Check if the current process has administrator privileges.
    
    Returns:
        bool: True if running with admin privileges
    """
    return os.geteuid() == 0

def get_environment_info() -> Dict[str, Any]:
    """
    Get relevant environment information.
    
    Returns:
        Dict containing environment information
    """
    env_info = {
        'user': os.getenv('USER', 'unknown'),
        'home': os.getenv('HOME', 'unknown'),
        'path': os.getenv('PATH', ''),
        'shell': os.getenv('SHELL', 'unknown'),
        'term': os.getenv('TERM', 'unknown'),
        'lang': os.getenv('LANG', 'unknown'),
        'is_admin': check_admin_privileges(),
        'working_directory': os.getcwd()
    }
    
    return env_info
