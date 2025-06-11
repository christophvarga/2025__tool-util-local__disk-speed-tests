import os
import platform
import subprocess

class BinaryManager:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.bin_dir = os.path.join(self.script_dir, 'bin')
        
    def _get_architecture(self):
        """Detect system architecture."""
        machine = platform.machine().lower()
        if machine in ['x86_64', 'amd64']:
            return 'intel'
        elif machine in ['arm64', 'aarch64']:
            return 'apple-silicon'
        else:
            raise RuntimeError(f"Unsupported architecture: {machine}")
    
    def get_fio_path(self):
        """
        Returns the path to the appropriate fio binary.
        Priority: bundled binary (verified) -> system fio (verified) -> None
        """
        try:
            arch = self._get_architecture()
            bundled_fio = os.path.join(self.bin_dir, f'fio-{arch}')
            
            # Check if bundled binary exists, is executable, and is real FIO
            if (os.path.exists(bundled_fio) and 
                os.access(bundled_fio, os.X_OK) and 
                self._verify_real_fio(bundled_fio)):
                return bundled_fio
                
        except RuntimeError:
            pass  # Fall back to system fio
        
        # Fall back to system fio (but verify it's real FIO)
        try:
            result = subprocess.run(['which', 'fio'], capture_output=True, text=True, check=True)
            system_fio = result.stdout.strip()
            if (system_fio and 
                os.access(system_fio, os.X_OK) and 
                self._verify_real_fio(system_fio)):
                return system_fio
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def check_fio_availability(self):
        """
        Checks if fio is available and returns status information.
        Returns: (is_available, fio_path, source_type)
        """
        fio_path = self.get_fio_path()
        
        if not fio_path:
            return False, None, None
            
        # Determine source type
        if fio_path.startswith(self.bin_dir):
            source_type = "bundled"
        else:
            source_type = "system"
            
        return True, fio_path, source_type
    
    def _verify_real_fio(self, fio_path):
        """Verify that the fio binary supports the features we need."""
        try:
            # Check if it supports --output-format=json
            result = subprocess.run([fio_path, '--help'], 
                                  capture_output=True, text=True, check=True)
            return '--output-format' in result.stdout and 'json' in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_fio_version(self, fio_path):
        """Get fio version information."""
        try:
            result = subprocess.run([fio_path, '--version'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "Unknown"
    
    def print_installation_instructions(self):
        """Print detailed installation instructions for fio."""
        arch = self._get_architecture()
        
        print("📦 FIO INSTALLATION INSTRUCTIONS")
        print("=" * 50)
        print(f"Detected Architecture: {arch}")
        print(f"Expected bundled binary: bin/fio-{arch}")
        print()
        print("OPTION 1: Download bundled binaries (Recommended)")
        print("  1. Visit: https://github.com/axboe/fio/releases")
        print("  2. Download the latest macOS binary for your architecture")
        print(f"  3. Rename it to 'fio-{arch}' and place in the 'bin/' directory")
        print("  4. Make it executable: chmod +x bin/fio-{arch}")
        print()
        print("OPTION 2: Install via Homebrew")
        print("  1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("  2. Install fio: brew install fio")
        print()
        print("OPTION 3: Manual installation")
        print("  1. Download fio source from https://github.com/axboe/fio")
        print("  2. Compile and install following the project's instructions")

if __name__ == "__main__":
    # Test the binary manager
    manager = BinaryManager()
    
    print(f"Architecture: {manager._get_architecture()}")
    print(f"Script directory: {manager.script_dir}")
    print(f"Bin directory: {manager.bin_dir}")
    
    is_available, fio_path, source_type = manager.check_fio_availability()
    
    if is_available:
        print(f"✅ fio found: {fio_path} ({source_type})")
        version = manager.get_fio_version(fio_path)
        print(f"Version: {version}")
    else:
        print("❌ fio not found")
        manager.print_installation_instructions()
