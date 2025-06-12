# GUI Context

## Purpose
Define the graphical user interface implementation for QLab Disk Performance Tester using PyQt6.

## Package Layout (PyQt6)
```
qlab_disk_tester/
├── __init__.py
├── main.py               # PyQt6 application entry point
├── cli.py                # Legacy CLI entrypoint (will be removed or adapted)
├── core/                 # Existing business logic (will be moved here from lib/)
│   ├── __init__.py
│   ├── disk_detector.py
│   ├── fio_engine.py
│   ├── qlab_analyzer.py
│   ├── report_generator.py
│   ├── binary_manager.py
│   └── live_monitor.py
├── gui_pyqt/             # PyQt6 GUI implementation
│   ├── __init__.py
│   ├── main_window.py    # Main PyQt6 window
│   ├── components/
│   │   ├── __init__.py
│   │   ├── drive_selector.py     # Drive selection and info display
│   │   ├── test_runner.py        # Test profile selection and start/stop
│   │   ├── live_chart.py         # Live throughput chart (PyQtGraph or QChart)
│   │   ├── progress_panel.py     # Progress bar and log output
│   │   └── results_viewer.py     # Display test results
│   └── styles/
│       ├── __init__.py
│       └── qss_styles.py         # PyQt6 stylesheets (QSS)
└── packaging/            # Application packaging scripts
    ├── __init__.py
    ├── build_app.py          # Script to build .app using PyInstaller
    └── Info.plist            # macOS application metadata
```

## GUI Features (PyQt6)
- **Modern UI**: Clean, responsive design with card-based layout and improved aesthetics.
- **Live Throughput Chart**: Real-time visualization of disk performance during tests.
- **Drive Selection**: Detailed drive information (capacity, free space, type) displayed.
- **Test Profiles**: Clear selection of QLab-specific test patterns with descriptions and durations.
- **Progress Monitoring**: Live progress bar and detailed log output.
- **Test Results**: Comprehensive display of key metrics and QLab suitability.
- **Application Packaging**: Creation of a standalone macOS .app bundle.

## Technical Notes (PyQt6)
- **Framework**: PyQt6 for rich, native-looking GUI.
- **Dependencies**: PyQt6, PyQt6-Charts (if using QChart), PyInstaller.
- **Threading**: Use QThread for non-blocking test execution and UI updates.
- **Styling**: Utilize Qt Style Sheets (QSS) for advanced theming.
- **FIO Integration**: Core logic will be moved to `qlab_disk_tester/core/` and accessed by GUI.
- **Live Charting**: Implement data streaming from FIO to QChart/PyQtGraph.
- **macOS .app**: PyInstaller will bundle Python interpreter, PyQt6, and all project files.
