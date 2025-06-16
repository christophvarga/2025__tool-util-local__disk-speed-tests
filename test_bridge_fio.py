#!/usr/bin/env python3
import json
import sys
import os

# Add bridge-server and diskbench to path
sys.path.insert(0, './bridge-server')
sys.path.insert(0, './diskbench')

# Import the server module directly
import server
DiskBenchBridge = server.DiskBenchBridge

def test_fio_functionality():
    """Test FIO functionality from bridge server."""
    print("Testing FIO functionality from bridge server...")
    
    bridge = DiskBenchBridge()
    result = bridge.test_fio_functionality()
    
    print("FIO Test Result:")
    print(json.dumps(result, indent=2))
    
    if result.get('success'):
        print("\n✅ FIO functionality test PASSED")
        print(f"FIO found at: {result.get('fio_path', 'unknown')}")
    else:
        print("\n❌ FIO functionality test FAILED")
        print(f"Error: {result.get('error', 'unknown')}")
    
    return result.get('success', False)

if __name__ == '__main__':
    success = test_fio_functionality()
    sys.exit(0 if success else 1)
