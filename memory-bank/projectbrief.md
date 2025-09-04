# Project Brief

## Project Name
QLab Disk Performance Tester - MVP Web Interface Architecture

## Project Goal

Top Goal (non-negotiable):
- Run on a factory-new Apple Silicon (M-series) Mac completely offline (no internet) and without interfering with or requiring changes to Apple's System Integrity Protection (SIP).

To develop a functional MVP disk performance testing application for macOS using a **Web GUI + HTTP Bridge + CLI Helper** architecture. The application provides professional FIO-based disk testing specifically tailored for QLab shows requiring high-performance video playback, while maintaining simplicity and honest error reporting.

## Key Objectives
- Develop a **HTML/CSS/JS web interface** served by Python HTTP bridge for modern user experience
- Implement a **CLI helper binary** (`diskbench`) for real FIO disk testing
- Provide **guided FIO installation** via Homebrew with honest status reporting
- Support **4 QLab-specific test patterns** with realistic durations and analysis
- Maintain **honest error reporting** about macOS FIO limitations
- Enable **real-time monitoring** via HTTP polling communication
- Ensure **Homebrew FIO integration** without bundled dependencies
- Generate **professional analysis** with QLab suitability ratings and recommendations

## Architecture Overview

### MVP Web GUI + HTTP Bridge + CLI Helper Design
```
HTML/CSS/JS Web GUI ←→ Python HTTP Bridge (localhost:8765) ←→ diskbench CLI ←→ Homebrew FIO
```

**Key Components:**
1. **Web Interface**: Plain HTML/CSS/JS with professional styling
2. **HTTP Bridge**: Python server translating web requests to CLI calls
3. **CLI Helper**: Standalone `diskbench` tool with JSON output
4. **FIO Integration**: Homebrew-installed FIO with honest error reporting

## Scope

### MVP Implementation ✅
- **Web Interface**: Professional HTML/CSS/JS interface in `web-gui/`
- **HTTP Bridge**: Python server in `bridge-server/server.py` on localhost:8765
- **CLI Helper**: diskbench tool in `diskbench/` with JSON output
- **FIO Integration**: Homebrew FIO detection and honest error reporting
- **Test Patterns**: 4 QLab-specific patterns with correct durations
- **Setup Wizard**: 3-step installation and validation process

### MVP Features Implemented ✅
- **Disk Selection**: Real-time disk detection and selection
- **Test Patterns**: Quick (3min), ProRes 422 Show (2.75h), ProRes HQ Show (2.75h), Max Sustained (1.5h)
- **Progress Monitoring**: Real-time test progress via HTTP polling
- **Results Analysis**: QLab-specific performance analysis and recommendations
- **Setup Wizard**: Guided FIO installation and system validation
- **Error Handling**: Honest reporting of macOS FIO limitations

## Core Features

### Disk Testing Capabilities 🚀
- **Multi-Tier Testing**: Quick Check (3min), QLab ProRes 422 Show (2.75h), QLab ProRes HQ Show (2.75h), Max Sustained (1.5h)
- **QLab-Specific Analysis**: 4K ProRes HQ stream capacity calculation (92 MB/s per stream)
- **Thermal Testing**: Long-duration tests with thermal performance monitoring
- **Real-time Monitoring**: Live throughput, IOPS, and progress tracking
- **Professional Reporting**: Suitability ratings with specific QLab recommendations

### Modern User Experience 🌐
- **Web-Based Interface**: HTML/CSS/JS frontend with responsive design
- **Real-time Updates**: HTTP polling for live progress monitoring
- **Setup Wizard**: Guided FIO installation with clear instructions
- **Professional Styling**: Clean, modern interface with QLab branding
- **Honest Communication**: Clear reporting of system limitations and capabilities

### Technical Excellence 💎
- **No Dependencies**: Plain HTML/CSS/JS, no build process required
- **Security Validation**: Input sanitization and path restrictions
- **Cross-Architecture**: Intel and Apple Silicon Mac support
- **Robust Error Handling**: Graceful fallbacks and clear user guidance
- **Modular Architecture**: Clean separation between GUI, bridge, and testing engine

### QLab Optimization 🎬
- **Realistic Workloads**: Simulates concurrent 4K ProRes streams with crossfades
- **Video-Optimized Parameters**: Large block sizes (1M-4M) for streaming performance
- **Latency Analysis**: Evaluates cue response times for live performance
- **Production Guidance**: Clear suitability ratings (🟢/🟡/🟠/🔴) with recommendations

## Distribution Strategy

### MVP Distribution
```
QLab-Disk-Tester/
├── web-gui/                      # HTML/CSS/JS interface
│   ├── index.html               # Main interface
│   ├── styles.css               # Professional styling
│   └── app.js                   # Frontend logic
├── bridge-server/               # HTTP bridge
│   └── server.py                # Python HTTP server
├── diskbench/                   # CLI helper
│   ├── main.py                  # CLI entry point
│   ├── commands/                # Command implementations
│   ├── core/                    # Core testing engines
│   └── utils/                   # System utilities
└── README.md                    # Setup instructions
```

### Installation Flow
1. User downloads/clones project
2. Installs FIO via Homebrew: `brew install fio`
3. Starts bridge server: `python3 bridge-server/server.py`
4. Opens web interface at localhost:8765
5. Follows setup wizard for validation

## Technology Stack

### Frontend Layer
- **Framework**: Plain HTML5/CSS3/JavaScript (no build process)
- **Styling**: Professional CSS with responsive design
- **Communication**: HTTP fetch() API to bridge server
- **Real-time**: HTTP polling for progress updates

### Backend Layer
- **Framework**: Python 3 with built-in http.server
- **API**: RESTful endpoints for disk operations and testing
- **Process Management**: subprocess calls to diskbench CLI
- **Security**: Input validation and command sanitization

### Helper Binary Layer
- **Language**: Python 3 (standalone CLI tool)
- **CLI Framework**: argparse for command-line interface
- **FIO Integration**: Homebrew FIO execution with honest error reporting
- **Output**: Structured JSON results
- **Installation**: No installation required - runs from project directory

## Success Metrics

### Functional Requirements ✅
- **Real FIO Testing**: Homebrew FIO integration with honest error reporting
- **Modern Interface**: Professional web GUI with responsive design
- **Real-time Monitoring**: HTTP polling updates during testing
- **QLab Analysis**: Accurate performance assessment for video workflows
- **Easy Setup**: Simple Homebrew installation with guided wizard

### Performance Requirements
- **Test Accuracy**: Results within 5% of native FIO execution
- **Real-time Updates**: <2 second latency for progress updates
- **Setup Time**: <5 minutes for complete setup including FIO installation
- **Memory Usage**: <100MB for bridge server, <50MB for CLI helper
- **Startup Time**: <3 seconds from bridge start to web interface ready

### Compatibility Requirements
- **macOS Versions**: 10.14 Mojave through latest macOS
- **Hardware**: Intel and Apple Silicon Macs
- **Disk Types**: Internal SSD, external SSD, HDD, NVMe
- **Browsers**: Safari, Chrome, Firefox for web interface

## Out of Scope
- Development of FIO itself (using existing Homebrew FIO)
- Cross-platform compatibility (macOS-only focus)
- App Store distribution (Homebrew dependency)
- Network-based testing (local disk testing only)
- Complex packaging (simple directory structure)

## Risk Mitigation

### Technical Risks
- **FIO Limitations**: Honest error reporting instead of workarounds
- **Homebrew Dependencies**: Clear user guidance for installation
- **Browser Compatibility**: Modern web standards with fallbacks

### User Experience Risks
- **Installation Complexity**: Guided setup wizard with clear instructions
- **FIO Errors**: Honest communication about macOS limitations
- **Setup Issues**: Comprehensive validation and troubleshooting guidance

## Legacy Components

### Not Used in MVP ❌
- `qlab_disk_tester/` - PyQt6 GUI components (archived)
- `disk_tester.py` - Flask app approach (not implemented)
- React components mentioned in old docs (never existed)
- DMG packaging (not needed for MVP)
- Bundled FIO binaries (using Homebrew instead)

### MVP Implementation ✅
- `web-gui/` - HTML/CSS/JS interface
- `bridge-server/` - Python HTTP server
- `diskbench/` - CLI helper tool
- `memory-bank/` - Documentation

This MVP architecture provides professional disk testing capabilities while maintaining simplicity, honesty about system limitations, and ease of use for QLab professionals. The focus is on core functionality with a clean, reliable implementation that works within macOS constraints.
