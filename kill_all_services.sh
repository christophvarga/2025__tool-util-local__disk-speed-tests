#!/bin/bash

echo "🛑 Killing all QLab Disk Tester services..."

# Step 1: Kill by process patterns
echo "Killing bridge server processes..."
pkill -f "bridge-server/server.py"

echo "Killing diskbench processes..."
pkill -f "diskbench"
pkill -f "main.py --test"

echo "Killing FIO processes..."
pkill -f "fio"
pkill -f "fio-nosmh"

# Step 2: Force kill if needed
sleep 2
echo "Force killing any remaining processes..."
pkill -9 -f "bridge-server/server.py"
pkill -9 -f "diskbench"
pkill -9 -f "fio"

# Step 3: Kill processes using specific ports
echo "Killing processes on ports 8765 and 8080..."
if lsof -ti:8765 >/dev/null 2>&1; then
    lsof -ti:8765 | xargs kill -9 2>/dev/null || true
fi

if lsof -ti:8080 >/dev/null 2>&1; then
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
fi

# Step 4: Clean up temporary files (including root-owned files)
echo "Cleaning up temporary files..."
echo "Removing user-owned files..."
rm -rf /tmp/diskbench_* 2>/dev/null || true
rm -f /tmp/diskbench-test_*.json 2>/dev/null || true
rm -f /tmp/diskbench_bridge_state.json 2>/dev/null || true

echo "Checking for remaining diskbench files..."
REMAINING_FILES=$(ls /tmp/diskbench* 2>/dev/null | wc -l)
if [ "$REMAINING_FILES" -gt 0 ]; then
    echo "Found $REMAINING_FILES remaining files, checking ownership..."
    ls -la /tmp/diskbench* 2>/dev/null || true
    echo "Removing with sudo..."
    sudo rm -f /tmp/diskbench* 2>/dev/null || true
    echo "✅ Remaining files cleaned up"
else
    echo "✅ No remaining files found"
fi

# Also clean up any FIO working directories
echo "Cleaning up FIO working directories..."
sudo rm -rf /tmp/diskbench_qlab_* 2>/dev/null || true
sudo rm -rf /tmp/fio_* 2>/dev/null || true

# Step 5: Verify cleanup
echo "Verifying cleanup..."
REMAINING=$(ps aux | grep -E "(bridge-server|diskbench|fio)" | grep -v grep | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ All services stopped successfully!"
else
    echo "⚠️  Some processes may still be running:"
    ps aux | grep -E "(bridge-server|diskbench|fio)" | grep -v grep
fi

# Check ports
PORT_8765=$(lsof -ti:8765 2>/dev/null | wc -l)
PORT_8080=$(lsof -ti:8080 2>/dev/null | wc -l)

if [ "$PORT_8765" -eq 0 ] && [ "$PORT_8080" -eq 0 ]; then
    echo "✅ All ports are free!"
else
    echo "⚠️  Some ports may still be in use:"
    lsof -i :8765 2>/dev/null || true
    lsof -i :8080 2>/dev/null || true
fi

echo "🎉 Cleanup complete!"
