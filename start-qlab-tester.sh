#!/bin/bash

# QLab Disk Performance Tester - Complete System Launcher
# This script starts the bridge server which serves the web GUI

echo "🚀 Starting QLab Disk Performance Tester"
echo "=========================================="
echo

# Check if running with sudo (required for disk testing and dependency installation)
if [ "$EUID" -ne 0 ]; then
    echo "🔐 Administrator privileges required for:"
    echo "   • Direct disk performance testing"
    echo "   • Temperature monitoring via smartctl (optional)"
    echo "   • Installing missing dependencies (FIO)"
    echo
    echo "💡 Please run with: sudo ./start-qlab-tester.sh"
    exit 1
fi

echo "✅ Administrator privileges confirmed"
echo

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "bridge-server/server.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Start the bridge server
echo "🌉 Starting bridge server..."
echo "   This will:"
echo "   • Start the HTTP bridge server on localhost:8765"
echo "   • Serve the web GUI interface"
echo "   • Bridge communication with the diskbench helper binary"
echo
echo "📱 Once started, open your web browser and go to:"
echo "   http://localhost:8765"
echo
echo "⚠️  The setup wizard will guide you through FIO installation if needed"
echo
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo

# Change to bridge-server directory and start server
cd bridge-server

# Check if required files exist
if [ ! -f "server.py" ]; then
    echo "❌ Bridge server not found"
    exit 1
fi

# Start the server
python3 server.py
