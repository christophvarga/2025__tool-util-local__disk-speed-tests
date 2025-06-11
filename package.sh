#!/bin/bash

# QLab Disk Tester Packaging Script
# Creates a distributable archive with all necessary files

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo
    print_colored "$BLUE$BOLD" "============================================"
    print_colored "$BLUE$BOLD" "    QLab Disk Tester - Package Creator"
    print_colored "$BLUE$BOLD" "============================================"
    echo
}

# Get version from progress.md or use timestamp
get_version() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    echo "v1.0_$timestamp"
}

# Create package
create_package() {
    local version=$(get_version)
    local package_name="qlab-disk-tester_$version"
    local temp_dir="temp_package"
    
    print_colored "$BLUE" "Creating package: $package_name"
    
    # Create temporary directory
    mkdir -p "$temp_dir/$package_name"
    
    # Copy essential files
    print_colored "$BLUE" "Copying core files..."
    cp qlab_disk_tester.py "$temp_dir/$package_name/"
    cp install.sh "$temp_dir/$package_name/"
    cp README.md "$temp_dir/$package_name/"
    
    # Copy lib directory
    if [[ -d "lib" ]]; then
        cp -r lib "$temp_dir/$package_name/"
        print_colored "$GREEN" "✅ Copied lib/ directory"
    else
        print_colored "$RED" "❌ lib/ directory not found"
        exit 1
    fi
    
    # Copy bin directory if it exists
    if [[ -d "bin" ]]; then
        cp -r bin "$temp_dir/$package_name/"
        print_colored "$GREEN" "✅ Copied bin/ directory with FIO binaries"
    else
        print_colored "$YELLOW" "⚠️  bin/ directory not found - creating empty one"
        mkdir -p "$temp_dir/$package_name/bin"
        echo "# Place FIO binaries here" > "$temp_dir/$package_name/bin/README.md"
        echo "# - fio-apple-silicon (for M1/M2/M3/M4 Macs)" >> "$temp_dir/$package_name/bin/README.md"
        echo "# - fio-intel (for Intel Macs)" >> "$temp_dir/$package_name/bin/README.md"
    fi
    
    # Copy results directory structure
    mkdir -p "$temp_dir/$package_name/results"
    echo "# Test results will be saved here" > "$temp_dir/$package_name/results/README.md"
    
    # Copy templates if they exist
    if [[ -d "templates" ]]; then
        cp -r templates "$temp_dir/$package_name/"
        print_colored "$GREEN" "✅ Copied templates/ directory"
    fi
    
    # Copy configuration files
    if [[ -f ".clinerules" ]]; then
        cp .clinerules "$temp_dir/$package_name/"
        print_colored "$GREEN" "✅ Copied .clinerules"
    fi
    
    # Create installation instructions
    cat > "$temp_dir/$package_name/INSTALL.txt" << 'EOF'
QLab Disk Performance Tester - Installation Instructions
========================================================

Quick Start:
1. Extract this archive to your desired location
2. Open Terminal and navigate to the extracted folder
3. Run: bash install.sh
4. Follow the on-screen instructions

Manual Installation:
1. Ensure Python 3.7+ is installed (python3 --version)
2. Make scripts executable: chmod +x install.sh qlab_disk_tester.py
3. Set binary permissions: chmod +x bin/fio-*
4. Run the application: python3 qlab_disk_tester.py

Requirements:
- macOS 10.14+ (Mojave or later)
- Python 3.7+
- FIO binary (included) or system installation

For more detailed instructions, see README.md
EOF
    
    # Set executable permissions in package
    chmod +x "$temp_dir/$package_name/install.sh"
    chmod +x "$temp_dir/$package_name/qlab_disk_tester.py"
    
    # Set FIO binary permissions if they exist
    if [[ -f "$temp_dir/$package_name/bin/fio-apple-silicon" ]]; then
        chmod +x "$temp_dir/$package_name/bin/fio-apple-silicon"
    fi
    if [[ -f "$temp_dir/$package_name/bin/fio-intel" ]]; then
        chmod +x "$temp_dir/$package_name/bin/fio-intel"
    fi
    
    print_colored "$GREEN" "✅ Package structure created"
    
    # Create the archive
    print_colored "$BLUE" "Creating archive..."
    cd "$temp_dir"
    
    # Create both ZIP and TAR.GZ for maximum compatibility
    tar -czf "../${package_name}.tar.gz" "$package_name"
    zip -r "../${package_name}.zip" "$package_name" >/dev/null
    
    cd ..
    
    # Clean up temp directory
    rm -rf "$temp_dir"
    
    print_colored "$GREEN" "✅ Archives created:"
    print_colored "$GREEN" "   - ${package_name}.tar.gz"
    print_colored "$GREEN" "   - ${package_name}.zip"
    
    # Show package info
    local tar_size=$(du -h "${package_name}.tar.gz" | cut -f1)
    local zip_size=$(du -h "${package_name}.zip" | cut -f1)
    
    echo
    print_colored "$BLUE$BOLD" "Package Information:"
    print_colored "$BLUE" "Version: $version"
    print_colored "$BLUE" "TAR.GZ size: $tar_size"
    print_colored "$BLUE" "ZIP size: $zip_size"
    echo
}

# Verify files before packaging
verify_files() {
    local required_files=(
        "qlab_disk_tester.py"
        "lib/__init__.py"
        "lib/binary_manager.py"
        "lib/disk_detector.py"
        "lib/fio_engine.py"
        "lib/qlab_analyzer.py"
        "lib/report_generator.py"
        "README.md"
        "install.sh"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -eq 0 ]]; then
        print_colored "$GREEN" "✅ All required files present"
        return 0
    else
        print_colored "$RED" "❌ Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
}

# Show usage instructions
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --verify-only  Only verify files, don't create package"
    echo ""
    echo "This script creates distributable packages of the QLab Disk Tester."
    echo "It creates both .tar.gz and .zip archives for maximum compatibility."
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --verify-only)
                print_header
                verify_files
                exit $?
                ;;
            *)
                print_colored "$RED" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_header
    
    print_colored "$BLUE" "Verifying project files..."
    if ! verify_files; then
        print_colored "$RED" "Cannot create package due to missing files."
        exit 1
    fi
    
    create_package
    
    echo
    print_colored "$GREEN$BOLD" "🎉 Package creation complete!"
    echo
    print_colored "$BLUE" "To distribute:"
    print_colored "$BLUE" "1. Share the .tar.gz or .zip file"
    print_colored "$BLUE" "2. Recipients should extract and run: bash install.sh"
    echo
    print_colored "$GREEN" "Ready for distribution! 📦"
}

# Run the script
main "$@"
