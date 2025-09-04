#!/bin/zsh
# Start Diskbench Bridge.command — Double-clickable macOS launcher
# Version 1.1 – 04.09.2025
#
# What it does:
# - Ensures a sane PATH for Homebrew
# - Optionally activates ./.venv if present
# - Starts the Bridge Server and shows logs in this Terminal window
# - Opens http://localhost:8765 automatically
#
# How to use:
# - Double-click this file in Finder, or run in Terminal: ./Start\ Diskbench\ Bridge.command

set -euo pipefail

# Make Homebrew and vendored FIO binaries available even from GUI-launched Terminal sessions
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Resolve repo root based on this file's location
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
cd "$REPO_ROOT"

# Prepend vendored FIO to PATH if present (offline use)
MACHINE_ARCH=$(uname -m)
if [[ "$MACHINE_ARCH" == arm64* || "$MACHINE_ARCH" == *aarch64* ]]; then
  ARCH_DIR=arm64
else
  ARCH_DIR=x86_64
fi
VENDOR_FIO_DIR="$REPO_ROOT/vendor/fio/macos/$ARCH_DIR"
if [[ -d "$VENDOR_FIO_DIR" ]]; then
  export PATH="$VENDOR_FIO_DIR:$PATH"
fi

# Activate venv if it exists
if [[ -d "$REPO_ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.venv/bin/activate" || true
fi

URL="http://localhost:8765/"
PY="python3"

# Prefer PyInstaller-built bridge if available
BIN_ONEDIR="$REPO_ROOT/dist/diskbench-bridge/diskbench-bridge"
BIN_ONEFILE="$REPO_ROOT/dist/diskbench-bridge"

echo "Starting Diskbench Bridge Server..."
if [[ -x "$BIN_ONEDIR" ]]; then
  "$BIN_ONEDIR" &
  SERVER_PID=$!
elif [[ -x "$BIN_ONEFILE" && ! -d "$BIN_ONEFILE" ]]; then
  "$BIN_ONEFILE" &
  SERVER_PID=$!
else
  # Start in background so we can open the browser; keep logs in this window
  "$PY" bridge-server/server.py &
  SERVER_PID=$!
fi

echo "Server PID: $SERVER_PID"

# Try to detect readiness (best-effort, up to ~5s)
READY=0
if command -v curl >/dev/null 2>&1; then
  for _ in {1..25}; do
    if curl -sSf "$URL" >/dev/null 2>&1; then
      READY=1
      break
    fi
    sleep 0.2
  done
fi

# Open browser (even if not yet READY; page will connect once available)
if command -v open >/dev/null 2>&1; then
  open "$URL" || true
fi

if [[ "$READY" -eq 1 ]]; then
  echo "Bridge Server is up at $URL"
else
  echo "Launching browser; server is starting up..."
fi

cleanup() {
  echo
  echo "Stopping server (PID $SERVER_PID)..."
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup INT TERM

# Keep this Terminal window attached to the server's lifecycle
wait "$SERVER_PID" || EXIT=$?
exit "${EXIT:-0}"

