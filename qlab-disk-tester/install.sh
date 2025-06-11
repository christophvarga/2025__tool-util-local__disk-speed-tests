#!/bin/bash
set -e

echo "🚀 Installing QLab Disk Tester (Standalone Package)..."

# Verify Apple Silicon Architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# Only Apple Silicon supported
if [[ "$ARCH" != "arm64" ]]; then
    echo "❌ Unsupported architecture: $ARCH"
    echo "ℹ️  This tool requires Apple Silicon (M1/M2/M3) Macs only"
    echo "   Current architecture: $ARCH (not supported)"
    exit 1
fi

FIO_SOURCE="bin/fio-apple-silicon"
echo "✅ Apple Silicon detected - using bundled fio binary"

# Check if binary exists
if [[ ! -f "$FIO_SOURCE" ]]; then
    echo "❌ fio binary not found: $FIO_SOURCE"
    echo ""
    echo "📦 STANDALONE PACKAGE SETUP REQUIRED:"
        echo "1. Download fio binary for Apple Silicon"
        echo "2. Place it as: $FIO_SOURCE"
        echo "3. Make it executable: chmod +x $FIO_SOURCE"
        echo ""
        echo "💡 This package is designed to run without external dependencies"
        echo "   No Homebrew, pip, or internet connection required!"
    exit 1
fi

# Make bundled binary executable
chmod +x "$FIO_SOURCE"
echo "✅ fio binary is ready: $FIO_SOURCE"

# Verify Python 3 is available (standard on macOS)
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    echo "ℹ️  Python 3 is required and should be pre-installed on macOS"
    echo "   If missing, install from: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# No virtual environment or pip dependencies needed!
echo "✅ Standalone package ready!"
echo ""
echo "🎯 USAGE:"
echo "  python3 qlab_disk_tester.py"
echo ""
echo "📋 FEATURES:"
echo "  ✅ No external dependencies (uses Python standard library only)"
echo "  ✅ No pip/homebrew required"
echo "  ✅ Works on fresh macOS installs"
echo "  ✅ Apple Silicon exclusive (M1/M2/M3)"
echo "  ✅ Live SSD temperature monitoring"
echo "  ✅ Realistic QLab ProRes 422 testing"
echo ""
echo "🔧 TECHNICAL:"
echo "  • Uses bundled fio binary: $FIO_SOURCE"
echo "  • Python standard library only"
echo "  • macOS-native temperature estimation"
echo "  • Professional QLab workflow simulation"
echo "  • Apple Silicon exclusive (M1/M2/M3 Macs)"