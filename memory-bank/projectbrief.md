# Project Brief

## Project Name
QLab Disk Performance Tester - Web GUI + Helper Binary Architecture

## Project Goal
To develop a modern web-based disk performance testing application for macOS using a **Web GUI + Helper Binary** architecture. The application provides professional FIO-based disk testing specifically tailored for QLab shows requiring high-performance video playback, while solving sandbox limitations through architectural separation.

## Key Objectives
- Develop a **React-based web interface** served by Python Flask for modern user experience
- Implement an **unsandboxed helper binary** (`diskbench`) for real FIO disk testing
- Provide **guided helper installation** with admin privileges for system-wide deployment
- Support **custom FIO pattern editor** with raw syntax validation and local storage
- Maintain all existing **QLab-specific test patterns** (ProRes 422/HQ, thermal testing)
- Enable **real-time monitoring** via WebSocket communication
- Ensure **bundled FIO distribution** without external dependencies
- Generate **professional analysis** with QLab suitability ratings and recommendations

## Architecture Overview

### Web GUI + Helper Binary Design
```
React Web GUI (Sandboxed) ←→ Flask Backend ←→ diskbench Helper Binary (Unsandboxed) ←→ FIO Engine
```

**Key Components:**
1. **React Frontend**: Modern web interface with real-time updates
2. **Flask Backend**: REST API + WebSocket server on localhost:8080
3. **Helper Binary**: Standalone `diskbench` CLI with bundled FIO
4. **Communication Bridge**: HTTP/WebSocket between sandboxed GUI and unsandboxed helper

## Scope

### Phase 1: Helper Binary Development
- Extract existing FIO logic into standalone `diskbench` CLI
- Bundle FIO binary with proper permissions and licensing
- Implement disk detection and security validation
- Create JSON-based input/output interface
- Test CLI functionality independently

### Phase 2: Flask Backend Development
- REST API endpoints for disk listing, test execution, and results
- WebSocket integration for real-time progress updates
- Helper binary detection and installation management
- Pattern storage and validation system
- Security layer for input sanitization

### Phase 3: React Frontend Development
- Modern responsive web interface
- Disk selection with real-time detection
- Built-in pattern library (QLab ProRes 422/HQ, Setup Check, Max Sustained)
- Custom pattern editor with FIO syntax validation
- Real-time progress monitoring with charts
- Results analysis with QLab-specific recommendations
- Helper binary installation wizard

### Phase 4: Distribution and Packaging
- DMG package with GUI app and helper binary
- Automated installer script for helper binary
- Documentation and setup guides
- Testing on clean macOS systems
- Code signing and notarization preparation

## Core Features

### Disk Testing Capabilities 🚀
- **Multi-Tier Testing**: Setup Check (30s), QLab ProRes 422 (2.5h), QLab ProRes HQ (2.5h), Max Sustained (2h)
- **QLab-Specific Analysis**: 4K ProRes HQ stream capacity calculation (92 MB/s per stream)
- **Thermal Testing**: Long-duration tests with thermal recovery phases
- **Real-time Monitoring**: Live throughput, IOPS, latency, and temperature tracking
- **Professional Reporting**: Suitability ratings with specific QLab recommendations

### Modern User Experience 🌐
- **Web-Based Interface**: React frontend with responsive design
- **Real-time Updates**: WebSocket-based live progress monitoring
- **Custom Pattern Editor**: Raw FIO syntax editor with validation
- **Pattern Library**: Import/export custom test configurations
- **Local Storage**: Browser-based pattern and settings persistence
- **Guided Installation**: Helper binary setup with clear instructions

### Technical Excellence 💎
- **Bundled Dependencies**: FIO binary included, no Homebrew required
- **Security Validation**: Input sanitization and path restrictions
- **Cross-Architecture**: Intel and Apple Silicon Mac support
- **Robust Error Handling**: Graceful fallbacks and clear user guidance
- **Modular Architecture**: Clean separation between GUI and testing engine

### QLab Optimization 🎬
- **Realistic Workloads**: Simulates concurrent 4K ProRes streams with crossfades
- **Video-Optimized Parameters**: Large block sizes (1M-4M) for streaming performance
- **Latency Analysis**: Evaluates cue response times for live performance
- **Production Guidance**: Clear suitability ratings (🟢/🟡/🟠/🔴) with recommendations

## Distribution Strategy

### DMG Package Contents
```
QLab-Disk-Tester.dmg
├── QLab Disk Tester.app          # Sandboxed web GUI
├── diskbench                     # Helper binary
├── fio-3.37/                     # Bundled FIO binary
├── install-helper.sh             # Installation script
└── README.pdf                   # Setup instructions
```

### Installation Flow
1. User mounts DMG and drags app to Applications
2. First launch opens browser to localhost:8080
3. GUI detects missing helper binary
4. User clicks "Install Helper" → Admin authentication
5. Helper binary installed to `/usr/local/bin/diskbench`
6. GUI enables full disk testing functionality

## Technology Stack

### Frontend Layer
- **Framework**: React 18+ with modern hooks
- **Styling**: CSS Modules for component-scoped styling
- **State Management**: React Context + useReducer
- **Real-time**: WebSocket connection to Flask backend
- **Storage**: Browser localStorage for custom patterns

### Backend Layer
- **Framework**: Python Flask with Flask-SocketIO
- **API**: RESTful endpoints + WebSocket for real-time updates
- **Process Management**: subprocess.Popen for helper binary execution
- **Security**: Input validation and command sanitization

### Helper Binary Layer
- **Language**: Python (standalone executable)
- **CLI Framework**: argparse for command-line interface
- **FIO Integration**: Bundled FIO binary execution
- **Output**: Structured JSON results
- **Installation**: System-wide deployment to /usr/local/bin/

## Success Metrics

### Functional Requirements
- ✅ **Real FIO Testing**: Unsandboxed helper binary with bundled FIO
- ✅ **Modern Interface**: React web GUI with professional design
- ✅ **Custom Patterns**: FIO syntax editor with validation and storage
- ✅ **Real-time Monitoring**: WebSocket updates during testing
- ✅ **QLab Analysis**: Accurate performance assessment for video workflows
- ✅ **Easy Distribution**: DMG package with guided installation

### Performance Requirements
- **Test Accuracy**: Results within 5% of native FIO execution
- **Real-time Updates**: <100ms latency for progress updates
- **Installation Time**: <2 minutes for complete setup
- **Memory Usage**: <200MB for GUI, <100MB for helper binary
- **Startup Time**: <5 seconds from launch to ready state

### Compatibility Requirements
- **macOS Versions**: 10.14 Mojave through latest macOS
- **Hardware**: Intel and Apple Silicon Macs
- **Disk Types**: Internal SSD, external SSD, HDD, NVMe
- **Browsers**: Safari, Chrome, Firefox for web interface

## Out of Scope
- Development of FIO itself (using existing FIO 3.37)
- Cross-platform compatibility (macOS-only focus)
- App Store distribution (due to helper binary requirements)
- Network-based testing (local disk testing only)
- Database storage (filesystem and localStorage only)

## Risk Mitigation

### Technical Risks
- **Sandbox Limitations**: Solved by helper binary architecture
- **Admin Privileges**: Clear user guidance and automated installer
- **FIO Licensing**: GPL compliance with proper attribution
- **Browser Compatibility**: Modern web standards with fallbacks

### User Experience Risks
- **Installation Complexity**: Guided wizard with clear instructions
- **Permission Prompts**: Clear explanation of admin requirements
- **Helper Binary Updates**: Automated detection and update prompts

This architecture provides the optimal balance of modern user experience, professional testing capabilities, and macOS compatibility while solving the fundamental sandbox limitations of the previous integrated approach.
