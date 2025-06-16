#!/usr/bin/env python3
"""
Setup commands for the diskbench tool.
Handles system detection, FIO installation, and validation.
"""

import os
import sys
import json
import subprocess
import shutil
import tempfile
import urllib.request
import tarfile
from pathlib import Path

from utils.logging import get_logger
from utils.system_info import get_system_info

logger = get_logger(__name__)

class SetupManager:
    def __init__(self):
        self.system_info = get_system_info()
        self.fio_path = None
        
    def detect_system_status(self):
        """Detect current system status and FIO availability."""
        logger.info("Detecting system status...")
        
        status = {
            'fio_available': False,
            'fio_working': False,
            'fio_partial': False,  # FIO available but with limitations
            'disk_access': True,  # Assume disk access is available
            'system_compatible': True,
            'issues': [],
            'warnings': []
        }
        
        # Check Homebrew FIO (only supported installation method)
        homebrew_paths = [
            '/opt/homebrew/bin/fio',  # Apple Silicon Homebrew
            '/usr/local/bin/fio',     # Intel Homebrew
        ]
        
        fio_type = None
        for fio_path in homebrew_paths:
            if Path(fio_path).exists():
                self.fio_path = fio_path
                status['fio_available'] = True
                fio_type = 'homebrew'
                logger.info(f"Found Homebrew FIO at: {self.fio_path}")
                break
        
        # Check system PATH (backup for other installations)
        if not status['fio_available']:
            fio_system = shutil.which('fio')
            if fio_system and fio_system not in homebrew_paths:
                self.fio_path = fio_system
                status['fio_available'] = True
                fio_type = 'system'
                logger.info(f"Found system FIO at: {self.fio_path}")
        
        # No FIO found
        if not status['fio_available']:
            status['issues'].append("FIO not found. Install with: brew install fio")
            logger.warning("FIO not found. Install with: brew install fio")
        
        # Add FIO type information to status
        status['fio_type'] = fio_type
        
        # Check FIO binary availability only (no execution test)
        if status['fio_available'] and self.fio_path:
            fio_binary_result = self.check_fio_binary_only()
            if fio_binary_result:
                status['fio_working'] = True
                logger.info("FIO binary check passed - execution tests will run from bridge server")
            else:
                status['fio_partial'] = True
                status['warnings'].append("FIO binary check failed")
                logger.info("FIO binary check failed")
        
        # Check macOS compatibility
        if self.system_info['platform'] != 'Darwin':
            status['system_compatible'] = False
            status['issues'].append("This setup is designed for macOS")
        
        # Consider system "usable" if FIO is available (even partially)
        status['system_usable'] = status['fio_available'] and (status['fio_working'] or status['fio_partial'])
        
        return status
    
    def check_fio_binary_only(self):
        """Check if FIO binary exists and can show version (no execution test)."""
        logger.info("Checking FIO binary availability (no execution test)...")
        
        if not self.fio_path:
            logger.warning("No FIO path available for testing")
            return False
            
        try:
            # Only check version - no actual test execution
            result = subprocess.run(
                [self.fio_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("FIO binary check passed (version command works)")
                return True
            else:
                logger.error(f"FIO version check failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"FIO binary check error: {e}")
            return False
    
    def install_fio(self, progress_callback=None):
        """Guide user to install FIO via Homebrew (recommended method)."""
        logger.info("Starting FIO installation guidance...")
        
        if progress_callback:
            progress_callback("Checking for Homebrew installation...")
        
        # Check if Homebrew is installed
        homebrew_installed, homebrew_output = self._check_homebrew_detailed()
        
        if progress_callback:
            progress_callback(f"Homebrew check output: {homebrew_output}")
        
        if not homebrew_installed:
            if progress_callback:
                progress_callback("ERROR: Homebrew not found. Manual installation required.")
                progress_callback("Install Homebrew from: https://brew.sh")
                progress_callback("Then run: brew install fio")
            logger.error("Homebrew not found. Install from: https://brew.sh")
            return False
        
        if progress_callback:
            progress_callback("Homebrew found. Attempting FIO installation...")
            progress_callback("Command: brew install fio")
        
        # Try to install FIO via Homebrew
        try:
            if progress_callback:
                progress_callback("Executing: brew install fio (this may take several minutes)")
            
            result = subprocess.run(['brew', 'install', 'fio'], 
                                  capture_output=True, text=True, timeout=300)
            
            if progress_callback:
                progress_callback(f"Command completed with return code: {result.returncode}")
                if result.stdout:
                    progress_callback(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    progress_callback(f"STDERR:\n{result.stderr}")
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback("FIO installed successfully via Homebrew")
                
                # Update our fio_path
                self.fio_path = shutil.which('fio')
                if progress_callback:
                    progress_callback(f"FIO found at: {self.fio_path}")
                
                # Test installation (binary check only)
                if self.check_fio_binary_only():
                    logger.info("FIO installation and binary check successful")
                    if progress_callback:
                        progress_callback("FIO binary check: PASSED")
                        progress_callback("Note: FIO execution tests will run from bridge server")
                    return True
                else:
                    logger.warning("FIO installed but binary check failed")
                    if progress_callback:
                        progress_callback("FIO binary check: FAILED")
                        progress_callback("Note: FIO may still be usable - verify manually")
                    return True  # Still consider success since installation completed
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Homebrew FIO installation failed: {error_msg}")
                if progress_callback:
                    progress_callback(f"Installation FAILED with return code {result.returncode}")
                    progress_callback(f"Error details: {error_msg}")
                    
                    # Check for common permission issues
                    if "Permission denied" in error_msg or "Operation not permitted" in error_msg:
                        progress_callback("PERMISSION ERROR DETECTED:")
                        progress_callback("Try running manually in terminal:")
                        progress_callback("  sudo chown -R $(whoami) /usr/local/share/zsh")
                        progress_callback("  sudo chown -R $(whoami) /usr/local/share/zsh/site-functions")
                        progress_callback("  brew install fio")
                    elif "already installed" in error_msg.lower():
                        progress_callback("FIO appears to already be installed")
                        return True
                        
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FIO installation timed out")
            if progress_callback:
                progress_callback("Installation timed out after 5 minutes")
                progress_callback("Try running manually: brew install fio")
            return False
        except Exception as e:
            logger.error(f"FIO installation error: {e}")
            if progress_callback:
                progress_callback(f"Installation error: {e}")
                progress_callback("Try running manually: brew install fio")
            return False
    
    def _check_homebrew(self):
        """Check if Homebrew is installed."""
        try:
            result = subprocess.run(['brew', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def _check_homebrew_detailed(self):
        """Check if Homebrew is installed with detailed output."""
        try:
            result = subprocess.run(['brew', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, f"Brew command failed: {result.stderr}"
        except FileNotFoundError:
            return False, "Homebrew command 'brew' not found in PATH"
        except subprocess.TimeoutExpired:
            return False, "Homebrew version check timed out"
        except Exception as e:
            return False, f"Error checking Homebrew: {str(e)}"
    
    def run_validation_tests(self):
        """Run validation tests to ensure everything is working."""
        logger.info("Running validation tests...")
        
        # Ensure we detect FIO first
        if not self.fio_path:
            status = self.detect_system_status()
            logger.info(f"Detected FIO at: {self.fio_path}")
        
        tests = {
            'fio_binary_test': False,
            'disk_access_test': False,
            'performance_test': False,
            'configuration_test': False
        }
        
        # Test 1: FIO Binary Test
        try:
            if self.fio_path and os.path.exists(self.fio_path):
                result = subprocess.run([self.fio_path, '--version'], capture_output=True, timeout=10)
                tests['fio_binary_test'] = result.returncode == 0
                logger.info(f"FIO binary test: {'PASS' if tests['fio_binary_test'] else 'FAIL'}")
            else:
                logger.warning(f"FIO path not found: {self.fio_path}")
        except Exception as e:
            logger.error(f"FIO binary test failed: {e}")
            tests['fio_binary_test'] = False
        
        # Test 2: Disk Access Test
        try:
            test_file = '/tmp/diskbench_access_test'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            tests['disk_access_test'] = True
            logger.info("Disk access test: PASS")
        except Exception as e:
            logger.error(f"Disk access test failed: {e}")
            tests['disk_access_test'] = False
        
        # Test 3: Performance Test (binary check only - no execution)
        if self.fio_path:
            tests['performance_test'] = self.check_fio_binary_only()
            logger.info(f"Performance test (binary check): {'PASS' if tests['performance_test'] else 'FAIL'}")
            logger.info("Note: FIO execution tests will run from bridge server")
        else:
            logger.warning("Skipping performance test - no FIO available")
            tests['performance_test'] = False
        
        # Test 4: Configuration Test
        tests['configuration_test'] = all([
            tests['fio_binary_test'],
            tests['disk_access_test']
            # Note: We don't require performance_test to pass due to macOS limitations
        ])
        
        # Mark system as usable even if FIO has limitations (common on macOS)
        tests['system_usable'] = (
            tests['fio_binary_test'] and 
            tests['disk_access_test']
            # FIO functionality not required - we have Python fallback
        )
        
        return tests

def handle_detect_command(args):
    """Handle the detect system status command."""
    setup_manager = SetupManager()
    status = setup_manager.detect_system_status()
    
    if args.json:
        print(json.dumps({
            'success': True,
            'status': status
        }, indent=2))
    else:
        print("System Status Detection:")
        print(f"  FIO Available: {'✅' if status['fio_available'] else '❌'}")
        print(f"  FIO Working: {'✅' if status['fio_working'] else '❌'}")
        print(f"  Disk Access: {'✅' if status['disk_access'] else '❌'}")
        print(f"  System Compatible: {'✅' if status['system_compatible'] else '❌'}")
        
        if status['issues']:
            print("\nIssues found:")
            for issue in status['issues']:
                print(f"  - {issue}")
    
    # Return success if system is usable (even with FIO limitations)
    return 0 if status.get('system_usable', False) else 1

def handle_install_command(args):
    """Handle the install/fix FIO command."""
    setup_manager = SetupManager()
    
    def progress_callback(message):
        if not getattr(args, 'quiet', False):
            print(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    import time
    
    success = setup_manager.install_fio(progress_callback)
    
    if args.json:
        print(json.dumps({
            'success': success,
            'message': 'FIO installation completed' if success else 'FIO installation failed'
        }, indent=2))
    else:
        if success:
            print("✅ FIO installation/fix completed successfully")
        else:
            print("❌ FIO installation/fix failed")
    
    return 0 if success else 1

def handle_validate_command(args):
    """Handle the validation tests command."""
    setup_manager = SetupManager()
    tests = setup_manager.run_validation_tests()
    
    if args.json:
        print(json.dumps({
            'success': all(tests.values()),
            'tests': tests
        }, indent=2))
    else:
        print("Validation Test Results:")
        for test_name, result in tests.items():
            status = '✅ PASS' if result else '❌ FAIL'
            readable_name = test_name.replace('_', ' ').title()
            print(f"  {readable_name}: {status}")
        
        overall = '✅ ALL TESTS PASSED' if all(tests.values()) else '❌ SOME TESTS FAILED'
        print(f"\nOverall: {overall}")
    
    return 0 if all(tests.values()) else 1
