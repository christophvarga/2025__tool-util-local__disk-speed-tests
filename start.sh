#!/usr/bin/env bash
# QLab Disk Performance Tester - Start Script (deprecated wrapper)
# Version 1.1 - 04.09.2025
# This script is kept for backward compatibility and delegates to the unified launchers.

set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$SCRIPT_DIR"

# Prefer the double-clickable macOS launcher for end users
COMMAND_FILE="$REPO_ROOT/Start Diskbench Bridge.command"
DEV_SCRIPT="$REPO_ROOT/scripts/start.sh"

if [[ -x "$COMMAND_FILE" ]]; then
  echo "Delegating to: $COMMAND_FILE"
  exec "$COMMAND_FILE"
fi

if [[ -x "$DEV_SCRIPT" ]]; then
  echo "Delegating to: $DEV_SCRIPT"
  exec bash "$DEV_SCRIPT"
fi

echo "Error: No launcher found. Expected either 'Start Diskbench Bridge.command' or 'scripts/start.sh'." >&2
exit 1
