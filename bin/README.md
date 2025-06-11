# FIO Binaries Directory

This directory contains the bundled `fio` binaries for offline operation.

## Structure

```
bin/
├── fio-intel          # Intel x86_64 binary
├── fio-apple-silicon  # Apple Silicon arm64 binary
├── licenses/          # License files
└── README.md          # This file
```

## Binary Sources

The `fio` binaries should be downloaded from the official FIO project:
- **Source**: https://github.com/axboe/fio/releases
- **License**: GPL v2
- **Version**: Latest stable release

## Installation Instructions

### For Intel Macs (x86_64):
1. Download the macOS Intel binary from FIO releases
2. Rename it to `fio-intel`
3. Place it in this directory
4. Make executable: `chmod +x bin/fio-intel`

### For Apple Silicon Macs (arm64):
1. Download the macOS ARM binary from FIO releases
2. Rename it to `fio-apple-silicon`
3. Place it in this directory
4. Make executable: `chmod +x bin/fio-apple-silicon`

## License Compliance

Since FIO is GPL v2 licensed, we must include:
- The GPL v2 license text (place in `licenses/GPL-v2.txt`)
- Attribution to the FIO project
- Source code availability notice

## Fallback Behavior

If bundled binaries are not available, the application will:
1. Try to use system-installed `fio`
2. Provide installation instructions if neither is available

## Binary Verification

The application automatically:
- Detects system architecture
- Selects appropriate binary
- Verifies executable permissions
- Falls back gracefully if needed
