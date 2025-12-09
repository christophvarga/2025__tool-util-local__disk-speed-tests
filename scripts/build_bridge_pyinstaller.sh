#!/usr/bin/env bash
# Build the Bridge Server as a self-contained binary via PyInstaller
# Version 1.0 – 04.09.2025
#
# Usage:
#   bash scripts/build_bridge_pyinstaller.sh [--onefile|--onedir]
#
# Outputs:
#   dist/diskbench-bridge            (onefile binary)
#   or
#   dist/diskbench-bridge/           (onedir folder with binary inside)
#
# Notes:
# - Includes the 'diskbench' package and 'web-gui' assets so the binary runs offline.
# - Apple Silicon (arm64) is the primary target.
# - Requires pyinstaller installed in your environment.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Ensure vendored FIO exists; if missing, try to vend a local fio binary (Homebrew) for offline use
MACHINE_ARCH="$(uname -m)"
if [[ "$MACHINE_ARCH" == arm64* || "$MACHINE_ARCH" == *aarch64* ]]; then
  ARCH_DIR=arm64
else
  ARCH_DIR=x86_64
fi
VENDOR_DIR="$REPO_ROOT/vendor/fio/macos/$ARCH_DIR"
FIO_VENDOR_BIN="$VENDOR_DIR/fio"
if [[ ! -x "$FIO_VENDOR_BIN" ]]; then
  # Try to pull from common locations (Homebrew)
  if command -v fio >/dev/null 2>&1; then
    mkdir -p "$VENDOR_DIR"
    cp "$(command -v fio)" "$FIO_VENDOR_BIN"
    chmod +x "$FIO_VENDOR_BIN"
    echo "Vendored fio created at: $FIO_VENDOR_BIN"
  else
    echo "Warning: vendored fio not found and no system fio available."
    echo "Place a macOS fio binary at $FIO_VENDOR_BIN for fully offline operation."
  fi
fi

MODE="onefile"
if [[ "${1-}" == "--onedir" ]]; then
  MODE="onedir"
fi

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "Error: pyinstaller not found. Install it first, e.g.:" >&2
  echo "  python3 -m pip install pyinstaller" >&2
  exit 1
fi

NAME="diskbench-bridge"
ENTRY="bridge-server/server.py"

COMMON_ARGS=(
  --clean
  --noconfirm
  --name "$NAME"
  --add-data "web-gui:web-gui"
  --add-data "diskbench:diskbench"
  --add-data "vendor/fio:vendor/fio"
  --collect-submodules "diskbench"
  --hidden-import "diskbench"
)

if [[ "$MODE" == "onefile" ]]; then
  echo "Building onefile binary..."
  pyinstaller "${COMMON_ARGS[@]}" --onefile "$ENTRY"
else
  echo "Building onedir bundle..."
  pyinstaller "${COMMON_ARGS[@]}" --onedir "$ENTRY"
fi

echo "Build complete. Artifacts in ./dist/"

