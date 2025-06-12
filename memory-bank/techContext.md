## Context: QLab Disk Performance Tester Development and Optimization

### 1. Previous Conversation:
The conversation began with debugging a QLab Disk Performance Tester that was showing 0 MB/s bandwidth and 0 IOPS in test results. We systematically identified and resolved multiple technical issues including fio output capture problems, bandwidth calculation errors, binary compatibility issues, and JSON parsing failures. The conversation evolved from basic bug fixes to comprehensive feature enhancement, culminating in implementing live monitoring capabilities and realistic ProRes 422 test scenarios for professional QLab workflows.

### 2. Current Work:
The final phase involved implementing live monitoring with SSD temperature display using powermetrics, simplifying test modes from 4 to 3 streamlined options, and creating realistic show-pattern tests. Key accomplishments included:
- Created `LiveMonitor` class for real-time SSD temperature and I/O monitoring
- Redesigned test modes: Setup Check (30s), QLab Show-Pattern Test (2.5h multi-phase), Max Sustained Performance (2h)
- Updated test specifications for ProRes 422 workflows (656 MB/s normal, 2100 MB/s crossfade peaks)
- Integrated live monitoring into the main application with keyboard interrupt safety
- **CONVERTED TO STANDALONE PACKAGE**: No external dependencies, works on fresh Apple Silicon Macs

### 3. Key Technical Concepts:
- **fio (Flexible I/O Tester)** - **MANDATORY TOOL**: All disk benchmarking relies on fio with JSON output parsing
- **Apple Silicon ONLY**: Exclusively supports ARM64 architecture (M1/M2/M3 Macs)
- **macOS storage detection** using system_profiler and diskutil
- **ProRes 422 streaming requirements** (440 MB/s 4K + 72 MB/s HD streams)
- **Live monitoring** via powermetrics and native macOS thermal estimation
- **Multi-phase testing** simulating real QLab show patterns
- **Thermal throttling detection** and performance degradation monitoring
- **Python subprocess management** with background threading
- **Standalone deployment** with bundled fio binary for Apple Silicon
- **GUI Framework**: PyQt6 for modern, interactive user interface
- **Zero external dependencies (core logic)** - Python standard library only (GUI adds PyQt6)

### 4. MANDATORY TECHNICAL CONSTRAINTS:
- **fio REQUIREMENT**: All disk benchmarking MUST use fio - no alternatives
- **Apple Silicon ONLY**: No Intel (x86_64) support - ARM64 exclusive
- **Standard Library ONLY**: No external Python dependencies (no pip packages)
- **Standalone Operation**: Must work on fresh macOS installs without internet
- **macOS Native APIs**: powermetrics, pmset for system monitoring

### 5. Relevant Files and Code:
- **qlab-disk-tester/lib/fio_engine.py**
  - Core fio integration with JSON output parsing
  - Multi-phase test configurations for QLab scenarios
  - Apple Silicon fio binary management
  ```python
  def execute_fio_test(self, test_mode, disk_path, test_size_gb, live_monitor=None):
  ```

- **qlab-disk-tester/lib/live_monitor.py**
  - Real-time monitoring using macOS native APIs only
  - No smartctl dependency - uses pmset thermal estimation
  - Background threading for non-blocking updates
  ```python
  def _estimate_temp_from_thermal_state(self):
  ```

- **qlab-disk-tester/lib/qlab_analyzer.py**
  - ProRes 422 specifications and performance thresholds
  - Performance ratings: 2100 MB/s (Excellent), 656 MB/s (Acceptable)

- **qlab-disk-tester/bin/fio-apple-silicon**
  - Bundled fio binary for ARM64 architecture only

### 6. Project Architecture Requirements:
- **Apple Silicon Focus**: All development targets M1/M2/M3 Macs exclusively
- **fio Integration**: fio is the only supported disk testing engine
- **Standalone Package**: Bundled with PyInstaller for macOS .app
- **Professional Grade**: Built for QLab production environments
- **Thermal Awareness**: Continuous monitoring for long-duration tests

### 7. Performance Standards (ProRes 422):
- Normal Operation: 656 MB/s (1x 4K + 3x HD streams)
- Crossfade Peaks: 2100 MB/s (with safety buffer)
- Test Durations: 30s (setup), 2.5h (show pattern), 2h (sustained max)

### 8. Deployment Model:
- Standalone tar.gz package
- Single fio binary for Apple Silicon
- Install script with architecture verification
- No internet required for operation
- Professional documentation for QLab technicians

**CORE PRINCIPLE**: This tool is fio-based, Apple Silicon exclusive, and designed for professional QLab environments with zero external dependencies.

## 9. Best FIO CLI Status Monitoring for macOS

- macOS requires `--ioengine=posixaio` for optimal compatibility.
- Use `--status-interval=N`, `--eta-newline=N`, and `--eta=always` to control FIO’s native status reporting.
- `--eta-interval=N` for high-frequency ETA updates.

**Example one-liners:**

```bash
fio --name=macos-test --ioengine=posixaio --rw=randrw --bs=4k --size=4G \
    --filename=/tmp/fio_test --direct=1 --runtime=300 --time_based \
    --eta=always --eta-newline=5 --status-interval=10
```

```bash
fio --name=benchmark --ioengine=posixaio --rw=randwrite --bs=32k \
    --size=8G --filename=/tmp/test --direct=1 --runtime=600 --time_based \
    --status-interval=5 --output-format=json --write_bw_log=bw \
    --write_lat_log=lat --write_iops_log=iops --log_avg_msec=1000
```

```bash
sudo fio --name=device-test --ioengine=posixaio --filename=/dev/rdisk2 \
    --direct=1 --rw=randread --bs=4k --iodepth=64 --runtime=120 \
    --time_based --eta-newline=2 --status-interval=15 \
    --group_reporting --readonly
```

**Shell integration (zsh):**

```zsh
function fio_monitor() {
    local test_file=${1:-/tmp/fio_test}
    local test_size=${2:-4G}
    local runtime=${3:-300}
    fio --name=monitor --ioengine=posixaio --rw=randrw --bs=4k \
        --size="$test_size" --filename="$test_file" --direct=1 \
        --runtime="$runtime" --time_based --eta=always --eta-newline=2 \
        --status-interval=10 --write_bw_log=monitor_bw \
        --write_lat_log=monitor_lat --log_avg_msec=1000
}
```

- Kombiniere FIO mit `iostat` oder `top` für erweiterte Systemüberwachung:
```bash
fio --name=disk-test --ioengine=posixaio ... & iostat -w 2 disk0
```
