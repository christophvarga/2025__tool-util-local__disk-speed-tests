#!/bin/bash

# QLab Disk Tester Installation Script
# Automatically sets up the application on a new Mac

set -e  # Exit on any error

# ANSI escape codes for colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print colored output
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo
    print_colored "$BLUE$BOLD" "================================================"
    print_colored "$BLUE$BOLD" "    QLab Disk Performance Tester - Installer"
    print_colored "$BLUE$BOLD" "================================================"
    echo
}

print_step() {
    print_colored "$BLUE" "[$1/6] $2"
}

print_success() {
    print_colored "$GREEN" "✅ $1"
}

print_warning() {
    print_colored "$YELLOW" "⚠️  $1"
}

print_error() {
    print_colored "$RED" "❌ $1"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This installer is designed for macOS only."
        exit 1
    fi
}

# Detect Mac architecture
detect_architecture() {
    local arch=$(uname -m)
    case $arch in
        "arm64")
            echo "apple-silicon"
            ;;
        "x86_64")
            echo "intel"
            ;;
        *)
            print_warning "Unknown architecture: $arch. Defaulting to apple-silicon."
            echo "apple-silicon"
            ;;
    esac
}

# Check Python 3 installation
check_python() {
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 found: $python_version"
        
        # Check if version is >= 3.7
        local major=$(echo $python_version | cut -d'.' -f1)
        local minor=$(echo $python_version | cut -d'.' -f2)
        
        if [[ $major -ge 3 ]] && [[ $minor -ge 7 ]]; then
            return 0
        else
            print_warning "Python 3.7+ recommended. Current: $python_version"
            return 0
        fi
    else
        print_error "Python 3 not found. Please install Python 3.7+ from https://python.org"
        exit 1
    fi
}

# Set executable permissions for FIO binaries
setup_permissions() {
    local arch=$1
    
    if [[ -f "bin/fio-$arch" ]]; then
        chmod +x "bin/fio-$arch"
        print_success "Set executable permissions for bin/fio-$arch"
    else
        print_warning "FIO binary for $arch not found in bin/ directory"
    fi
    
    # Also set permissions for the main script
    if [[ -f "qlab_disk_tester.py" ]]; then
        chmod +x "qlab_disk_tester.py"
        print_success "Set executable permissions for qlab_disk_tester.py"
    fi
}

# Check for FIO availability
check_fio() {
    local arch=$1
    local fio_found=false
    
    # Check bundled binary first
    if [[ -f "bin/fio-$arch" ]]; then
        print_success "Found bundled FIO binary for $arch architecture"
        fio_found=true
    fi
    
    # Check system FIO
    if command -v fio &> /dev/null; then
        local fio_version=$(fio --version 2>&1 | head -1)
        print_success "Found system FIO: $fio_version"
        fio_found=true
    fi
    
    if [[ "$fio_found" == false ]]; then
        print_warning "FIO not found. The application will provide installation instructions when run."
        echo
        print_colored "$YELLOW" "To install FIO now, you can use:"
        print_colored "$YELLOW" "  brew install fio"
        print_colored "$YELLOW" "  or"
        print_colored "$YELLOW" "  sudo port install fio"
        echo
    fi
}

# Verify project structure
verify_structure() {
    local required_files=(
        "qlab_disk_tester.py"
        "lib/__init__.py"
        "lib/binary_manager.py"
        "lib/disk_detector.py"
        "lib/fio_engine.py"
        "lib/qlab_analyzer.py"
        "lib/report_generator.py"
        "README.md"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -eq 0 ]]; then
        print_success "All required files present"
    else
        print_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
}

# Create desktop shortcut (optional)
create_shortcut() {
    local current_dir=$(pwd)
    local desktop_dir="$HOME/Desktop"
    local shortcut_name="QLab Disk Tester"
    
    read -p "Create desktop shortcut? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Create a simple shell script that launches the app
        cat > "$desktop_dir/$shortcut_name.command" << EOF
#!/bin/bash
cd "$current_dir"
python3 qlab_disk_tester.py
EOF
        
        chmod +x "$desktop_dir/$shortcut_name.command"
        print_success "Desktop shortcut created: $shortcut_name.command"
    fi
}

# Test installation
test_installation() {
    print_colored "$BLUE" "Testing installation..."
    
    # Quick syntax check
    if python3 -m py_compile qlab_disk_tester.py; then
        print_success "Python syntax check passed"
    else
        print_error "Python syntax check failed"
        return 1
    fi
    
    # Try importing modules
    if python3 -c "
import sys
sys.path.append('.')
from lib.binary_manager import BinaryManager
from lib.disk_detector import DiskDetector
from lib.fio_engine import FioEngine
from lib.qlab_analyzer import QLabAnalyzer
from lib.report_generator import ReportGenerator
print('All modules imported successfully')
"; then
        print_success "Module import test passed"
    else
        print_error "Module import test failed"
        return 1
    fi
}

# Main installation process
main() {
    print_header
    
    print_step 1 "Checking macOS compatibility"
    check_macos
    print_success "Running on macOS"
    
    print_step 2 "Detecting system architecture"
    local arch=$(detect_architecture)
    print_success "Detected architecture: $arch"
    
    print_step 3 "Verifying project structure"
    verify_structure
    
    print_step 4 "Checking Python installation"
    check_python
    
    print_step 5 "Setting up permissions and checking FIO"
    setup_permissions "$arch"
    check_fio "$arch"
    
    print_step 6 "Testing installation"
    if test_installation; then
        print_success "Installation test completed successfully"
    else
        print_warning "Installation test had issues, but you can still try running the application"
    fi
    
    echo
    print_colored "$GREEN$BOLD" "🎉 Installation Complete!"
    echo
    print_colored "$BLUE" "To run the QLab Disk Tester:"
    print_colored "$BLUE" "  python3 qlab_disk_tester.py"
    echo
    print_colored "$BLUE" "Or from anywhere:"
    print_colored "$BLUE" "  cd $(pwd) && python3 qlab_disk_tester.py"
    echo
    
    # Optional desktop shortcut
    create_shortcut
    
    print_colored "$GREEN" "Ready to test your storage devices! 🚀"
}

# Run the installer
main "$@"
