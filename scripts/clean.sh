#!/usr/bin/env bash
set -euo pipefail
# Project cleanup script: removes build/test artifacts while preserving the latest test report.
# Safe: affects only files within this repository tree.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# 1) Python caches and coverage caches
find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
rm -rf .pytest_cache .mypy_cache .ruff_cache || true
rm -f .coverage coverage.xml || true

# 2) Build artifacts
rm -rf build dist ./*.egg-info || true

# 3) macOS cruft
find . -name ".DS_Store" -type f -delete || true

# 4) Preserve the latest test report, remove older ones
REPORTS_DIR="89_output/test_reports"
if [ -d "$REPORTS_DIR" ]; then
  latest_link="$REPORTS_DIR/latest"
  latest_target=""
  if [ -L "$latest_link" ]; then
    latest_target="$(readlink "$latest_link")"
  fi
  # Remove everything except 'latest' symlink and the directory it points to
  for entry in "$REPORTS_DIR"/*; do
    name="$(basename "$entry")"
    # Skip if matches the latest target dir or the symlink itself
    if [ "$name" = "latest" ]; then
      continue
    fi
    if [ -n "$latest_target" ] && [ "$name" = "$latest_target" ]; then
      continue
    fi
    rm -rf "$entry"
  done
fi

# 5) Bridge state artifact (if any)
STATE_FILE="memory-bank/diskbench_bridge_state.json"
if [ -f "$STATE_FILE" ]; then
  rm -f "$STATE_FILE"
fi

# 6) Remove any stray DMG artifacts (packaging is on HOLD)
find . -type f -name "*.dmg" -print -delete || true

echo "Cleanup complete."
