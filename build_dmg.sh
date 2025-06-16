#!/bin/bash
#
# QLab Disk Performance Tester - DMG Builder
# Creates a professional macOS DMG package with all components
#

set -e

# Configuration
APP_NAME="QLab Disk Performance Tester"
DMG_NAME="qlab-disk-tester"
VERSION="1.0.0"
BUILD_DIR="build"
DMG_DIR="$BUILD_DIR/dmg"
DIST_DIR="dist"

echo "🚀 Building QLab Disk Performance Tester DMG v$VERSION"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DMG_DIR" "$DIST_DIR"

# Create app bundle structure
echo "📦 Creating application bundle..."
APP_BUNDLE="$DMG_DIR/$APP_NAME.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"
mkdir -p "$APP_BUNDLE/Contents/Resources/diskbench"
mkdir -p "$APP_BUNDLE/Contents/Resources/bridge-server"
mkdir -p "$APP_BUNDLE/Contents/Resources/web-gui"
mkdir -p "$APP_BUNDLE/Contents/Resources/fio-backup"

# Copy Info.plist
echo "📋 Creating Info.plist..."
cat > "$APP_BUNDLE/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>qlab-disk-tester</string>
    <key>CFBundleIdentifier</key>
    <string>com.qlab.disk-tester</string>
    <key>CFBundleName</key>
    <string>QLab Disk Performance Tester</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

# Copy diskbench components
echo "🔧 Copying diskbench helper binary..."
cp -r diskbench/* "$APP_BUNDLE/Contents/Resources/diskbench/"

# Copy bridge server
echo "🌉 Copying bridge server..."
cp -r bridge-server/* "$APP_BUNDLE/Contents/Resources/bridge-server/"

# Copy web GUI
echo "🖥️ Copying web GUI..."
cp -r web-gui/* "$APP_BUNDLE/Contents/Resources/web-gui/"

# Copy FIO backup (if exists)
echo "⚙️ Copying FIO backup..."
if [ -d "fio-3.37" ]; then
    cp -r fio-3.37/* "$APP_BUNDLE/Contents/Resources/fio-backup/"
fi

# Copy icon (if exists)
if [ -f "icon.png" ]; then
    echo "🎨 Copying application icon..."
    cp icon.png "$APP_BUNDLE/Contents/Resources/icon.png"
fi

# Create main launcher script
echo "🚀 Creating launcher script..."
cat > "$APP_BUNDLE/Contents/MacOS/qlab-disk-tester" << 'EOF'
#!/bin/bash
#
# QLab Disk Performance Tester Launcher
# Starts the bridge server and opens web GUI
#

# Get the directory containing this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR="$DIR/../Resources"

# Setup paths
export PATH="$RESOURCES_DIR/diskbench:$PATH"
export PYTHONPATH="$RESOURCES_DIR/diskbench:$PYTHONPATH"

# Function to check if Homebrew FIO is available
check_fio() {
    if command -v fio >/dev/null 2>&1; then
        echo "✅ FIO found in PATH: $(which fio)"
        return 0
    elif [ -x "/opt/homebrew/bin/fio" ]; then
        echo "✅ Homebrew FIO found: /opt/homebrew/bin/fio"
        return 0
    elif [ -x "/usr/local/bin/fio" ]; then
        echo "✅ Homebrew FIO found: /usr/local/bin/fio"
        return 0
    else
        echo "⚠️ FIO not found in Homebrew paths"
        return 1
    fi
}

# Function to start bridge server
start_bridge_server() {
    echo "🌉 Starting bridge server..."
    cd "$RESOURCES_DIR/bridge-server"
    
    # Kill any existing bridge server
    pkill -f "python.*server.py" 2>/dev/null || true
    sleep 1
    
    # Start bridge server in background
    python3 server.py > /tmp/qlab-bridge-server.log 2>&1 &
    BRIDGE_PID=$!
    
    # Wait for server to start
    echo "⏳ Waiting for bridge server to start..."
    for i in {1..10}; do
        if curl -s http://localhost:8080/api/status >/dev/null 2>&1; then
            echo "✅ Bridge server started successfully (PID: $BRIDGE_PID)"
            return 0
        fi
        sleep 1
    done
    
    echo "❌ Bridge server failed to start"
    return 1
}

# Function to open web GUI
open_web_gui() {
    echo "🖥️ Opening web GUI..."
    
    # Try to open in default browser
    if command -v open >/dev/null 2>&1; then
        open "http://localhost:8080"
    else
        echo "📋 Please open http://localhost:8080 in your web browser"
    fi
}

# Function to show installation dialog
show_installation_dialog() {
    local title="QLab Disk Performance Tester"
    local message="For optimal performance, please install FIO via Homebrew:

1. Install Homebrew (if not already installed):
   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"

2. Install FIO:
   brew install fio

3. Restart this application

The application will work without FIO but with limited performance testing capabilities."
    
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "display dialog \"$message\" with title \"$title\" buttons {\"Continue Anyway\", \"Install FIO\"} default button \"Install FIO\""
        local result=$?
        if [ $result -eq 0 ]; then
            # User clicked "Install FIO"
            if command -v open >/dev/null 2>&1; then
                open "https://brew.sh/"
            fi
        fi
    else
        echo ""
        echo "=================================================="
        echo "$title"
        echo "=================================================="
        echo "$message"
        echo "=================================================="
        echo ""
    fi
}

# Main execution
echo "🚀 Starting QLab Disk Performance Tester..."

# Check FIO availability
if check_fio; then
    echo "✅ FIO is available - full functionality enabled"
else
    echo "⚠️ FIO not found - showing installation guidance"
    show_installation_dialog
fi

# Start bridge server
if start_bridge_server; then
    # Open web GUI
    open_web_gui
    
    echo ""
    echo "✅ QLab Disk Performance Tester is running!"
    echo "📱 Web GUI: http://localhost:8080"
    echo "📝 Bridge server log: /tmp/qlab-bridge-server.log"
    echo ""
    echo "To stop the application, close this terminal or press Ctrl+C"
    
    # Keep the launcher running
    trap 'echo "🛑 Stopping bridge server..."; pkill -f "python.*server.py"; exit 0' INT TERM
    
    # Wait for bridge server process
    wait $BRIDGE_PID
else
    echo "❌ Failed to start bridge server"
    exit 1
fi
EOF

# Make launcher executable
chmod +x "$APP_BUNDLE/Contents/MacOS/qlab-disk-tester"

# Create README and documentation
echo "📚 Creating documentation..."
cat > "$DMG_DIR/README.txt" << 'EOF'
QLab Disk Performance Tester v1.0.0
====================================

Professional disk performance testing tool optimized for QLab audio/video applications.

QUICK START:
1. Install FIO for best performance:
   - Install Homebrew: https://brew.sh/
   - Run: brew install fio
   
2. Double-click "QLab Disk Performance Tester.app"

3. The web interface will open automatically at http://localhost:8080

FEATURES:
✅ Professional FIO-based disk testing
✅ QLab-optimized test patterns (4K ProRes HQ simulation)
✅ Clean web-based interface
✅ Detailed performance analysis
✅ macOS-native integration
✅ Python fallback when FIO unavailable

ARCHITECTURE:
- Sandboxed Web GUI for user interface
- Unsandboxed Helper Binary for FIO execution
- Bridge Server for secure communication
- Professional FIO engine for accurate testing

SYSTEM REQUIREMENTS:
- macOS 10.15 or later
- Python 3.6 or later (usually pre-installed)
- Homebrew FIO (recommended) or bundled fallback

TROUBLESHOOTING:
- If FIO tests fail: Install via "brew install fio"
- If bridge server won't start: Check Python installation
- If web GUI won't open: Manually visit http://localhost:8080

For support: https://github.com/your-repo/qlab-disk-tester
EOF

cat > "$DMG_DIR/INSTALL_FIO.command" << 'EOF'
#!/bin/bash
#
# FIO Installation Helper
# Automatically installs Homebrew and FIO
#

echo "🍺 QLab Disk Tester - FIO Installation Helper"
echo "=============================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew >/dev/null 2>&1; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for current session
    if [ -d "/opt/homebrew" ]; then
        export PATH="/opt/homebrew/bin:$PATH"
    elif [ -d "/usr/local" ]; then
        export PATH="/usr/local/bin:$PATH"
    fi
else
    echo "✅ Homebrew is already installed"
fi

# Install FIO
echo "⚙️ Installing FIO..."
if brew install fio; then
    echo ""
    echo "✅ FIO installation completed successfully!"
    echo ""
    echo "You can now:"
    echo "1. Close this window"
    echo "2. Restart QLab Disk Performance Tester"
    echo "3. Enjoy full FIO-powered disk testing!"
    echo ""
else
    echo ""
    echo "❌ FIO installation failed"
    echo ""
    echo "Please try manual installation:"
    echo "1. Open Terminal"
    echo "2. Run: brew install fio"
    echo ""
fi

echo "Press any key to close this window..."
read -n 1
EOF

chmod +x "$DMG_DIR/INSTALL_FIO.command"

# Create symlink to Applications
echo "🔗 Creating Applications symlink..."
ln -s /Applications "$DMG_DIR/Applications"

# Create DMG
echo "💿 Creating DMG..."
DMG_PATH="$DIST_DIR/$DMG_NAME-v$VERSION.dmg"

# Create temporary DMG
hdiutil create -size 200m -fs HFS+ -volname "$APP_NAME" -srcfolder "$DMG_DIR" "$DMG_PATH.tmp.dmg"

# Convert to compressed DMG
hdiutil convert "$DMG_PATH.tmp.dmg" -format UDZO -o "$DMG_PATH"
rm "$DMG_PATH.tmp.dmg"

# Calculate size
DMG_SIZE=$(du -h "$DMG_PATH" | cut -f1)

echo ""
echo "✅ DMG created successfully!"
echo "📦 File: $DMG_PATH"
echo "📏 Size: $DMG_SIZE"
echo ""
echo "🎯 Installation Instructions:"
echo "1. Mount the DMG"
echo "2. Drag 'QLab Disk Performance Tester.app' to Applications folder"
echo "3. Run 'INSTALL_FIO.command' for optimal performance"
echo "4. Launch the app from Applications folder"
echo ""
echo "🏗️ Architecture Features:"
echo "✅ Prioritizes Homebrew FIO for best compatibility"
echo "✅ Falls back to bundled FIO if needed"
echo "✅ Python fallback for basic testing"
echo "✅ Clean web GUI with bridge server communication"
echo "✅ Professional FIO test patterns optimized for QLab"
echo ""
