#!/usr/bin/env bash
# start.sh — Dev launcher for Diskbench Bridge Server (CLI-friendly)
# Version 1.1 – 04.09.2025
# Usage:
#   ./scripts/start.sh [--no-browser] [--no-venv]
#   bash scripts/start.sh ...
#
# Behavior:
# - Prepends vendored FIO to PATH if present
# - Activates ./.venv if present (unless --no-venv)
# - Prefers PyInstaller build at dist/diskbench-bridge (if present)
# - Falls back to python bridge-server/server.py
# - Opens http://localhost:8765 unless --no-browser

set -euo pipefail

# Resolve repo root (directory containing this script is scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

NO_BROWSER=0
NO_VENV=0

for arg in "$@"; do
  case "$arg" in
    --no-browser)
      NO_BROWSER=1
      shift
      ;;
    --no-venv)
      NO_VENV=1
      shift
      ;;
    -h|--help)
      grep -E '^(# (Usage|Behavior|Notes):|#   |# - )' "$0" | sed -E 's/^# ?//'
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Use --help for usage." >&2
      exit 2
      ;;
  esac
done

# Environment: prepend vendored FIO (offline support)
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

# Activate venv if present
if [[ "$NO_VENV" -eq 0 && -d "$REPO_ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.venv/bin/activate"
fi

# Start the server
URL="http://localhost:8765/"
PY=python3

# Prefer PyInstaller-built bridge if available
BIN_ONEDIR="$REPO_ROOT/dist/diskbench-bridge/diskbench-bridge"
BIN_ONEFILE="$REPO_ROOT/dist/diskbench-bridge"

echo "Starting Diskbench Bridge Server..."
if [[ -x "$BIN_ONEDIR" ]]; then
  "$BIN_ONEDIR" >/tmp/diskbench_bridge_server.log 2>&1 &
  SERVER_PID=$!
elif [[ -x "$BIN_ONEFILE" && ! -d "$BIN_ONEFILE" ]]; then
  "$BIN_ONEFILE" >/tmp/diskbench_bridge_server.log 2>&1 &
  SERVER_PID=$!
else
  "$PY" bridge-server/server.py >/tmp/diskbench_bridge_server.log 2>&1 &
  SERVER_PID=$!
fi

echo "Server PID: $SERVER_PID (logs: /tmp/diskbench_bridge_server.log)"

# Wait for server to come up (max ~5s)
ATTEMPTS=25
SLEEP=0.2
READY=0
for _ in $(seq 1 $ATTEMPTS); do
  if curl -sSf "$URL" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep "$SLEEP"
done

if [[ "$READY" -eq 1 ]]; then
  echo "Bridge Server is up at $URL"
  if [[ "$NO_BROWSER" -eq 0 ]]; then
    # macOS: open in default browser
    if command -v open >/dev/null 2>&1; then
      open "$URL" || true
    fi
  fi
else
  echo "Warning: Bridge Server did not become ready yet. It may still be starting."
  echo "Check logs: tail -f /tmp/diskbench_bridge_server.log"
fi

# Foreground wait with cleanup on Ctrl-C
cleanup() {
  echo
  echo "Stopping server (PID $SERVER_PID)..."
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup INT TERM

# If the process exits early, propagate its exit code
wait "$SERVER_PID" || EXIT=$?
exit "${EXIT:-0}"

