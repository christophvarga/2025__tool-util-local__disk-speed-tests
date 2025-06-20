#!/usr/bin/env python3
"""
Test script for diskbench helper binary.
"""

import sys
import os
import subprocess
import json
import tempfile

def test_diskbench():
    """Test the diskbench helper binary."""
    print("Testing diskbench helper binary...")
    
    # Get the path to the main script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, 'main.py')
    
    if not os.path.exists(main_script):
        print(f"❌ Main script not found: {main_script}")
        return False
    
    # Test 1: Version check
    print("\n1. Testing version check...")
    try:
        result = subprocess.run([sys.executable, main_script, '--version'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Version check passed")
            print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ Version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Version check error: {e}")
        return False
    
    # Test 2: Validation
    print("\n2. Testing system validation...")
    try:
        result = subprocess.run([sys.executable, main_script, '--validate', '--json'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            validation_data = json.loads(result.stdout)
            overall_status = validation_data.get('overall_status', 'unknown')
            print(f"✅ Validation completed: {overall_status}")
            
            # Show validation details
            checks = validation_data.get('checks', {})
            for check_name, check_result in checks.items():
                status = "✅" if check_result.get('passed') else "❌"
                message = check_result.get('message', 'No message')
                print(f"   {status} {check_name}: {message}")
        else:
            print(f"❌ Validation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False
    
    # Test 3: List disks
    print("\n3. Testing disk listing...")
    try:
        result = subprocess.run([sys.executable, main_script, '--list-disks', '--json'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            disk_data = json.loads(result.stdout)
            disk_count = disk_data.get('count', 0)
            print(f"✅ Disk listing completed: {disk_count} disks found")
            
            # Show first few disks
            disks = disk_data.get('disks', [])
            for i, disk in enumerate(disks[:3]):
                name = disk.get('name', 'Unknown')
                device = disk.get('device', 'Unknown')
                size = disk.get('size', 'Unknown')
                print(f"   - {name} ({device}) - {size}")
        else:
            print(f"❌ Disk listing failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Disk listing error: {e}")
        return False
    
    # Test 4: FIO version check
    print("\n4. Testing FIO availability...")
    try:
        result = subprocess.run([sys.executable, main_script, '--version', '--check-fio', '--json'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            version_data = json.loads(result.stdout)
            fio_status = version_data.get('fio_status', {})
            if fio_status.get('available'):
                print(f"✅ FIO available: {fio_status.get('version')}")
                print(f"   Path: {fio_status.get('path')}")
            else:
                print(f"⚠️ FIO not available: {fio_status.get('error')}")
        else:
            print(f"❌ FIO check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ FIO check error: {e}")
        return False
    
    print("\n✅ All basic tests passed!")
    print("\nNext steps:")
    print("- Install FIO if not available")
    print("- Test with actual disk performance tests")
    print("- Integrate with web GUI")
    
    return True

if __name__ == '__main__':
    success = test_diskbench()
    sys.exit(0 if success else 1)
