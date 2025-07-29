# QLab Disk Performance Tester - Architecture & Information Flow

## System Overview

The QLab Disk Performance Tester consists of three main components that work together to provide a seamless disk testing experience:

```
┌─────────────────────┐     HTTP API      ┌──────────────────┐     CLI      ┌────────────────┐
│                     │ ◄─────────────────► │                  │ ◄───────────► │                │
│   Web GUI (React)   │                    │  Bridge Server   │               │   Diskbench    │
│   localhost:8080    │                    │  localhost:8081  │               │   Python CLI   │
│                     │                    │                  │               │                │
└─────────────────────┘                    └──────────────────┘               └────────────────┘
         │                                          │                                    │
         │                                          │                                    │
         ▼                                          ▼                                    ▼
    User Interface                            Middleware/API                      Test Execution
    - Test Selection                          - Request Routing                  - FIO Integration
    - Progress Display                        - Process Management               - Disk Operations
    - Results Visualization                   - State Persistence                - Results Processing
```

## Component Details

### 1. Web GUI (Frontend)
**Location**: `/web-gui/`
**Technology**: Pure JavaScript (no framework), HTML5, CSS3
**Key Files**:
- `app.js` - Main application logic
- `index.html` - UI structure
- `style.css` - Styling

**Responsibilities**:
- User interface for test configuration
- Real-time progress monitoring
- Results visualization
- System setup wizard
- Architecture documentation display

### 2. Bridge Server (Middleware)
**Location**: `/bridge-server/`
**Technology**: Python HTTP Server
**Key Files**:
- `server.py` - HTTP server and request handling
- `setup.py` - Installation and system checks

**Responsibilities**:
- HTTP API endpoint for Web GUI
- Process management for diskbench CLI
- State persistence (running tests)
- Background test discovery
- FIO installation management

### 3. Diskbench CLI (Test Engine)
**Location**: `/diskbench/`
**Technology**: Python CLI application
**Key Components**:
- `main.py` - CLI entry point
- `commands/` - Command implementations
- `core/` - FIO runner and test patterns
- `utils/` - Helper utilities

**Responsibilities**:
- FIO test execution
- Disk discovery and validation
- Test pattern management
- Results processing and analysis

## Information Flow

### 1. Test Discovery Flow

```
User clicks "Refresh Disks" in Web GUI
    │
    ▼
app.js: loadAvailableDisks()
    │
    ▼
HTTP GET /api/disks ──────► Bridge Server
                                │
                                ▼
                            server.py: handle_list_disks()
                                │
                                ▼
                            Execute: diskbench --list-disks --json
                                │
                                ▼
                            diskbench/commands/list_disks.py
                                │
                                ▼
                            System disk enumeration (diskutil)
                                │
                                ▼
                            Filter suitable disks
                                │
                                ▼
                            Return JSON response
                                │
    ◄───────────────────────────┘
    │
    ▼
Display disk list in UI
```

### 2. Test Execution Flow

```
User selects disk, test type, and clicks "Start Test"
    │
    ▼
app.js: startTest()
    │
    ▼
HTTP POST /api/test/start
{
    test_type: "quick_max_mix",
    disk_path: "/Volumes/TestDisk",
    size_gb: 10
}
    │
    ▼
Bridge Server: start_test()
    │
    ├─► Validate test type mapping
    ├─► Generate unique test_id
    ├─► Store test state
    └─► Start background thread
            │
            ▼
        Execute diskbench command:
        python main.py --test quick_max_mix --disk /Volumes/TestDisk --size 10 --json --progress
            │
            ▼
        diskbench/commands/test.py: execute_builtin_test()
            │
            ├─► Get test pattern from qlab_patterns.py
            ├─► Create test directory
            ├─► Prepare FIO configuration
            └─► Execute FIO test
                    │
                    ▼
                core/fio_runner.py: run_fio_test()
                    │
                    ├─► Write FIO config file
                    ├─► Execute FIO process
                    ├─► Monitor progress
                    └─► Parse results
                            │
                            ▼
                        Process and analyze results
                            │
    ◄───────────────────────────┘
    │
    ▼
Polling loop: app.js: pollTestStatus()
    │
    ▼
HTTP GET /api/test/{test_id} (every 2 seconds)
    │
    ▼
Bridge returns test status and progress
    │
    ▼
Update UI progress bar and details
```

### 3. Test Completion Flow

```
FIO test completes
    │
    ▼
fio_runner.py processes results
    │
    ▼
qlab_patterns.py analyzes for QLab suitability
    │
    ▼
Results returned to bridge server
    │
    ▼
Bridge updates test state to "completed"
    │
    ▼
Next poll from Web GUI gets final results
    │
    ▼
app.js: showResults()
    │
    ├─► Display performance metrics
    ├─► Show QLab recommendations
    └─► Enable export functionality
```

## Test Types and Mapping

The system supports several test types with specific purposes:

### Web GUI Names → Diskbench Names

| Web GUI Display | Internal ID | Diskbench ID | Duration | Purpose |
|-----------------|-------------|--------------|----------|---------|
| Quick Max Performance | quick_max_speed | quick_max_mix | 5 min | Fast baseline test |
| QLab ProRes 422 Show | qlab_prores_422_show | prores_422_real | 30 min | Standard ProRes workflow |
| QLab ProRes HQ Show | qlab_prores_hq_show | prores_422_hq_real | 30 min | High-quality ProRes |
| Thermal Maximum | thermal_maximum_analyser | thermal_maximum | 60 min | Thermal throttling test |

### Test Pattern Details

Each test uses specific FIO patterns optimized for QLab workloads:

1. **quick_max_mix**:
   - 70/30 read/write mix
   - 4MB block size
   - 4 parallel jobs
   - Tests maximum mixed performance

2. **prores_422_real**:
   - Two-phase test: warmup + playback
   - Variable block sizes (1MB, 256KB, 16KB)
   - 98% read workload
   - Rate-limited to simulate real playback

3. **prores_422_hq_real**:
   - Higher bandwidth requirements
   - Larger block sizes (2MB, 512KB, 32KB)
   - 6 parallel jobs for heavier load
   - Simulates 4K ProRes HQ workflows

4. **thermal_maximum**:
   - Four-phase test with increasing load
   - Tests sustained performance over time
   - Identifies thermal throttling
   - Up to 12 parallel jobs

## State Management

### Bridge Server State

The bridge server maintains persistent state in `memory-bank/diskbench_bridge_state.json`:

```json
{
  "running_tests": {
    "test_1234567890": {
      "status": "running",
      "start_time": "2024-01-10T10:30:00",
      "params": {
        "test_type": "quick_max_speed",
        "disk_path": "/Volumes/TestDisk",
        "size_gb": 10
      },
      "diskbench_test_type": "quick_max_mix",
      "estimated_duration": 300,
      "progress": 45
    }
  },
  "last_updated": "2024-01-10T10:32:30"
}
```

### Test Status Lifecycle

```
starting → running → completed
    ↓         ↓          ↓
  failed   stopped    (success)
    ↓         ↓
  error    timeout

Special states:
- disconnected: Server restarted while test was running
- unknown: Test state cannot be determined
```

## Error Handling

### Web GUI
- Connection errors → Retry with exponential backoff
- API errors → User-friendly error messages
- Background test detection → Cleanup UI

### Bridge Server
- Process crashes → Mark test as failed
- Orphaned processes → Cleanup on startup
- State corruption → Safe fallback to empty state

### Diskbench
- FIO not found → Clear installation instructions
- Disk access denied → Permission error messages
- Insufficient space → Pre-flight validation

## Security Considerations

1. **Path Validation**: All disk paths are validated before use
2. **Command Injection**: FIO parameters are sanitized
3. **File Access**: Test files only in designated directories
4. **Process Isolation**: Each test runs in separate process
5. **Resource Limits**: Timeouts prevent runaway tests

## Performance Optimizations

1. **Polling Efficiency**: 2-second intervals during tests
2. **State Persistence**: Minimize disk writes
3. **Memory Usage**: Stream large results
4. **Process Management**: Clean process termination
5. **UI Updates**: Throttled progress updates

## Future Enhancements

Based on the refactoring plan in `grand-plan.md`:

1. **Simplified Setup**: Automated FIO installation
2. **Better Error Messages**: Context-aware help
3. **Quick Test Mode**: Faster evaluation option
4. **Visual Results**: Graphs and charts
5. **Export Options**: Multiple format support
6. **Stability Improvements**: Better timeout handling
