# Technical Context

## Architecture Overview

### New Architecture: Web GUI + Helper Binary
The project has transitioned from an integrated PyQt6 application to a **Web GUI + Helper Binary** architecture to solve sandbox limitations while maintaining professional disk testing capabilities.

```mermaid
graph TB
    A[React Web GUI] --> B[Flask Backend]
    B --> C[HTTP/WebSocket Bridge]
    C --> D[diskbench Helper Binary]
    D --> E[FIO Engine]
    E --> F[Real Disk Testing]
    F --> G[JSON Results]
    G --> C
    C --> B
    B --> A
    
    subgraph "Sandboxed Environment"
        A
        B
        H[localhost:8080]
        I[Pattern Storage]
    end
    
    subgraph "Unsandboxed Environment"
        D
        E
        F
        J[/usr/local/bin/diskbench]
        K[Bundled FIO Binary]
    end
```

## Technology Stack

### Frontend Layer
- **Framework**: React 18+ with modern hooks
- **Styling**: CSS Modules or Styled Components
- **State Management**: React Context + useReducer
- **Real-time Updates**: WebSocket connection to Flask backend
- **Local Storage**: Browser localStorage for custom patterns
- **Build Tool**: Create React App or Vite

### Backend Layer
- **Framework**: Python Flask with Flask-SocketIO
- **API**: RESTful endpoints for disk operations
- **Real-time**: WebSocket for live test progress
- **Process Management**: subprocess.Popen for helper binary
- **Security**: Input validation and sanitization
- **Logging**: Structured logging for debugging

### Helper Binary Layer
- **Language**: Python (standalone executable)
- **CLI Framework**: argparse for command-line interface
- **FIO Integration**: Bundled FIO binary execution
- **Output Format**: JSON for structured results
- **Security**: Input validation and path sanitization
- **Installation**: System-wide installation to /usr/local/bin/

### Distribution Layer
- **Package Format**: macOS DMG with installer
- **App Bundle**: Sandboxed .app for GUI
- **Helper Installation**: Admin-privileged installer script
- **FIO Bundling**: Included FIO binary with proper licensing
- **Documentation**: Integrated setup guides

## Core Components

### 1. React Frontend (`frontend/`)
```javascript
// Component Structure
src/
├── components/
│   ├── DiskSelector.jsx          # Disk selection interface
│   ├── TestPatterns.jsx          # Built-in pattern library
│   ├── CustomPatternEditor.jsx   # FIO syntax editor
│   ├── TestRunner.jsx            # Test execution interface
│   ├── ProgressMonitor.jsx       # Real-time progress display
│   ├── ResultsViewer.jsx         # Test results analysis
│   └── HelperInstaller.jsx       # Helper binary setup
├── hooks/
│   ├── useWebSocket.js           # WebSocket connection management
│   ├── useLocalStorage.js        # Pattern storage
│   └── useTestRunner.js          # Test execution logic
├── services/
│   ├── api.js                    # REST API client
│   ├── diskService.js            # Disk detection
│   └── patternService.js         # Pattern management
└── utils/
    ├── fioValidator.js           # FIO syntax validation
    └── formatters.js             # Data formatting utilities
```

### 2. Flask Backend (`app/`)
```python
# API Structure
app/
├── main.py                       # Flask app + launcher
├── api/
│   ├── __init__.py
│   ├── disks.py                  # Disk enumeration endpoints
│   ├── tests.py                  # Test execution endpoints
│   ├── patterns.py               # Pattern management
│   └── system.py                 # System status endpoints
├── services/
│   ├── helper_manager.py         # Helper binary management
│   ├── test_executor.py          # Test execution coordination
│   └── websocket_handler.py      # Real-time updates
└── utils/
    ├── security.py               # Input validation
    └── logging_config.py         # Logging setup
```

### 3. Helper Binary (`diskbench/`)
```python
# CLI Structure
diskbench/
├── main.py                       # CLI entry point
├── commands/
│   ├── __init__.py
│   ├── test.py                   # Test execution commands
│   ├── list_disks.py            # Disk enumeration
│   └── validate.py              # System validation
├── core/
│   ├── fio_runner.py            # FIO execution engine
│   ├── disk_detector.py         # macOS disk detection
│   ├── pattern_loader.py        # Test pattern management
│   └── result_processor.py      # JSON result formatting
└── utils/
    ├── security.py              # Input sanitization
    ├── logging.py               # Logging configuration
    └── system_info.py           # System information
```

## Data Flow Architecture

### 1. Test Execution Flow
```
User selects disk + pattern in React GUI
    ↓ HTTP POST /api/tests/start
Flask validates request + spawns helper binary
    ↓ subprocess.Popen(['diskbench', '--test', 'qlab_hq', ...])
Helper binary executes FIO with bundled binary
    ↓ Real-time stdout parsing
Flask streams progress via WebSocket
    ↓ WebSocket messages
React updates progress display in real-time
    ↓ Test completion
Helper binary outputs JSON results
    ↓ HTTP response
React displays formatted results with QLab analysis
```

### 2. Custom Pattern Flow
```
User creates custom pattern in editor
    ↓ FIO syntax validation in browser
Pattern saved to localStorage
    ↓ HTTP POST /api/patterns/save
Flask validates and stores pattern
    ↓ Available for test execution
Pattern appears in test selection dropdown
    ↓ User selects custom pattern
Same execution flow as built-in patterns
```

### 3. Helper Installation Flow
```
GUI detects missing helper binary
    ↓ HTTP GET /api/system/helper-status
Flask checks /usr/local/bin/diskbench
    ↓ Returns installation status
React shows "Install Helper" button
    ↓ User clicks install
Flask executes installer script with admin privileges
    ↓ sudo installer script
Helper binary installed system-wide
    ↓ Installation verification
GUI enables real disk testing features
```

## Security Considerations

### Input Validation
- **Disk Paths**: Whitelist validation against system disk list
- **FIO Parameters**: Syntax validation and dangerous flag filtering
- **File Paths**: Path traversal prevention
- **Command Injection**: Parameterized subprocess calls only

### Privilege Separation
- **GUI Process**: Sandboxed, minimal privileges
- **Helper Binary**: Unsandboxed, disk access only
- **Installation**: Admin privileges only during setup
- **Communication**: Localhost-only HTTP/WebSocket

### FIO Safety
- **Parameter Filtering**: Remove dangerous flags (--exec, --external)
- **Path Restrictions**: Limit file operations to selected disk
- **Resource Limits**: Prevent system overload
- **Timeout Protection**: Kill runaway processes

## Performance Optimizations

### Frontend Performance
- **Component Memoization**: React.memo for expensive components
- **Virtual Scrolling**: For large result datasets
- **Debounced Updates**: Throttle real-time progress updates
- **Code Splitting**: Lazy load heavy components

### Backend Performance
- **Async Processing**: Non-blocking test execution
- **Connection Pooling**: Efficient WebSocket management
- **Caching**: Cache disk information and system status
- **Resource Management**: Proper subprocess cleanup

### Helper Binary Performance
- **Efficient FIO Execution**: Optimized parameters for macOS
- **Minimal Dependencies**: Standalone Python executable
- **Fast Startup**: Minimal import overhead
- **Memory Management**: Proper cleanup of large test files

## Testing Strategy

### Unit Testing
- **Frontend**: Jest + React Testing Library
- **Backend**: pytest with Flask test client
- **Helper Binary**: pytest with subprocess mocking
- **Integration**: End-to-end test scenarios

### Performance Testing
- **Load Testing**: Multiple concurrent test executions
- **Memory Profiling**: Long-running test memory usage
- **Disk Performance**: Validation against known benchmarks
- **WebSocket Stress**: High-frequency update handling

### Platform Testing
- **macOS Versions**: 10.14+ compatibility testing
- **Hardware Variants**: Intel and Apple Silicon Macs
- **Disk Types**: SSD, HDD, external drives
- **Permission Scenarios**: Various security configurations

## Deployment Architecture

### Development Environment
```bash
# Frontend development
cd frontend && npm start          # React dev server on :3000
cd app && python main.py         # Flask backend on :8080

# Helper binary testing
cd diskbench && python main.py --test setup_check --disk /tmp
```

### Production Distribution
```
QLab-Disk-Tester.dmg
├── QLab Disk Tester.app/         # Sandboxed GUI app
│   └── Contents/
│       ├── MacOS/main            # Flask + React bundle
│       └── Resources/static/     # React build output
├── diskbench                     # Helper binary
├── fio-3.37/                     # FIO binary
├── install-helper.sh             # Installation script
└── README.pdf                   # Setup instructions
```

### Installation Process
1. User mounts DMG and drags app to Applications
2. First launch detects missing helper binary
3. GUI prompts for helper installation
4. Admin authentication for system-wide installation
5. Helper binary and FIO installed to /usr/local/
6. GUI enables full functionality

This architecture provides the optimal balance of user experience, security, and functionality while maintaining compatibility with macOS security requirements.
