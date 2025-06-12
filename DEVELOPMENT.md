# QLab Disk Performance Tester - Development Guide

This document is for developers who want to build, modify, or contribute to the QLab Disk Performance Tester.

## 🛠️ **Development Setup**

### Prerequisites
- **macOS 10.14+** (for building macOS apps)
- **Python 3.8+**
- **Git** (for version control)

### Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd qlab-disk-performance-tester

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies
```
PyQt6>=6.5.0          # GUI framework
pyinstaller>=5.13.0   # App bundling
Pillow>=10.0.0         # Icon conversion
```

## 🏗️ **Project Structure**

```
qlab_disk_tester/                    # Main application package
├── main.py                         # Application entry point
├── gui_pyqt/                       # PyQt6 user interface
│   ├── main_window.py              # Main GUI window
│   └── styles/                     # UI styling and themes
├── core/                           # Core disk testing engine
│   ├── disk_detector.py            # macOS drive detection
│   ├── python_disk_engine.py       # Pure Python testing engine
│   ├── temperature_monitor.py      # System monitoring
│   ├── qlab_analyzer.py            # QLab-specific analysis
│   └── report_generator.py         # Results processing
└── icon.png                       # Application icon

build_app.sh                        # Automated build script
qlab_disk_tester.spec              # PyInstaller configuration
requirements.txt                    # Python dependencies
memory-bank/                        # Development documentation
```

## 🚀 **Running in Development**

### Run the GUI Application
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python qlab_disk_tester/main.py
```

### Run Tests (if available)
```bash
# Run unit tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_disk_engine.py
```

## 📦 **Building the .app Bundle**

### Automated Build
```bash
# Make build script executable
chmod +x build_app.sh

# Build everything (recommended)
./build_app.sh
```

This creates:
- `dist/QLab Disk Performance Tester.app` - Standalone macOS application (77MB)
- `dist/*.dmg` - Professional DMG installer package
- `dist/*.zip` - ZIP distribution package

### Manual Build
```bash
# Activate virtual environment
source .venv/bin/activate

# Clean previous builds
rm -rf build/ dist/

# Build with PyInstaller
pyinstaller qlab_disk_tester.spec --clean --noconfirm
```

### Build Configuration

The `qlab_disk_tester.spec` file contains:
- **Hidden imports**: All required modules
- **Data files**: Icons and resources
- **Bundle settings**: macOS app metadata
- **Exclusions**: Unnecessary packages to reduce size

## 🔧 **Development Guidelines**

### Code Style
- **PEP 8** compliance for Python code
- **Type hints** where appropriate
- **Docstrings** for all public functions
- **Error handling** with proper exceptions

### Architecture Principles
- **Pure Python**: No external binary dependencies
- **Modular design**: Separate concerns into different modules
- **Cross-platform core**: Core engine should work on any OS
- **macOS GUI**: Platform-specific UI optimizations

### Testing Strategy
- **Unit tests** for core engine functions
- **Integration tests** for GUI components
- **Manual testing** on different Mac models
- **Performance validation** with real drives

## 🎨 **GUI Development**

### PyQt6 Components
- **Main Window**: `gui_pyqt/main_window.py`
- **Styles**: `gui_pyqt/styles/qss_styles.py`
- **Real-time Charts**: Custom PyQt6 widgets
- **Progress Monitoring**: Thread-safe UI updates

### Adding New Features
1. **Core Logic**: Add to appropriate `core/` module
2. **GUI Integration**: Update `gui_pyqt/main_window.py`
3. **Styling**: Add styles to `qss_styles.py`
4. **Testing**: Create tests for new functionality

## 🧪 **Testing the Engine**

### Disk Engine Testing
```python
from qlab_disk_tester.core.python_disk_engine import PythonDiskEngine

# Create engine instance
engine = PythonDiskEngine()

# Run a quick test
results = engine.run_test(
    drive_path="/path/to/test/drive",
    test_profile="setup_check",
    progress_callback=lambda p: print(f"Progress: {p}%")
)

print(results)
```

### Drive Detection Testing
```python
from qlab_disk_tester.core.disk_detector import DiskDetector

# Detect available drives
detector = DiskDetector()
drives = detector.get_available_drives()

for drive in drives:
    print(f"Drive: {drive['name']} - {drive['size']} - {drive['path']}")
```

## 📊 **Performance Optimization**

### App Bundle Size
- **Current size**: 77MB
- **Optimization**: Exclude unnecessary PyQt6 modules
- **Future**: Consider alternative GUI frameworks

### Runtime Performance
- **Threading**: All disk I/O in background threads
- **Memory**: Efficient buffer management
- **CPU**: Optimized I/O patterns for QLab simulation

## 🔄 **Release Process**

### Version Numbering
- **Format**: `v1.0.0` (semantic versioning)
- **Increment**: Major.Minor.Patch
- **Tagging**: Git tags for releases

### Creating a Release
1. **Update version** in relevant files
2. **Test thoroughly** on different Mac models
3. **Build .app bundle** with `./build_app.sh`
4. **Create release notes**
5. **Upload distribution files**

### Distribution Files
- **DMG**: For easy installation
- **ZIP**: For direct download
- **Checksums**: SHA256 for verification

## 🐛 **Debugging**

### Common Issues
- **PyQt6 import errors**: Check virtual environment
- **Permission denied**: Test with external drives
- **Build failures**: Check PyInstaller logs in `build/`

### Debug Mode
```bash
# Run with debug output
python qlab_disk_tester/main.py --debug

# PyInstaller debug build
pyinstaller qlab_disk_tester.spec --debug
```

### Logging
The application uses Python's logging module:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 **Memory Bank System**

The project uses a memory bank for development context:
- `memory-bank/projectbrief.md` - Project scope and goals
- `memory-bank/techContext.md` - Technical constraints
- `memory-bank/activeContext.md` - Current development status
- `memory-bank/progress.md` - Development history

## 🤝 **Contributing**

### Before Contributing
1. **Read the memory bank** files for context
2. **Follow the architecture** patterns
3. **Test on multiple Macs** if possible
4. **Update documentation** as needed

### Pull Request Process
1. **Fork** the repository
2. **Create feature branch** from main
3. **Make changes** with tests
4. **Update documentation**
5. **Submit pull request**

## 📄 **License**

This project is copyleft by **varga.media**. See LICENSE file for details.

## 🔗 **Resources**

- **PyQt6 Documentation**: https://doc.qt.io/qtforpython/
- **PyInstaller Guide**: https://pyinstaller.readthedocs.io/
- **macOS App Guidelines**: https://developer.apple.com/design/human-interface-guidelines/
- **QLab Documentation**: https://qlab.app/docs/

---

**Happy coding! 🚀**

*© 2025 varga.media - Professional QLab Solutions*
