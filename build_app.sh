#!/bin/bash

# QLab Disk Performance Tester - .app Bundle Builder
# Creates a standalone macOS application bundle

set -e

# Colors for output
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
    print_colored "$BLUE$BOLD" "    QLab Disk Tester - .app Builder"
    print_colored "$BLUE$BOLD" "============================================"
    echo
}

# Check if we're on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_colored "$RED" "❌ This script must be run on macOS"
        exit 1
    fi
    print_colored "$GREEN" "✅ Running on macOS"
}

# Check Python version
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_colored "$RED" "❌ Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    print_colored "$GREEN" "✅ Python $python_version found"
}

# Install dependencies
install_dependencies() {
    print_colored "$BLUE" "Installing dependencies..."
    
    # Check if virtual environment exists
    if [[ ! -d ".venv" ]]; then
        print_colored "$BLUE" "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_colored "$GREEN" "✅ Dependencies installed"
}

# Clean previous builds
clean_build() {
    print_colored "$BLUE" "Cleaning previous builds..."
    
    rm -rf build/
    rm -rf dist/
    rm -rf __pycache__/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_colored "$GREEN" "✅ Build directory cleaned"
}

# Build the .app bundle
build_app() {
    print_colored "$BLUE" "Building .app bundle..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Run PyInstaller
    pyinstaller qlab_disk_tester.spec --clean --noconfirm
    
    if [[ -d "dist/QLab Disk Performance Tester.app" ]]; then
        print_colored "$GREEN" "✅ .app bundle created successfully"
    else
        print_colored "$RED" "❌ Failed to create .app bundle"
        exit 1
    fi
}

# Test the app
test_app() {
    print_colored "$BLUE" "Testing .app bundle..."
    
    local app_path="dist/QLab Disk Performance Tester.app"
    
    if [[ -d "$app_path" ]]; then
        # Check if app can be opened
        print_colored "$BLUE" "Checking app structure..."
        
        # Verify executable exists
        if [[ -f "$app_path/Contents/MacOS/QLab Disk Performance Tester" ]]; then
            print_colored "$GREEN" "✅ Executable found"
        else
            print_colored "$RED" "❌ Executable not found"
            return 1
        fi
        
        # Check Info.plist
        if [[ -f "$app_path/Contents/Info.plist" ]]; then
            print_colored "$GREEN" "✅ Info.plist found"
        else
            print_colored "$RED" "❌ Info.plist not found"
            return 1
        fi
        
        print_colored "$GREEN" "✅ App bundle structure is valid"
        
        # Get app size
        local app_size=$(du -sh "$app_path" | cut -f1)
        print_colored "$BLUE" "App bundle size: $app_size"
        
    else
        print_colored "$RED" "❌ App bundle not found"
        return 1
    fi
}

# Create distribution package
create_distribution() {
    print_colored "$BLUE" "Creating distribution package..."
    
    local app_path="dist/QLab Disk Performance Tester.app"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local package_name="QLab-Disk-Tester_v1.0_$timestamp"
    
    # Create distribution directory
    mkdir -p "dist/$package_name"
    
    # Copy app bundle
    cp -R "$app_path" "dist/$package_name/"
    
    # Create README for distribution
    cat > "dist/$package_name/README.txt" << 'EOF'
QLab Disk Performance Tester v1.0
==================================

Installation:
1. Copy "QLab Disk Performance Tester.app" to your Applications folder
2. Double-click to run

Requirements:
- macOS 10.14 (Mojave) or later
- No additional software required

Usage:
1. Select a drive to test
2. Choose a test profile
3. Click "Start Test"
4. Review results

For support, visit: https://qlab.app

© 2025 QLab Tools
EOF
    
    # Create DMG (if hdiutil is available)
    if command -v hdiutil &> /dev/null; then
        print_colored "$BLUE" "Creating DMG file..."
        
        # Create temporary DMG
        hdiutil create -volname "QLab Disk Tester" -srcfolder "dist/$package_name" -ov -format UDZO "dist/$package_name.dmg"
        
        if [[ -f "dist/$package_name.dmg" ]]; then
            print_colored "$GREEN" "✅ DMG created: dist/$package_name.dmg"
        fi
    fi
    
    # Create ZIP archive
    cd dist
    zip -r "$package_name.zip" "$package_name" >/dev/null
    cd ..
    
    print_colored "$GREEN" "✅ Distribution package created: dist/$package_name.zip"
}

# Show final results
show_results() {
    echo
    print_colored "$GREEN$BOLD" "🎉 Build completed successfully!"
    echo
    print_colored "$BLUE" "Files created:"
    print_colored "$BLUE" "• dist/QLab Disk Performance Tester.app"
    
    if [[ -f dist/*.dmg ]]; then
        print_colored "$BLUE" "• dist/*.dmg (Disk Image)"
    fi
    
    if [[ -f dist/*.zip ]]; then
        print_colored "$BLUE" "• dist/*.zip (Distribution Package)"
    fi
    
    echo
    print_colored "$BLUE" "To test the app:"
    print_colored "$BLUE" "open 'dist/QLab Disk Performance Tester.app'"
    echo
    print_colored "$GREEN" "Ready for distribution! 📦"
}

# Main function
main() {
    print_header
    
    check_macos
    check_python
    install_dependencies
    clean_build
    build_app
    test_app
    create_distribution
    show_results
}

# Run the script
main "$@"
