# QLab Disk Performance Tester

A professional disk performance testing tool specifically designed for QLab video playback systems. Tests SSD performance for 4K ProRes HQ video streaming with frame blending capabilities.

## Features

- **Offline Operation**: Bundled `fio` binaries for Intel and Apple Silicon Macs
- **Intelligent Disk Detection**: Automatically detects writable SSDs using macOS system profiler
- **QLab-Specific Testing**: Simulates 8x concurrent 4K ProRes HQ streams (92 MB/s each)
- **Multi-Tier Test Modes**: Quick (5min), Standard (30min), Extended (2h), Ultimate (8h)
- **Professional Reporting**: Colorful CLI output and detailed JSON exports
- **Smart Test Sizing**: Automatically adjusts test file sizes based on available disk space

## Requirements

- macOS (Intel or Apple Silicon)
- Python 3.6+ (uses only standard library)
- Writable SSD for testing

## Quick Start

### New Installation
1. **Download the project archive** (`.tar.gz` or `.zip`)
2. **Extract and install**:
   ```bash
   tar -xzf qlab-disk-tester_*.tar.gz
   cd qlab-disk-tester_*/
   bash install.sh
   ```
3. **Run the tester**:
   ```bash
   python3 qlab_disk_tester.py
   ```
4. **Follow the interactive prompts** to select disk and test mode

### Existing Installation
```bash
python3 qlab_disk_tester.py
```

## Project Structure

```
qlab_disk_tester.py     # Main executable
lib/                    # Core modules
├── disk_detector.py    # macOS disk detection
├── fio_engine.py       # FIO test execution
├── qlab_analyzer.py    # QLab-specific analysis
├── report_generator.py # CLI and JSON reporting
└── binary_manager.py   # Binary management system
bin/                    # FIO binaries (offline operation)
├── fio-intel          # Intel x86_64 binary
├── fio-apple-silicon  # Apple Silicon arm64 binary
└── README.md          # Binary installation guide
results/               # JSON test reports
templates/             # FIO job templates (future)
memory-bank/           # Development documentation
```

## Test Modes

### 1. Quick Speed Test (5 minutes)
- **Purpose**: Rapid assessment of peak performance
- **Tests**: Sequential read/write, random read
- **File Size**: 1GB
- **Use Case**: Initial SSD evaluation

### 2. Standard QLab Test (30 minutes) ⭐ **Recommended**
- **Purpose**: Simulate real QLab 4K ProRes HQ workload
- **Tests**: 8x concurrent streams, sustained read performance
- **File Size**: 20GB
- **Use Case**: Production readiness verification

### 3. Extended Stress Test (2 hours)
- **Purpose**: Assess sustained performance and thermal behavior
- **Tests**: Heavy concurrent load, thermal throttling detection
- **File Size**: 50GB
- **Use Case**: Professional deployment validation

### 4. Ultimate Endurance (8 hours)
- **Purpose**: Push SSD to absolute limits
- **Tests**: Maximum stress, long-term degradation analysis
- **File Size**: 100GB
- **Use Case**: Extreme reliability testing

## QLab Suitability Analysis

The tool analyzes results specifically for QLab video playback:

- **Stream Capacity**: Calculates maximum 4K ProRes HQ streams (92 MB/s each)
- **Cue Response**: Evaluates latency for smooth cue transitions
- **Suitability Rating**: ✅ Excellent / ⚠️ Acceptable / ❌ Poor
- **Recommendations**: Specific guidance for QLab production use

## Transfer and Installation

### Automated Installation (Recommended)

The project includes an automated installer that handles all setup:

```bash
# After extracting the archive
bash install.sh
```

The installer will:
- ✅ Check macOS compatibility
- ✅ Detect Mac architecture (Intel vs Apple Silicon)
- ✅ Verify Python 3.7+ installation
- ✅ Set proper file permissions
- ✅ Check FIO availability
- ✅ Test the installation
- ✅ Optionally create desktop shortcut

### Creating Distribution Packages

To create a distributable package for sharing:

```bash
# Create .tar.gz and .zip archives
bash package.sh

# This creates:
# - qlab-disk-tester_v1.0_YYYYMMDD_HHMMSS.tar.gz
# - qlab-disk-tester_v1.0_YYYYMMDD_HHMMSS.zip
```

### Manual Transfer Methods

#### Option 1: Complete Archive
```bash
# Create archive of entire project
tar -czf qlab-disk-tester.tar.gz qlab_disk_tester.py lib/ bin/ README.md install.sh

# Transfer via:
# - USB drive
# - AirDrop  
# - Cloud storage (Dropbox, Google Drive)
# - Email (if small enough)
```

#### Option 2: Git Repository
```bash
# If using Git version control
git clone <repository-url>
cd qlab-disk-tester
bash install.sh
```

#### Option 3: Individual Files
Minimum required files for transfer:
```
qlab_disk_tester.py     # Main application
lib/                    # All Python modules
install.sh              # Automated installer
README.md              # Documentation
bin/                    # FIO binaries (optional)
```

## FIO Binary Installation (Offline Operation)

### Option 1: Bundled Binaries (Recommended)
The project includes pre-compiled `fio` binaries for offline operation:

1. Download appropriate binary for your Mac:
   - **Intel Macs**: Place `fio` binary as `bin/fio-intel`
   - **Apple Silicon**: Place `fio` binary as `bin/fio-apple-silicon`
2. Make executable: `chmod +x bin/fio-*`
3. Run the tester - it will automatically detect and use bundled binaries

### Option 2: System Installation
If bundled binaries aren't available, install `fio` system-wide:

```bash
# Using Homebrew
brew install fio

# Or download from: https://github.com/axboe/fio/releases
```

## Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║                    QLab Disk Performance Tester              ║
║                  Professional Video Storage Testing          ║
╚══════════════════════════════════════════════════════════════╝

📊 PERFORMANCE METRICS
  Bandwidth (Read): 1,234.56 MB/s
  IOPS (Read):      308
  Latency (avg):    3.21 ms
  Latency (99%):    7.89 ms

🎬 QLAB SUITABILITY ANALYSIS
  4K ProRes HQ Streams: 13 simultaneous
  Stream Performance:   ✅ EXCELLENT
  Cue Response Time:    ✅ EXCELLENT

💡 RECOMMENDATIONS
  ✅ Perfect for professional 4K QLab production.
```

## Troubleshooting Installation

### Common Issues

#### "Permission denied" errors
```bash
# Fix file permissions
chmod +x install.sh qlab_disk_tester.py
chmod +x bin/fio-*
```

#### "Python 3 not found"
- Install Python 3.7+ from [python.org](https://python.org)
- Or use Homebrew: `brew install python3`

#### "No module named 'lib'"
- Ensure the `lib/` directory was completely copied
- Check that `lib/__init__.py` exists

#### "fio not found"
- The application will show installation instructions
- Install via Homebrew: `brew install fio`
- Or place FIO binary in `bin/` directory

### Architecture-Specific Notes

#### Apple Silicon Macs (M1/M2/M3/M4)
- Uses `bin/fio-apple-silicon` if available
- Automatic architecture detection
- Falls back to system FIO if needed

#### Intel Macs
- Uses `bin/fio-intel` if available
- Compatible with all Intel Mac models
- Falls back to system FIO if needed

### Manual Installation Steps

If the automated installer doesn't work:

```bash
# 1. Check Python
python3 --version  # Should be 3.7+

# 2. Set permissions
chmod +x qlab_disk_tester.py
chmod +x bin/fio-apple-silicon  # or fio-intel

# 3. Test modules
python3 -c "from lib.binary_manager import BinaryManager; print('OK')"

# 4. Run application
python3 qlab_disk_tester.py
```

## Technical Details

### FIO Test Parameters
- **Block Sizes**: Optimized for video streaming (1M-4M)
- **Queue Depths**: Simulate concurrent stream access
- **I/O Engine**: `posixaio` (recommended for macOS)
- **Direct I/O**: Bypasses system cache for realistic results

### QLab-Specific Calculations
- **4K ProRes HQ**: 92 MB/s per stream (conservative estimate)
- **Frame Blending**: Accounts for 2x read overhead
- **Latency Thresholds**: <10ms excellent, <20ms acceptable

## Development

### Memory Bank System
The project uses a comprehensive memory bank for development context:
- `memory-bank/projectbrief.md` - Project scope and goals
- `memory-bank/techContext.md` - Technical constraints and decisions
- `memory-bank/progress.md` - Development status and issues

### Contributing
1. Read the memory bank files for context
2. Follow the modular architecture
3. Maintain Python standard library only
4. Test on both Intel and Apple Silicon Macs

## License

This project is open source. The bundled `fio` binaries are GPL v2 licensed.

## Support

For QLab-specific questions, consult the QLab documentation. For disk performance issues, consider professional SSD benchmarking tools.
