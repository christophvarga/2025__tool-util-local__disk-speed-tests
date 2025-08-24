#!/bin/bash
# QLab Disk Performance Tester - Start Script
# Version 1.0 - Created 2025-07-29
# This script handles the complete setup and launch of the disk tester

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BRIDGE_PORT=8765
WEB_URL="http://localhost:${BRIDGE_PORT}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="${SCRIPT_DIR}/.venv"
BRIDGE_SERVER="${SCRIPT_DIR}/bridge-server/server.py"
PID_FILE="${SCRIPT_DIR}/.bridge_server.pid"

# Functions
print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    QLab Disk Performance Tester v1.0      ║${NC}"
    echo -e "${BLUE}║         Easy Setup & Launch Script        ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
    echo ""
}

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

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This tool is designed for macOS only"
        exit 1
    fi
    print_success "Running on macOS"
}

# Detect processor architecture
detect_architecture() {
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        print_status "Detected Apple Silicon (M1/M2/M3)"
        HOMEBREW_PREFIX="/opt/homebrew"
    else
        print_status "Detected Intel processor"
        HOMEBREW_PREFIX="/usr/local"
    fi
}

# Check for Homebrew
check_homebrew() {
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew not found!"
        print_status "Please install Homebrew from https://brew.sh"
        print_status "Run: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    print_success "Homebrew found at $(which brew)"
}

# Check for FIO
check_fio() {
    # Check multiple locations for FIO
    local fio_paths=(
        "/usr/local/bin/fio-nosmh"
        "${HOMEBREW_PREFIX}/bin/fio"
        "/usr/local/bin/fio"
        "$(which fio 2>/dev/null || true)"
    )
    
    local fio_found=false
    for fio_path in "${fio_paths[@]}"; do
        if [[ -x "$fio_path" ]]; then
            print_success "FIO found at $fio_path"
            fio_found=true
            break
        fi
    done
    
    if [[ "$fio_found" == false ]]; then
        print_warning "FIO not found - Installing via Homebrew..."
        brew install fio
        if command -v fio &> /dev/null; then
            print_success "FIO installed successfully"
        else
            print_error "Failed to install FIO"
            exit 1
        fi
    fi
}

# Check Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found!"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION found"
    
    # Check if version is 3.7 or higher
    if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3,7) else 1)'; then
        print_error "Python 3.7 or higher required"
        exit 1
    fi
}

# Setup Python virtual environment
setup_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate venv
    source "${VENV_DIR}/bin/activate"
    
    # Install/upgrade pip
    pip install --upgrade pip --quiet
}

# Stop any running bridge server
stop_bridge_server() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping existing bridge server (PID: $pid)..."
            kill "$pid"
            sleep 2
        fi
        rm -f "$PID_FILE"
    fi
    
    # Also check for orphaned processes
    local orphaned_pids=$(lsof -ti:$BRIDGE_PORT 2>/dev/null || true)
    if [[ -n "$orphaned_pids" ]]; then
        print_warning "Found orphaned process on port $BRIDGE_PORT"
        for pid in $orphaned_pids; do
            kill "$pid" 2>/dev/null || true
        done
        sleep 2
    fi
}

# Start bridge server
start_bridge_server() {
    print_status "Starting bridge server..."
    
    # Start server in background
    cd "$SCRIPT_DIR"
    nohup python3 "$BRIDGE_SERVER" > bridge-server.log 2>&1 &
    local server_pid=$!
    echo $server_pid > "$PID_FILE"
    
    # Wait for server to start
    local max_attempts=30
    local attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s "http://localhost:${BRIDGE_PORT}/api/status" > /dev/null 2>&1; then
            print_success "Bridge server started (PID: $server_pid)"
            return 0
        fi
        sleep 1
        ((attempt++))
    done
    
    print_error "Bridge server failed to start"
    print_status "Check bridge-server.log for details"
    return 1
}

# Open web browser
open_browser() {
    print_status "Opening web browser..."
    
    # Wait a moment for server to fully initialize
    sleep 2
    
    # Open default browser
    if command -v open &> /dev/null; then
        open "$WEB_URL"
        print_success "Browser opened at $WEB_URL"
    else
        print_warning "Could not open browser automatically"
        print_status "Please open $WEB_URL in your browser"
    fi
}

# Main execution
main() {
    print_header
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Run checks
    print_status "Running system checks..."
    check_macos
    detect_architecture
    check_homebrew
    check_fio
    check_python
    
    # Setup environment
    print_status ""
    print_status "Setting up environment..."
    setup_venv
    
    # Stop any existing server
    stop_bridge_server
    
    # Start bridge server
    print_status ""
    if start_bridge_server; then
        # Open browser
        open_browser
        
        print_status ""
        print_success "QLab Disk Performance Tester is ready!"
        print_status "Web interface: $WEB_URL"
        print_status "Log file: bridge-server.log"
        print_status ""
        print_status "To stop the server, run: ./stop.sh"
        print_status "Or press Ctrl+C in this terminal"
        
        # Keep script running and monitor server
        print_status ""
        print_status "Server is running. Press Ctrl+C to stop..."
        
        # Trap Ctrl+C to cleanup
        trap 'print_status "Stopping server..."; stop_bridge_server; exit 0' INT
        
        # Monitor server
        while true; do
            if [[ -f "$PID_FILE" ]]; then
                local pid=$(cat "$PID_FILE")
                if ! kill -0 "$pid" 2>/dev/null; then
                    print_error "Bridge server stopped unexpectedly"
                    break
                fi
            else
                print_error "PID file missing"
                break
            fi
            sleep 5
        done
    else
        print_error "Failed to start disk tester"
        exit 1
    fi
}

# Run main function
main
