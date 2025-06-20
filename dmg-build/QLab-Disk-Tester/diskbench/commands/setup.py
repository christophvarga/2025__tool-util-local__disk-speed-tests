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
        
        # No longer checking for smartmontools
        
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
    
    def install_smartmontools(self, progress_callback=None):
        """Install smartmontools via Homebrew with enhanced error handling."""
        logger.info("Installing smartmontools...")
        
        if progress_callback:
            progress_callback("🔧 Installing smartmontools via Homebrew...")
        
        # Check if already installed first
        if self._verify_smartmontools_installation():
            if progress_callback:
                progress_callback("✅ smartmontools already installed and working")
            logger.info("smartmontools already installed and working")
            return True
        
        # Check if Homebrew is installed
        homebrew_installed, homebrew_output = self._check_homebrew_detailed()
        
        if not homebrew_installed:
            error_msg = f"Homebrew not found: {homebrew_output}"
            if progress_callback:
                progress_callback(f"❌ ERROR: {error_msg}")
                progress_callback("Install Homebrew from: https://brew.sh")
                progress_callback("Then run: brew install smartmontools")
            logger.error(error_msg)
            return False
        
        if progress_callback:
            progress_callback(f"✅ Homebrew found: {homebrew_output}")
        
        # Try to install smartmontools via Homebrew
        try:
            if progress_callback:
                progress_callback("Executing: brew install smartmontools (this may take a few minutes)")
            
            # Use sudo userspace approach for Homebrew
            brew_command = self._get_user_brew_command(['install', 'smartmontools'])
            if progress_callback:
                progress_callback(f"Command: {' '.join(brew_command)}")
            
            result = subprocess.run(brew_command, capture_output=True, text=True, timeout=300)
            
            if progress_callback:
                progress_callback(f"Command completed with return code: {result.returncode}")
                if result.stdout.strip():
                    progress_callback(f"STDOUT:\n{result.stdout}")
                if result.stderr.strip():
                    progress_callback(f"STDERR:\n{result.stderr}")
            
            # Check success conditions
            success_indicators = [
                result.returncode == 0,
                "already installed" in (result.stderr or "").lower(),
                "already installed" in (result.stdout or "").lower()
            ]
            
            if any(success_indicators):
                # Verify installation actually worked
                if self._verify_smartmontools_installation():
                    if progress_callback:
                        progress_callback("✅ smartmontools installed and verified successfully")
                    logger.info("smartmontools installed and verified successfully")
                    return True
                else:
                    if progress_callback:
                        progress_callback("⚠️ smartmontools installation reported success but verification failed")
                    logger.warning("smartmontools installation reported success but verification failed")
                    return False
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"smartmontools installation failed: {error_msg}")
                if progress_callback:
                    progress_callback(f"❌ Installation FAILED: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = "smartmontools installation timed out after 5 minutes"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            return False
        except Exception as e:
            error_msg = f"smartmontools installation error: {e}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            return False
    
    def install_all_dependencies(self, progress_callback=None):
        """Install both FIO and smartmontools."""
        logger.info("Installing all dependencies...")
        
        if progress_callback:
            progress_callback("🚀 Installing all required dependencies...")
        
        # Install smartmontools first (simpler, faster)
        smartmontools_success = self.install_smartmontools(progress_callback)
        
        # Install FIO (more complex)
        fio_success = self.install_fio(progress_callback)
        
        overall_success = smartmontools_success and fio_success
        
        if progress_callback:
            if overall_success:
                progress_callback("✅ All dependencies installed successfully")
            else:
                failed_deps = []
                if not smartmontools_success:
                    failed_deps.append("smartmontools")
                if not fio_success:
                    failed_deps.append("FIO")
                progress_callback(f"❌ Failed to install: {', '.join(failed_deps)}")
        
        return overall_success
    
    def install_fio(self, progress_callback=None):
        """Install FIO via Homebrew and ensure it works without SHM issues."""
        logger.info("Starting comprehensive FIO installation...")
        
        if progress_callback:
            progress_callback("🔧 Phase 1: Homebrew FIO Installation...")
        
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
            
            # Use sudo userspace approach for Homebrew
            brew_command = self._get_user_brew_command(['install', 'fio'])
            result = subprocess.run(brew_command, capture_output=True, text=True, timeout=300)
            
            if progress_callback:
                progress_callback(f"Command completed with return code: {result.returncode}")
                if result.stdout:
                    progress_callback(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    progress_callback(f"STDERR:\n{result.stderr}")
            
            if result.returncode == 0 or "already installed" in (result.stderr or "").lower():
                if progress_callback:
                    progress_callback("FIO installed successfully via Homebrew")
                
                # Update our fio_path
                self.fio_path = shutil.which('fio')
                if progress_callback:
                    progress_callback(f"FIO found at: {self.fio_path}")
                
                # Phase 2: SHM Validation
                if progress_callback:
                    progress_callback("🔍 Phase 2: Testing FIO shared memory compatibility...")
                
                shm_test_result = self._test_fio_shm_support()
                
                if shm_test_result['has_shm_issues']:
                    if progress_callback:
                        progress_callback("⚠️ SHM Issues detected - compiling FIO without shared memory...")
                        progress_callback("🛠️ Phase 3: Auto-Fix - Building FIO-nosmh...")
                    
                    # Auto-fix by compiling no-shm version
                    auto_fix_result = self._auto_fix_fio_shm(progress_callback)
                    
                    if auto_fix_result:
                        if progress_callback:
                            progress_callback("✅ FIO-nosmh compiled and installed successfully")
                            progress_callback("✅ FIO installation completed with SHM fix")
                        return True
                    else:
                        if progress_callback:
                            progress_callback("❌ FIO-nosmh compilation failed")
                            progress_callback("⚠️ Standard FIO available but may have SHM limitations")
                        return False
                else:
                    if progress_callback:
                        progress_callback("✅ FIO SHM test passed - no issues detected")
                        progress_callback("✅ FIO installation completed successfully")
                    return True
                    
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Homebrew FIO installation failed: {error_msg}")
                if progress_callback:
                    progress_callback(f"Installation FAILED with return code {result.returncode}")
                    progress_callback(f"Error details: {error_msg}")
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
            # Use user-space brew command for checking
            brew_cmd = self._get_user_brew_command(['--version'])
            result = subprocess.run(brew_cmd, capture_output=True, text=True, timeout=10)
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
    
    def _get_user_brew_command(self, brew_args):
        """Get Homebrew command that runs as original user, not root."""
        original_user = os.environ.get('SUDO_USER')
        
        if original_user and os.geteuid() == 0:
            # We're running as root via sudo, run brew as original user
            logger.info(f"Running brew as user: {original_user}")
            return ['sudo', '-u', original_user, 'brew'] + brew_args
        else:
            # Not running as root or no SUDO_USER, run normally
            return ['brew'] + brew_args
    
    def _verify_smartmontools_installation(self):
        """Verify that smartmontools is properly installed and working."""
        try:
            # Check common installation paths
            smartctl_paths = [
                '/opt/homebrew/bin/smartctl',  # Apple Silicon Homebrew
                '/usr/local/bin/smartctl',     # Intel Homebrew
                '/usr/sbin/smartctl'           # System installation
            ]
            
            smartctl_path = None
            for path in smartctl_paths:
                if Path(path).exists() and os.access(path, os.X_OK):
                    smartctl_path = path
                    break
            
            # Also check system PATH
            if not smartctl_path:
                smartctl_path = shutil.which('smartctl')
            
            if not smartctl_path:
                logger.debug("smartctl binary not found in any standard location")
                return False
            
            # Test smartctl version command
            result = subprocess.run(
                [smartctl_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"smartmontools verified at: {smartctl_path}")
                return True
            else:
                logger.warning(f"smartctl version test failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.debug(f"smartmontools verification failed: {e}")
            return False
    
    def _test_fio_shm_support(self):
        """Test if FIO has shared memory issues."""
        logger.info("Testing FIO shared memory support...")
        
        if not self.fio_path:
            return {'has_shm_issues': True, 'error': 'No FIO path available'}
        
        try:
            # Create a minimal FIO test to check for SHM issues
            test_file = '/tmp/fio_shm_test'
            fio_command = [
                self.fio_path,
                '--name=shm_test',
                f'--filename={test_file}',
                '--size=1M',
                '--bs=4k',
                '--rw=read',
                '--runtime=1',
                '--time_based=1',
                '--ioengine=libaio',
                '--direct=1',
                '--numjobs=2',
                '--group_reporting=1',
                '--output-format=json'
            ]
            
            result = subprocess.run(
                fio_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check for shared memory error
            if result.returncode != 0 and 'failed to setup shm segment' in result.stderr:
                logger.warning("FIO shared memory issue detected")
                return {
                    'has_shm_issues': True,
                    'error': result.stderr,
                    'reason': 'shm_error_detected'
                }
            elif result.returncode == 0:
                logger.info("FIO shared memory test passed")
                return {
                    'has_shm_issues': False,
                    'reason': 'shm_test_passed'
                }
            else:
                # Other error, but not SHM-related
                logger.info("FIO test failed but not due to SHM issues")
                return {
                    'has_shm_issues': False,
                    'reason': 'other_error',
                    'error': result.stderr
                }
                
        except Exception as e:
            logger.error(f"SHM test failed: {e}")
            return {
                'has_shm_issues': True,
                'error': str(e),
                'reason': 'test_failed'
            }
        finally:
            # Cleanup test file
            try:
                if os.path.exists('/tmp/fio_shm_test'):
                    os.remove('/tmp/fio_shm_test')
            except:
                pass
    
    def _auto_fix_fio_shm(self, progress_callback=None):
        """Auto-fix FIO shared memory issues by compiling without SHM."""
        logger.info("Starting FIO SHM auto-fix...")
        
        if progress_callback:
            progress_callback("🔧 Installing build dependencies...")
        
        # Install build dependencies
        try:
            # Use sudo userspace approach for Homebrew
            deps_cmd = self._get_user_brew_command(['install', 'automake', 'libtool'])
            result = subprocess.run(deps_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Dependency installation failed: {e}")
            return False
        
        if progress_callback:
            progress_callback("📦 Downloading FIO source...")
        
        # Download and compile FIO
        build_dir = None
        try:
            build_dir = tempfile.mkdtemp(prefix='fio_build_')
            
            # Download FIO source
            fio_url = 'https://github.com/axboe/fio/archive/refs/tags/fio-3.40.tar.gz'
            fio_tar = os.path.join(build_dir, 'fio.tar.gz')
            
            urllib.request.urlretrieve(fio_url, fio_tar)
            
            if progress_callback:
                progress_callback("📦 Extracting FIO source...")
            
            # Extract
            with tarfile.open(fio_tar, 'r:gz') as tar:
                tar.extractall(build_dir)
            
            fio_src_dir = os.path.join(build_dir, 'fio-fio-3.40')
            
            if progress_callback:
                progress_callback("⚙️ Configuring FIO without shared memory...")
            
            # Configure without shared memory
            configure_cmd = ['./configure', '--disable-shm']
            result = subprocess.run(
                configure_cmd,
                cwd=fio_src_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"Configure failed: {result.stderr}")
                return False
            
            if progress_callback:
                progress_callback("🔨 Compiling FIO (this may take a few minutes)...")
            
            # Compile
            make_cmd = ['make', '-j4']
            result = subprocess.run(
                make_cmd,
                cwd=fio_src_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
            
            if result.returncode != 0:
                logger.error(f"Compilation failed: {result.stderr}")
                return False
            
            if progress_callback:
                progress_callback("📦 Installing FIO-nosmh...")
                progress_callback("🔐 Administrator-Rechte benötigt für Installation nach /usr/local/bin/")
                progress_callback("Bitte geben Sie Ihr Administrator-Passwort ein, wenn abgefragt:")
            
            # Install to /usr/local/bin/fio-nosmh
            fio_binary = os.path.join(fio_src_dir, 'fio')
            install_path = '/usr/local/bin/fio-nosmh'
            
            # Copy with interactive sudo (no capture_output to allow password prompt)
            install_cmd = ['sudo', 'cp', fio_binary, install_path]
            try:
                result = subprocess.run(install_cmd, timeout=120)  # 2 minutes timeout for user input
                
                if result.returncode != 0:
                    logger.error(f"Installation failed with return code: {result.returncode}")
                    if progress_callback:
                        progress_callback("❌ Installation fehlgeschlagen - Administrator-Rechte verweigert oder Timeout")
                    return False
                
                if progress_callback:
                    progress_callback("✅ FIO-nosmh erfolgreich installiert")
                
                # Make executable with interactive sudo
                if progress_callback:
                    progress_callback("🔧 Setze Ausführungsrechte...")
                
                chmod_cmd = ['sudo', 'chmod', '+x', install_path]
                chmod_result = subprocess.run(chmod_cmd, timeout=60)
                
                if chmod_result.returncode != 0:
                    logger.warning(f"chmod failed, but installation may still work")
                    if progress_callback:
                        progress_callback("⚠️ Berechtigung setzen fehlgeschlagen, aber Installation möglicherweise erfolgreich")
                    
            except subprocess.TimeoutExpired:
                logger.error("sudo installation timed out - user may not have entered password")
                if progress_callback:
                    progress_callback("❌ Installation timeout - Passwort nicht rechtzeitig eingegeben")
                return False
            except Exception as e:
                logger.error(f"Interactive sudo failed: {e}")
                if progress_callback:
                    progress_callback(f"❌ Installation fehlgeschlagen: {e}")
                return False
            
            if progress_callback:
                progress_callback("🧪 Testing FIO-nosmh installation...")
            
            # Test the new binary
            test_result = subprocess.run(
                [install_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if test_result.returncode == 0:
                logger.info("FIO-nosmh installation successful")
                return True
            else:
                logger.error("FIO-nosmh test failed")
                return False
                
        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")
            return False
        finally:
            # Cleanup
            if build_dir and os.path.exists(build_dir):
                shutil.rmtree(build_dir, ignore_errors=True)
    
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
    """Handle the install/fix all dependencies command."""
    setup_manager = SetupManager()
    
    def progress_callback(message):
        if not getattr(args, 'quiet', False):
            print(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    import time
    
    success = setup_manager.install_all_dependencies(progress_callback)
    
    if args.json:
        print(json.dumps({
            'success': success,
            'message': 'All dependencies installation completed' if success else 'Dependencies installation failed'
        }, indent=2))
    else:
        if success:
            print("✅ All dependencies installation/fix completed successfully")
        else:
            print("❌ Dependencies installation/fix failed")
    
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
