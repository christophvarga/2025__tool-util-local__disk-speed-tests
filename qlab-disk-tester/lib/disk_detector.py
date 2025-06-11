import subprocess
import re
import os

class DiskDetector:
    def __init__(self, min_capacity_gb=300):
        self.min_capacity_gb = min_capacity_gb

    def _run_system_profiler(self):
        """Runs system_profiler SPStorageDataType and returns its output."""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPStorageDataType'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running system_profiler: {e}")
            return None

    def detect_disks(self):
        """Detects and parses information about storage devices."""
        output = self._run_system_profiler()
        if not output:
            return []

        disks = []
        lines = output.split('\n')
        current_disk = None
        in_physical_drive = False
        
        for line in lines:
            # New disk entry (4 spaces indentation + name + colon)
            if re.match(r'^    [^\s].*:$', line):
                if current_disk:  # Save previous disk
                    disks.append(current_disk)
                
                disk_name = line.strip().rstrip(':')
                current_disk = {"Name": disk_name, "Physical Drive": {}}
                in_physical_drive = False
                
            # Physical Drive section start
            elif line.strip() == "Physical Drive:" and current_disk:
                in_physical_drive = True
                
            # Key-value pairs (6+ spaces indentation)
            elif re.match(r'^      [^\s].*:', line) and current_disk:
                key_value = line.strip().split(':', 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    
                    if in_physical_drive:
                        current_disk["Physical Drive"][key] = value
                    else:
                        current_disk[key] = value
        
        # Don't forget the last disk
        if current_disk:
            disks.append(current_disk)
            
        return disks

    def _parse_size_to_gb(self, size_str):
        """Parse size string like '500 GB' to float in GB."""
        if not size_str or size_str == 'Unknown':
            return 0
        size_str = size_str.replace(',', '').strip()
        parts = size_str.split()
        if len(parts) >= 2:
            try:
                value = float(parts[0])
                unit = parts[1].upper()
                if unit in ['TB', 'TERABYTES']:
                    return value * 1024
                elif unit in ['GB', 'GIGABYTES']:
                    return value
                elif unit in ['MB', 'MEGABYTES']:
                    return value / 1024
            except ValueError:
                pass
        return 0

    def _get_diskutil_info(self):
        """Alternative detection using diskutil list."""
        try:
            result = subprocess.run(['diskutil', 'list'], capture_output=True, text=True, check=True)
            lines = result.stdout.split('\n')
            
            drives = []
            for line in lines:
                # Look for mounted volumes
                if '/dev/disk' in line and ('APFS' in line or 'HFS' in line):
                    parts = line.split()
                    if len(parts) >= 3:
                        device = parts[0]
                        # Get detailed info for this device
                        try:
                            info_result = subprocess.run(['diskutil', 'info', device], 
                                                       capture_output=True, text=True, check=True)
                            info_lines = info_result.stdout.split('\n')
                            
                            drive_info = {'Device': device}
                            for info_line in info_lines:
                                if ':' in info_line:
                                    key, value = info_line.split(':', 1)
                                    drive_info[key.strip()] = value.strip()
                            
                            # Check if it's mounted and has sufficient capacity
                            mount_point = drive_info.get('Mount Point', '')
                            total_size = drive_info.get('Disk Size', '')
                            
                            if mount_point and mount_point != '(not mounted)':
                                capacity_gb = self._parse_size_to_gb(total_size)
                                if capacity_gb >= self.min_capacity_gb:
                                    drives.append({
                                        'Name': drive_info.get('Volume Name', device),
                                        'Mount Point': mount_point,
                                        'Capacity': total_size,
                                        'Device': device,
                                        'File System': drive_info.get('Type (Bundle)', 'Unknown')
                                    })
                        except subprocess.CalledProcessError:
                            continue
            return drives
        except subprocess.CalledProcessError:
            return []

    def _get_df_info(self):
        """Alternative detection using df command."""
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
            lines = result.stdout.split('\n')[1:]  # Skip header
            
            drives = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 6 and parts[5].startswith('/') and parts[5] != '/':
                    mount_point = parts[5]
                    total_size = parts[1]
                    available = parts[3]
                    
                    # Parse capacity and check minimum
                    capacity_gb = self._parse_size_to_gb(total_size.replace('G', ' GB').replace('T', ' TB'))
                    if capacity_gb >= self.min_capacity_gb:
                        drives.append({
                            'Name': os.path.basename(mount_point),
                            'Mount Point': mount_point,
                            'Capacity': total_size,
                            'Free': available,
                            'Device': parts[0]
                        })
            return drives
        except subprocess.CalledProcessError:
            return []

    def get_large_drives(self):
        """Returns drives with capacity >= min_capacity_gb using multiple detection methods."""
        drives = []
        
        # Method 1: system_profiler (original SSD detection)
        all_disks = self.detect_disks()
        for disk in all_disks:
            if disk.get("Mount Point") and disk.get("Writable") == "Yes":
                capacity_gb = self._parse_size_to_gb(disk.get("Capacity", ""))
                if capacity_gb >= self.min_capacity_gb:
                    drive_type = "Unknown"
                    if "Physical Drive" in disk:
                        drive_type = disk["Physical Drive"].get("Medium Type", "Unknown")
                    
                    drives.append({
                        "Name": disk.get("Name"),
                        "Mount Point": disk.get("Mount Point"),
                        "Capacity": disk.get("Capacity"),
                        "Free": disk.get("Free"),
                        "Device Name": disk.get("Physical Drive", {}).get("Device Name", "Unknown"),
                        "Internal": disk.get("Physical Drive", {}).get("Internal", "Unknown"),
                        "Protocol": disk.get("Physical Drive", {}).get("Protocol", "Unknown"),
                        "Type": drive_type,
                        "Source": "system_profiler"
                    })
        
        # Method 2: diskutil (if system_profiler found nothing)
        if not drives:
            diskutil_drives = self._get_diskutil_info()
            for drive in diskutil_drives:
                drives.append({
                    "Name": drive['Name'],
                    "Mount Point": drive['Mount Point'],
                    "Capacity": drive['Capacity'],
                    "Free": "Unknown",
                    "Device Name": drive['Device'],
                    "Internal": "Unknown",
                    "Protocol": "Unknown",
                    "Type": drive.get('File System', 'Unknown'),
                    "Source": "diskutil"
                })
        
        # Method 3: df (if still nothing found)
        if not drives:
            df_drives = self._get_df_info()
            for drive in df_drives:
                drives.append({
                    "Name": drive['Name'],
                    "Mount Point": drive['Mount Point'],
                    "Capacity": drive['Capacity'],
                    "Free": drive['Free'],
                    "Device Name": drive['Device'],
                    "Internal": "Unknown",
                    "Protocol": "Unknown",
                    "Type": "Unknown",
                    "Source": "df"
                })
        
        return drives

    def get_ssds(self):
        """Legacy method - now calls get_large_drives for backward compatibility."""
        return self.get_large_drives()

    def validate_manual_path(self, path):
        """Validate a manually entered path for testing."""
        if not path:
            return False, "Path cannot be empty"
        
        if not os.path.exists(path):
            return False, f"Path does not exist: {path}"
        
        if not os.path.isdir(path):
            return False, f"Path is not a directory: {path}"
        
        if not os.access(path, os.W_OK):
            return False, f"Path is not writable: {path}"
        
        # Check available space
        try:
            statvfs = os.statvfs(path)
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            free_gb = free_bytes / (1024**3)
            
            if free_gb < 1:  # Minimum 1GB free space
                return False, f"Insufficient free space: {free_gb:.1f}GB (minimum 1GB required)"
            
            return True, f"Valid path with {free_gb:.1f}GB free space"
        except OSError as e:
            return False, f"Cannot check disk space: {e}"

    def get_volume_list(self):
        """Get a simple list of mounted volumes for manual selection."""
        volumes = []
        try:
            # Get all mounted volumes from /Volumes
            if os.path.exists('/Volumes'):
                for item in os.listdir('/Volumes'):
                    volume_path = f'/Volumes/{item}'
                    if os.path.isdir(volume_path) and os.access(volume_path, os.W_OK):
                        try:
                            statvfs = os.statvfs(volume_path)
                            free_bytes = statvfs.f_frsize * statvfs.f_bavail
                            total_bytes = statvfs.f_frsize * statvfs.f_blocks
                            free_gb = free_bytes / (1024**3)
                            total_gb = total_bytes / (1024**3)
                            
                            if total_gb >= self.min_capacity_gb:
                                volumes.append({
                                    'Name': item,
                                    'Mount Point': volume_path,
                                    'Capacity': f'{total_gb:.1f} GB',
                                    'Free': f'{free_gb:.1f} GB',
                                    'Device Name': 'Unknown',
                                    'Internal': 'Unknown',
                                    'Protocol': 'Unknown',
                                    'Type': 'Volume',
                                    'Source': 'volumes'
                                })
                        except OSError:
                            continue
            
            # Also add root filesystem if it's large enough
            try:
                statvfs = os.statvfs('/')
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
                total_bytes = statvfs.f_frsize * statvfs.f_blocks
                free_gb = free_bytes / (1024**3)
                total_gb = total_bytes / (1024**3)
                
                if total_gb >= self.min_capacity_gb:
                    volumes.append({
                        'Name': 'System Drive',
                        'Mount Point': '/',
                        'Capacity': f'{total_gb:.1f} GB',
                        'Free': f'{free_gb:.1f} GB',
                        'Device Name': 'System',
                        'Internal': 'Yes',
                        'Protocol': 'Internal',
                        'Type': 'System',
                        'Source': 'system'
                    })
            except OSError:
                pass
                
        except OSError:
            pass
            
        return volumes

if __name__ == "__main__":
    detector = DiskDetector()
    drives = detector.get_large_drives()
    if drives:
        print("Detected large drives:")
        for i, drive in enumerate(drives):
            print(f"  {i+1}. Name: {drive['Name']}")
            print(f"     Mount Point: {drive['Mount Point']}")
            print(f"     Capacity: {drive['Capacity']}, Free: {drive['Free']}")
            print(f"     Device Name: {drive['Device Name']}")
            print(f"     Internal: {drive['Internal']}")
            print(f"     Protocol: {drive['Protocol']}")
    else:
        print("No large drives detected. Trying volume list...")
        volumes = detector.get_volume_list()
        if volumes:
            print("Available volumes:")
            for i, vol in enumerate(volumes):
                print(f"  {i+1}. {vol['Name']} ({vol['Mount Point']}) - {vol['Free']} free of {vol['Capacity']}")
        else:
            print("No suitable volumes found.")
