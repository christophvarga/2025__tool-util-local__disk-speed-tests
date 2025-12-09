#!/usr/bin/env bash
# Build a fully offline bundle you can copy to an external SSD and run on a new Mac (no internet).
# Version 1.0 – 09.09.2025
#
# Usage:
#   bash scripts/build_offline_bundle.sh
#
# Output:
#   dist/offline_bundle-<arch>/
#     ├── diskbench-bridge            (PyInstaller onefile binary)
#     ├── Start Diskbench Bridge.command
#     └── vendor/fio/macos/<arch>/fio
#
# Notes:
# - Requires PyInstaller installed locally. Builds the bridge binary including diskbench + vendored FIO.
# - If vendored FIO is missing, tries to copy from your local system (Homebrew) automatically.
# - After building, copy the offline_bundle-* directory to an SSD and double‑click “Start Diskbench Bridge.command”.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Detect arch
MACHINE_ARCH="$(uname -m)"
if [[ "$MACHINE_ARCH" == arm64* || "$MACHINE_ARCH" == *aarch64* ]]; then
  ARCH_DIR=arm64
else
  ARCH_DIR=x86_64
fi

# Ensure vendored fio exists; attempt to copy from system if available
VENDOR_DIR="$REPO_ROOT/vendor/fio/macos/$ARCH_DIR"
FIO_VENDOR_BIN="$VENDOR_DIR/fio"
if [[ ! -x "$FIO_VENDOR_BIN" ]]; then
  if command -v fio >/dev/null 2>&1; then
    mkdir -p "$VENDOR_DIR"
    cp "$(command -v fio)" "$FIO_VENDOR_BIN"
    chmod +x "$FIO_VENDOR_BIN"
    echo "Vendored fio created at: $FIO_VENDOR_BIN"
  else
    echo "Error: vendored fio missing and no system 'fio' found."
    echo "Place a macOS fio binary at $FIO_VENDOR_BIN and re-run."
    exit 2
  fi
fi

# Build PyInstaller onefile binary (includes diskbench + vendor/fio as data)
bash "$REPO_ROOT/scripts/build_bridge_pyinstaller.sh" --onefile

# Prepare offline bundle dir
BUNDLE_DIR="$REPO_ROOT/dist/offline_bundle-$ARCH_DIR"
mkdir -p "$BUNDLE_DIR"

# Copy onefile binary
if [[ -x "$REPO_ROOT/dist/diskbench-bridge" && ! -d "$REPO_ROOT/dist/diskbench-bridge" ]]; then
  cp "$REPO_ROOT/dist/diskbench-bridge" "$BUNDLE_DIR/diskbench-bridge"
else
  echo "Error: onefile binary not found at dist/diskbench-bridge."
  exit 3
fi

# Copy vendored fio (redundant to embedded data, but useful for inspection/replacement)
mkdir -p "$BUNDLE_DIR/vendor/fio/macos/$ARCH_DIR"
cp "$FIO_VENDOR_BIN" "$BUNDLE_DIR/vendor/fio/macos/$ARCH_DIR/fio"
chmod +x "$BUNDLE_DIR/vendor/fio/macos/$ARCH_DIR/fio"

# Create double-click launcher
LAUNCHER="$BUNDLE_DIR/Start Diskbench Bridge.command"
cat > "$LAUNCHER" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# Start server in background, open browser
"$DIR/diskbench-bridge" >/tmp/diskbench_bridge_server.log 2>&1 &
sleep 2
if command -v open >/dev/null 2>&1; then
  open "http://localhost:8765/" || true
fi
# Keep terminal open briefly to show status
echo "Diskbench Bridge gestartet. Logs: /tmp/diskbench_bridge_server.log"
EOF
chmod +x "$LAUNCHER"

# Write a short README into bundle
cat > "$BUNDLE_DIR/README_OFFLINE.txt" << EOF
QLab Disk Performance Tester – Offline Bundle
============================================

Start:
- Doppelklick auf "Start Diskbench Bridge.command"
- Browser öffnet: http://localhost:8765/

Ohne Internet:
- Der Bundle enthält eine vendorte FIO-Binary unter vendor/fio/macos/$ARCH_DIR/fio.
- Der Bridge-Server nutzt die vendorte FIO-Binary automatisch.

Troubleshooting:
- Logs: /tmp/diskbench_bridge_server.log
- Falls FIO fehlt oder nicht ausführbar: ersetzen unter vendor/fio/macos/$ARCH_DIR/fio (chmod +x)
EOF

echo "Offline bundle created at: $BUNDLE_DIR"

