# QLab Disk Performance Tester - Visual Flow Diagram

## Complete System Information Flow

```mermaid
graph TB
    %% User Interface Layer
    subgraph "Web GUI (localhost:8080)"
        UI[User Interface]
        APP[app.js]
        UI --> APP
    end

    %% Bridge Server Layer
    subgraph "Bridge Server (localhost:8081)"
        API[HTTP API Handler]
        PM[Process Manager]
        STATE[State Persistence]
        API --> PM
        PM --> STATE
    end

    %% Diskbench CLI Layer
    subgraph "Diskbench CLI"
        MAIN[main.py]
        CMD[Commands]
        FIO[FIO Runner]
        PATTERNS[Test Patterns]
        MAIN --> CMD
        CMD --> FIO
        CMD --> PATTERNS
    end

    %% System Layer
    subgraph "System Resources"
        DISK[Disk Storage]
        FIOB[FIO Binary]
        FIO --> FIOB
        FIOB --> DISK
    end

    %% Main Flow Connections
    APP -->|HTTP Requests| API
    PM -->|subprocess.run| MAIN
    
    %% Specific Operations
    APP -->|GET /api/disks| API
    APP -->|POST /api/test/start| API
    APP -->|GET /api/test/{id}| API
    APP -->|POST /api/test/stop| API
    
    %% Data Flow Back
    API -.->|JSON Response| APP
    MAIN -.->|JSON Output| PM
    FIO -.->|Test Results| CMD
    DISK -.->|Performance Data| FIOB
```

## Detailed Test Execution Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web GUI
    participant B as Bridge Server
    participant D as Diskbench CLI
    participant F as FIO
    participant S as Storage

    %% Test Start
    U->>W: Select disk & test type
    U->>W: Click "Start Test"
    W->>B: POST /api/test/start
    Note over B: Generate test_id
    Note over B: Save to state file
    B->>D: python main.py --test [type]
    B-->>W: {test_id, status: "starting"}
    
    %% Test Execution
    D->>F: Execute FIO config
    F->>S: Read/Write operations
    
    %% Progress Updates
    loop Every 2 seconds
        W->>B: GET /api/test/{test_id}
        B-->>W: {progress, status, metrics}
        W->>U: Update progress bar
    end
    
    %% Test Completion
    S-->>F: Performance data
    F-->>D: Raw results
    Note over D: Process & analyze
    D-->>B: JSON results
    B-->>W: {status: "completed", results}
    W->>U: Display results
```

## Error Handling Flow

```mermaid
graph LR
    subgraph "Error Sources"
        E1[Connection Error]
        E2[FIO Not Found]
        E3[Disk Access Denied]
        E4[Test Timeout]
        E5[Process Crash]
    end

    subgraph "Error Handlers"
        H1[Retry Logic]
        H2[Setup Wizard]
        H3[Permission Help]
        H4[Cleanup Process]
        H5[State Recovery]
    end

    subgraph "User Feedback"
        F1[Error Message]
        F2[Action Button]
        F3[Help Documentation]
    end

    E1 --> H1 --> F1
    E2 --> H2 --> F2
    E3 --> H3 --> F3
    E4 --> H4 --> F1
    E5 --> H5 --> F1
```

## State Management Flow

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Starting: User starts test
    Starting --> Running: Process launched
    Running --> Completed: Test finishes
    Running --> Failed: Error occurs
    Running --> Stopped: User cancels
    Running --> Timeout: Time limit exceeded
    
    Completed --> Idle: Results shown
    Failed --> Idle: Error handled
    Stopped --> Idle: Cleanup done
    Timeout --> Idle: Process killed
    
    Running --> Disconnected: Server restart
    Disconnected --> Unknown: Cannot reconnect
    Disconnected --> Stopped: Manual cleanup
    Unknown --> Idle: Force cleanup
```

## Data Transformation Pipeline

```mermaid
graph LR
    subgraph "Input Stage"
        I1[Test Parameters]
        I2[Disk Selection]
        I3[Test Size]
    end

    subgraph "Processing Stage"
        P1[Parameter Validation]
        P2[FIO Config Generation]
        P3[Test Execution]
        P4[Result Parsing]
    end

    subgraph "Analysis Stage"
        A1[Performance Metrics]
        A2[QLab Suitability]
        A3[Recommendations]
    end

    subgraph "Output Stage"
        O1[JSON Results]
        O2[UI Display]
        O3[Export File]
    end

    I1 --> P1
    I2 --> P1
    I3 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> A1
    P4 --> A2
    A1 --> A3
    A2 --> A3
    A1 --> O1
    A2 --> O1
    A3 --> O1
    O1 --> O2
    O1 --> O3
```

## Component Communication Matrix

| From | To | Protocol | Data Format | Purpose |
|------|-----|----------|-------------|---------|
| Web GUI | Bridge Server | HTTP/JSON | REST API | Commands & queries |
| Bridge Server | Diskbench | subprocess | CLI args | Test execution |
| Diskbench | FIO | subprocess | Config file | Performance testing |
| FIO | Disk | System I/O | Binary | Actual disk operations |
| Diskbench | Bridge Server | stdout | JSON | Results return |
| Bridge Server | Web GUI | HTTP/JSON | REST API | Status & results |

## Key Information Elements

### 1. Test Configuration
```json
{
    "test_type": "quick_max_mix",
    "disk_path": "/Volumes/TestDisk",
    "size_gb": 10,
    "show_progress": true
}
```

### 2. Progress Update
```json
{
    "test_id": "test_1234567890",
    "status": "running",
    "progress": 45.2,
    "current_phase": "prores_422_playback",
    "elapsed_time": 234,
    "estimated_remaining": 156
}
```

### 3. Test Results
```json
{
    "test_info": {
        "test_mode": "quick_max_mix",
        "disk_path": "/Volumes/TestDisk",
        "timestamp": "2024-01-10T10:35:00"
    },
    "summary": {
        "total_read_iops": 45000,
        "total_write_iops": 15000,
        "total_read_bw": 1800,
        "total_write_bw": 600,
        "avg_read_latency": 0.8,
        "avg_write_latency": 1.2
    },
    "qlab_analysis": {
        "overall_performance": "excellent",
        "qlab_suitable": true,
        "recommended_streams": 8
    }
}
```

## Performance Bottlenecks & Optimizations

1. **Polling Overhead**: 2-second interval balances responsiveness vs. load
2. **JSON Parsing**: Streaming parser for large results
3. **Process Management**: Process groups for reliable cleanup
4. **State Persistence**: Write-through cache with periodic flush
5. **UI Rendering**: Virtual scrolling for large result sets

## Security Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    User Space                           │
│  ┌─────────────┐                                       │
│  │   Web GUI   │ ← Sandboxed browser environment       │
│  └─────────────┘                                       │
│         ↕ HTTP (localhost only)                        │
│  ┌─────────────┐                                       │
│  │Bridge Server│ ← Python process with limited privs   │
│  └─────────────┘                                       │
│         ↕ subprocess (controlled execution)            │
│  ┌─────────────┐                                       │
│  │  Diskbench  │ ← Validated paths, sanitized inputs   │
│  └─────────────┘                                       │
└─────────────────────────────────────────────────────────┘
           ↕ System calls (FIO)
┌─────────────────────────────────────────────────────────┐
│                   System Space                          │
│  ┌─────────────┐                                       │
│  │     FIO     │ ← Direct I/O operations               │
│  └─────────────┘                                       │
│         ↕                                              │
│  ┌─────────────┐                                       │
│  │Disk Hardware│ ← Physical storage access             │
│  └─────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```
