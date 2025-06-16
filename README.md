# QLab Disk Performance Tester

Professional disk performance testing tool optimized for QLab audio/video applications. This tool uses a modern architecture with a clean web GUI that communicates with an unsandboxed helper binary to perform comprehensive FIO-based disk testing.

## 🏗️ Architecture Overview

The application uses a **sandboxed GUI + unsandboxed helper binary** architecture to provide both security and functionality:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web GUI       │    │  Communication   │    │ Helper Binary   │    │   FIO Engine    │
│  (Sandboxed)    │◄──►│     Bridge       │◄──►│ (Unsandboxed)   │◄──►│ (Professional)  │
│                 │    │                  │    │                 │    │                 │
│ • Clean UI      │    │ • Parameter      │    │ • Raw disk      │    │ • Industry      │
│ • Disk select   │    │   validation     │    │   access        │    │   standard      │
│ • Test config   │    │ • Command exec   │    │ • FIO execution │    │ • Precise       │
│ • Results view  │    │ • Progress mon   │    │ • JSON output   │    │   testing       │
│ • Export data   │    │ • Error handling │    │ • Safety checks │    │ • QLab patterns │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

1. **Web GUI (Sandboxed)**: Clean browser-based interface for user interaction
2. **Helper Binary (Unsandboxed)**: Python CLI tool that executes FIO tests with raw disk access
3. **Communication Bridge**: Local command execution and data exchange
4. **FIO Engine**: Professional disk benchmarking with QLab-optimized test patterns

## 🚀 Quick Start

### 1. Install FIO via Homebrew

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install FIO
brew install fio
```

### 2. Start the Bridge Server

```bash
cd bridge-server
python server.py
```

### 3. Open the Web Interface

```bash
open web-gui/index.html
```

### 4. Run Setup Wizard

1. Open the web interface in your browser
2. Follow the setup wizard to verify FIO installation
3. Select a disk from the available list
4. Choose a test type (QLab Mixed Test recommended)
5. Click "Start Test"
6. View results and export if needed

## 📋 Test Types

### QLab-Optimized Tests

- **QLab ProRes HQ Test** ⭐ *Recommended*
  - Mixed read/write patterns for ProRes HQ video playback
  - 4K block sizes with realistic access patterns
  - Optimized for live performance requirements

- **QLab ProRes 422 Test**
  - Optimized for ProRes 422 video playback
  - Lower bandwidth requirements than HQ

- **Setup Check**
  - Quick system validation
  - Basic performance verification
  - Ideal for initial system testing

- **Baseline Streaming**
  - General streaming performance test
  - Audio/video content simulation

## 🔧 Helper Binary Commands

The `diskbench` helper binary provides comprehensive CLI functionality:

### System Validation
```bash
python main.py --validate
```

### List Available Disks
```bash
python main.py --list-disks --json
```

### Run Performance Tests
```bash
# QLab ProRes HQ test
python main.py --test qlab_prores_hq --disk /dev/disk1s1 --size 10 --output results.json

# Quick setup check
python main.py --test setup_check --disk /Volumes/MyDrive --size 5 --output check.json

# Custom FIO configuration
python main.py --config custom-test.fio --disk /dev/disk2s1 --size 20 --output custom.json
```

### Command Options
- `--test`: Test type (qlab_prores_hq, qlab_prores_422, setup_check, baseline_streaming)
- `--disk`: Target disk path (/dev/diskX or /Volumes/Name)
- `--size`: Test file size in GB (1-100)
- `--output`: Output JSON file path
- `--progress`: Show progress during test
- `--json`: Format output as JSON
- `--validate`: Run system validation
- `--list-disks`: List available disks
- `--version`: Show version information

## 📊 Understanding Results

### QLab Performance Analysis

Results include QLab-specific performance analysis:

- **Excellent** ✅: Perfect for complex shows, 4K video, rapid cue triggering
- **Good** ✅: Suitable for most QLab applications, standard video playback
- **Fair** ⚠️: Basic usage only, pre-load cues, avoid rapid sequences
- **Poor** ❌: Not suitable for live performance, upgrade recommended

### Key Metrics

- **Sequential Read/Write**: Large file streaming (video files)
- **Random Read/Write**: Small file access (audio samples, cues)
- **IOPS**: Input/Output Operations Per Second
- **Latency**: Response time for disk operations
- **Bandwidth**: Data transfer rate (MB/s)

### Recommendations

The tool provides specific recommendations based on test results:
- Hardware upgrade suggestions
- QLab configuration tips
- Performance optimization advice
- Workflow recommendations

## 🛠️ Development

### Project Structure

```
├── diskbench/              # Helper binary (unsandboxed)
│   ├── main.py             # CLI entry point
│   ├── commands/           # Command implementations
│   ├── core/               # FIO engine and test patterns
│   └── utils/              # Utilities and validation
├── web-gui/                # Web interface (sandboxed)
│   ├── index.html          # Main interface
│   ├── styles.css          # Styling
│   └── app.js              # Application logic
├── bridge-server/          # HTTP API server
│   └── server.py           # Bridge communication
└── memory-bank/            # Development documentation
```

### Testing

```bash
# Test helper binary
cd diskbench && python test_diskbench.py

# Test FIO availability
cd diskbench && python main.py --validate

# Test disk listing
cd diskbench && python main.py --list-disks
```

### Adding Custom Test Patterns

1. Edit `diskbench/core/qlab_patterns.py`
2. Add new test configuration
3. Update web GUI test options
4. Test with `--test custom_pattern_name`

## 🔒 Security & Safety

### Built-in Safety Features

- **Disk path validation**: Prevents access to system-critical paths
- **Space checking**: Ensures sufficient free space before testing
- **Parameter sanitization**: Validates all user inputs
- **Safe test directories**: Uses isolated test locations
- **Cleanup procedures**: Removes test files after completion

### Permissions

- **Web GUI**: Runs in browser sandbox with no system access
- **Helper Binary**: Requires disk access permissions for testing
- **Raw device access**: May require admin privileges for `/dev/disk*` testing

## 📈 Performance Expectations

### SSD Performance (Typical)
- Sequential Read: 400-600 MB/s
- Sequential Write: 350-500 MB/s
- Random Read: 40,000-80,000 IOPS
- Random Write: 35,000-70,000 IOPS
- Latency: <1ms

### HDD Performance (Typical)
- Sequential Read: 100-150 MB/s
- Sequential Write: 80-120 MB/s
- Random Read: 100-300 IOPS
- Random Write: 80-200 IOPS
- Latency: 8-15ms

## 🎯 QLab-Specific Recommendations

### For Excellent QLab Performance
- Use SSD storage for all media files
- Ensure >50,000 random read IOPS
- Maintain <2ms average latency
- Have >300 MB/s sequential read bandwidth

### For Basic QLab Usage
- Minimum 5,000 random read IOPS
- <10ms average latency
- >100 MB/s sequential read bandwidth
- Pre-load cues when possible

## 🐛 Troubleshooting

### Common Issues

**"FIO not found"**
- Ensure FIO is installed or use bundled version
- Check PATH environment variable
- Run `diskbench --validate` to verify

**"Permission denied"**
- Raw device testing requires admin privileges
- Use mounted volumes instead of raw devices
- Run with `sudo` if necessary for `/dev/disk*` access

**"Insufficient space"**
- Ensure target disk has enough free space
- Reduce test size parameter
- Clean up existing test files

**Web GUI not loading disks**
- Check that helper binary is working: `cd diskbench && python main.py --list-disks`
- Verify browser console for JavaScript errors
- Ensure all files are in correct locations

### Getting Help

1. Run system validation: `cd diskbench && python main.py --validate`
2. Check the browser console for errors
3. Verify FIO installation and permissions
4. Test helper binary independently

## 📄 License

This project is provided as-is for professional audio/video applications. The bundled FIO binary is subject to its own license terms.

## 🔄 Version History

- **v1.0.0**: Initial release with web GUI + helper binary architecture
  - Professional FIO-based testing
  - QLab-optimized test patterns
  - Clean web interface
  - Comprehensive safety features
  - JSON result export
