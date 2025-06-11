#!/bin/bash
set -e

echo "📦 Creating QLab Disk Tester Standalone Package..."

# Package info
PACKAGE_NAME="qlabdisktester-standalone"
VERSION="1.0.0"
DATE=$(date +%Y%m%d)
PACKAGE_FILE="${PACKAGE_NAME}-v${VERSION}-${DATE}.tar.gz"

# Files to include in standalone package
INCLUDE_FILES=(
    "qlab_disk_tester.py"
    "install.sh"
    "test_standalone.py"
    "README.md"
    "requirements.txt"
    "lib/"
    "bin/fio-apple-silicon"
)

# Create temporary package directory
TEMP_DIR="/tmp/${PACKAGE_NAME}"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

echo "📋 Including files in package:"
for file in "${INCLUDE_FILES[@]}"; do
    if [[ -e "$file" ]]; then
        echo "  ✅ $file"
        cp -r "$file" "$TEMP_DIR/"
    else
        echo "  ⚠️  $file (not found, skipping)"
    fi
done

# Make scripts executable
chmod +x "$TEMP_DIR/install.sh"
chmod +x "$TEMP_DIR/test_standalone.py" 
chmod +x "$TEMP_DIR/bin/"*

# Create package info
cat > "$TEMP_DIR/PACKAGE_INFO.txt" << EOF
QLab Disk Performance Tester - Standalone Edition
Version: ${VERSION}
Build Date: $(date)
Architecture: Apple Silicon Exclusive (M1/M2/M3)

CONTENTS:
- qlab_disk_tester.py     : Main application
- install.sh              : Installation script
- test_standalone.py      : Standalone verification
- README.md               : Complete documentation
- lib/                    : Python modules (standard library only)
- bin/fio-apple-silicon   : fio binary for Apple Silicon

FEATURES:
✅ Zero external dependencies
✅ No pip/homebrew required
✅ Works on fresh macOS installs
✅ Apple Silicon exclusive (M1/M2/M3)
✅ Live SSD temperature monitoring
✅ Realistic QLab ProRes 422 testing
✅ fio-based disk benchmarking

INSTALLATION:
1. Extract package
2. cd ${PACKAGE_NAME}
3. ./install.sh
4. python3 qlab_disk_tester.py

For technical support and updates:
Made for QLab Professionals
EOF

# Create the package
echo ""
echo "🗂️  Creating package archive..."
cd /tmp
tar -czf "$PACKAGE_FILE" "$PACKAGE_NAME"

# Move to original directory
mv "$PACKAGE_FILE" "$OLDPWD/"

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Package created: $PACKAGE_FILE"
echo ""
echo "📊 Package contents:"
tar -tzf "$PACKAGE_FILE" | head -20
if [[ $(tar -tzf "$PACKAGE_FILE" | wc -l) -gt 20 ]]; then
    echo "   ... and $(( $(tar -tzf "$PACKAGE_FILE" | wc -l) - 20 )) more files"
fi

echo ""
echo "📋 Package info:"
echo "  Size: $(du -h "$PACKAGE_FILE" | cut -f1)"
echo "  Files: $(tar -tzf "$PACKAGE_FILE" | wc -l)"
echo ""
echo "🚀 Ready for distribution!"
echo "   Users can extract and run ./install.sh on any macOS system"