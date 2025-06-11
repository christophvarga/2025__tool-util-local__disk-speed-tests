import os
import platform
import subprocess

class BinaryManager:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.bin_dir = os.path.join(self.script_dir, 'bin')
        
    def _get_architecture(self):
        """Verify Apple Silicon architecture."""
        machine = platform.machine().lower()
        if machine in ['arm64', 'aarch64']:
            return 'apple-silicon'
        else:
            raise RuntimeError(f"Unsupported architecture: {machine}. This tool requires Apple Silicon (M1/M2/M3) Macs only.")
    
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
                
        except RuntimeError as e:
            print(f"❌ {e}")
            return None  # Do not fall back - strict Apple Silicon requirement
        
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
        """Print installation instructions for Apple Silicon fio."""
        try:
            arch = self._get_architecture()
        except RuntimeError as e:
            print(f"❌ {e}")
            return
        
        print("📦 FIO INSTALLATION INSTRUCTIONS (Apple Silicon)")
        print("=" * 55)
        print(f"Architecture: {arch}")
        print(f"Required binary: bin/fio-{arch}")
        print()
        print("⚠️  This tool requires Apple Silicon (M1/M2/M3) Macs only")
        print()
        print("SETUP REQUIRED:")
        print("  1. Download fio binary for Apple Silicon")
        print("  2. Place as: bin/fio-apple-silicon")
        print("  3. Make executable: chmod +x bin/fio-apple-silicon")
        print()
        print("💡 This package uses bundled fio binary only")
        print("   No Homebrew or system fio installation needed")

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
