#!/bin/bash
# QLab Disk Performance Tester - Stop Script
# Version 1.0 - Created 2025-07-29

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BRIDGE_PORT=8765
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="${SCRIPT_DIR}/.bridge_server.pid"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Stop bridge server
stop_bridge_server() {
    local stopped=false
    
    # Try PID file first
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping bridge server (PID: $pid)..."
            kill "$pid"
            stopped=true
            
            # Wait for process to stop
            local count=0
            while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                sleep 1
                ((count++))
            done
            
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Process didn't stop gracefully, forcing..."
                kill -9 "$pid" 2>/dev/null
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Check for processes on port
    local pids=$(lsof -ti:$BRIDGE_PORT 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        print_warning "Found process(es) on port $BRIDGE_PORT"
        for pid in $pids; do
            print_status "Stopping process $pid..."
            kill "$pid" 2>/dev/null || true
            stopped=true
        done
        sleep 2
    fi
    
    # Final check
    if lsof -ti:$BRIDGE_PORT >/dev/null 2>&1; then
        print_error "Failed to stop all processes on port $BRIDGE_PORT"
        return 1
    fi
    
    if [[ "$stopped" == true ]]; then
        print_success "Bridge server stopped"
    else
        print_status "No running bridge server found"
    fi
    
    return 0
}

# Stop any running FIO tests
stop_fio_tests() {
    local fio_pids=$(pgrep -f "fio.*diskbench" 2>/dev/null || true)
    if [[ -n "$fio_pids" ]]; then
        print_warning "Found running FIO tests"
        for pid in $fio_pids; do
            print_status "Stopping FIO test (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
        done
        sleep 2
        print_success "FIO tests stopped"
    fi
}

# Clean up temporary files
cleanup_temp_files() {
    print_status "Cleaning up temporary files..."
    
    # Remove test files
    find /tmp -name "diskbench_test_*.dat" -mtime +1 -delete 2>/dev/null || true
    find /Volumes -name "diskbench_test_*.dat" -mtime +1 -delete 2>/dev/null || true
    
    # Remove FIO log files
    find "${SCRIPT_DIR}" -name "*_bw.*.log" -delete 2>/dev/null || true
    find "${SCRIPT_DIR}" -name "*_lat.*.log" -delete 2>/dev/null || true
    
    print_success "Cleanup complete"
}

# Main execution
main() {
    echo -e "${BLUE}QLab Disk Performance Tester - Stop Script${NC}"
    echo ""
    
    # Stop bridge server
    stop_bridge_server
    
    # Stop any running tests
    stop_fio_tests
    
    # Optional cleanup
    read -p "Clean up temporary test files? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_temp_files
    fi
    
    echo ""
    print_success "All done!"
}

# Run main function
main
