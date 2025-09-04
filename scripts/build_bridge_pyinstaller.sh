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

