#!/usr/bin/env python3
"""
QLab Disk Performance Tester Setup Script
Handles installation of dependencies and system configuration.

This application uses only Python Standard Library - no external Python packages required!
Only FIO (via Homebrew) is needed as external dependency.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header():
    """Print setup header."""
    print("🚀 QLab Disk Performance Tester Setup v1.3")
    print("=" * 45)
    print("✨ No External Python Dependencies Required!")
    print("   Uses Python Standard Library only")
    print()

def check_python():
    """Check Python version."""
    print("🐍 Checking Python...")
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} found")
    print("✅ Python Standard Library available (all we need!)")
    return True

def check_homebrew():
    """Check if Homebrew is installed and configure PATH if needed."""
    print("\n🍺 Checking Homebrew...")
    
    # Common Homebrew paths
    brew_paths = [
        '/opt/homebrew/bin/brew',  # Apple Silicon
        '/usr/local/bin/brew',     # Intel Mac
        'brew'                     # In PATH
    ]
    
    for brew_path in brew_paths:
        try:
            result = subprocess.run([brew_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Homebrew found")
                
                # If using direct path, ensure it's in environment for this session
                if brew_path != 'brew':
                    brew_dir = os.path.dirname(brew_path)
                    current_path = os.environ.get('PATH', '')
                    if brew_dir not in current_path:
                        os.environ['PATH'] = f"{brew_dir}:{current_path}"
                        print(f"✅ Added {brew_dir} to PATH for this session")
                
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    print("❌ Homebrew not found")
    print("\n   Install Homebrew:")
    print('   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
    print("\n   After installation, run these commands:")
    print('   echo \'eval "$(/opt/homebrew/bin/brew shellenv)"\' >> ~/.zprofile')
    print('   eval "$(/opt/homebrew/bin/brew shellenv)"')
    print("\n   Then re-run this setup script.")
    return False

def setup_homebrew_path():
    """Setup Homebrew PATH in shell profile for future sessions."""
    print("\n🔧 Configuring Homebrew PATH...")
    
    # Detect if we're on Apple Silicon
    try:
        result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
        is_apple_silicon = 'arm64' in result.stdout
    except:
        is_apple_silicon = False
    
    if is_apple_silicon:
        homebrew_path = '/opt/homebrew/bin/brew'
        shell_env_cmd = 'eval "$(/opt/homebrew/bin/brew shellenv)"'
    else:
        homebrew_path = '/usr/local/bin/brew'
        shell_env_cmd = 'eval "$(/usr/local/bin/brew shellenv)"'
    
    # Check if Homebrew is installed but not in PATH
    if os.path.exists(homebrew_path):
        try:
            subprocess.run(['brew', '--version'], capture_output=True, timeout=5)
            print("✅ Homebrew already in PATH")
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Homebrew exists but not in PATH
            print("⚠️ Homebrew installed but not in PATH. Configuring...")
            
            # Add to shell profiles
            shell_profiles = [
                os.path.expanduser('~/.zprofile'),
                os.path.expanduser('~/.bash_profile')
            ]
            
            for profile in shell_profiles:
                try:
                    # Check if already configured
                    if os.path.exists(profile):
                        with open(profile, 'r') as f:
                            content = f.read()
                            if 'brew shellenv' in content:
                                continue
                    
                    # Add Homebrew configuration
                    with open(profile, 'a') as f:
                        f.write(f'\n# Added by QLab Disk Tester setup\n')
                        f.write(f'{shell_env_cmd}\n')
                    
                    print(f"✅ Added Homebrew PATH to {profile}")
                except Exception as e:
                    print(f"⚠️ Could not update {profile}: {e}")
            
            # Set for current session
            homebrew_dir = os.path.dirname(homebrew_path)
            current_path = os.environ.get('PATH', '')
            if homebrew_dir not in current_path:
                os.environ['PATH'] = f"{homebrew_dir}:{current_path}"
            
            return True
    
    return False

def install_fio():
    """Install FIO via Homebrew and handle SHM issues."""
    print("\n⚡ Setting up FIO...")
    
    # Check if FIO is already installed in common locations
    fio_paths = [
        '/usr/local/bin/fio-nosmh',   # No-SHM version (preferred)
        '/opt/homebrew/bin/fio',      # Apple Silicon Homebrew
        '/usr/local/bin/fio',         # Intel Homebrew
    ]
    
    fio_installed = False
    for fio_path in fio_paths:
        if Path(fio_path).exists():
            fio_installed = True
            if 'nosmh' in fio_path:
                print("✅ FIO (no-SHM version) found")
            else:
                print("⚠️ Standard FIO found. May have shared memory limitations.")
            break
    
    if fio_installed:
        # Test for SHM issues if standard FIO is found
        if not test_fio_shm():
            print("⚠️ FIO has shared memory issues. diskbench will handle this.")
        else:
            print("✅ FIO is working correctly")
        return True

    # If FIO is not installed, try to install it via Homebrew
    print("📥 Installing FIO via Homebrew...")
    if not check_homebrew():
        print("\n   Please install Homebrew and re-run this setup script.")
        return False

    try:
        result = subprocess.run(['brew', 'install', 'fio'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 or "already installed" in result.stderr.lower():
            print("✅ FIO installed via Homebrew")
            
            # Test for SHM issues after installation
            print("🧪 Testing FIO...")
            if test_fio_shm():
                print("✅ FIO working correctly")
            else:
                print("⚠️ FIO has shared memory issues. diskbench will handle this.")
            return True
        else:
            print("❌ FIO installation failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FIO installation timed out")
        return False
    except Exception:
        print("❌ FIO installation error")
        return False

def test_fio_shm():
    """Test if FIO has shared memory issues by running a small test."""
    try:
        test_file = Path('/tmp/fio_shm_test_file')
        result = subprocess.run([
            'fio', '--name=shm_test', f'--filename={test_file}', '--size=1M',
            '--bs=4k', '--rw=read', '--runtime=1', '--time_based=1',
            '--ioengine=sync', '--direct=1', '--numjobs=1', '--group_reporting'
        ], capture_output=True, text=True, timeout=30)
        
        try:
            test_file.unlink(missing_ok=True)
        except Exception:
            pass # Ignore cleanup errors
        
        if 'failed to setup shm segment' in result.stderr.lower():
            return False
        return result.returncode == 0
        
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def run_validation():
    """Run system validation using diskbench."""
    print("\n🔍 Running system validation...")
    
    script_dir = Path(__file__).parent
    diskbench_path = script_dir / 'diskbench' / 'main.py'
    
    if not diskbench_path.exists():
        print("❌ diskbench script not found")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, str(diskbench_path), '--validate', '--json'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            try:
                validation_data = json.loads(result.stdout)
                if validation_data.get('success', False):
                    print("✅ System validation passed")
                    return True
                else:
                    print("⚠️ System validation warnings")
                    return True 
            except json.JSONDecodeError:
                print("❌ Validation output error")
                return False
        else:
            print("❌ System validation failed")
            return False
        
    except FileNotFoundError:
        print("❌ Python interpreter or diskbench script not found")
        return False
    except subprocess.TimeoutExpired:
        print("❌ System validation timed out")
        return False
    except Exception:
        print("❌ System validation error")
        return False

def main():
    """Main setup function."""
    print_header()
    
    setup_successful = True
    
    # Step 1: Check Python (only requirement!)
    if not check_python():
        setup_successful = False
    
    # Step 2: Check and configure Homebrew
    if setup_successful:
        if not check_homebrew():
            # Try to setup PATH if Homebrew exists but isn't in PATH
            if not setup_homebrew_path():
                print("\n   Please install Homebrew and re-run this setup script.")
                return 1
            else:
                # Try checking Homebrew again after PATH setup
                if not check_homebrew():
                    print("\n   Homebrew PATH configured. Please restart your terminal and re-run setup.")
                    return 1
    
    # Step 3: Install FIO (only external dependency)
    if setup_successful and not install_fio():
        setup_successful = False
    
    # Step 4: Run system validation (non-critical)
    if setup_successful and not run_validation():
        print("⚠️ System validation had issues, but setup can continue")
    
    print("\n" + "=" * 45)
    if setup_successful:
        print("🎉 Setup completed successfully!")
        print("\n   ✨ Architecture:")
        print("   • Python Standard Library (HTTP server, JSON, etc.)")
        print("   • FIO (disk benchmarking tool)")
        print("   • No external Python packages required!")
        print("\n   🚀 Next steps:")
        print("   1. Double-click 'start-disk-tester.sh' to launch")
        print("   2. Or run: ./start-disk-tester.sh")
        print("   3. Web interface will open at http://localhost:8765")
        print("\n   ✅ Dependencies installed:")
        print("   • Python Standard Library (built-in)")
        print("   • FIO (disk benchmarking tool)")
        print("   • Homebrew (package manager)")
        print("\n   🔧 Compatibility:")
        print("   • Works with Python 3.13+ (no pip install issues)")
        print("   • No 'externally-managed-environment' problems")
        print("   • Clean system installation")
    else:
        print("❌ Setup encountered errors. Please review messages above.")
        print("\n   Common solutions:")
        print("   • Install Homebrew if missing")
        print("   • Check internet connection for FIO download")
        print("   • Run with administrator privileges if needed")
        print("   • Resolve issues and re-run setup")
    
    print("\n   For detailed help, consult README.md")
    
    return 0 if setup_successful else 1

if __name__ == '__main__':
    sys.exit(main())
