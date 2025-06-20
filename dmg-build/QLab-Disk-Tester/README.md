# QLab Disk Performance Tester v1.3

Professional disk performance testing tool specifically designed for QLab video playback requirements.

## ✨ Key Features

- **QLab-Specific Tests**: ProRes 422/HQ show patterns (2.75 hours)
- **Quick Max Speed**: 3-minute maximum throughput test
- **Sustained Performance**: 1.5-hour thermal endurance testing
- **Web Interface**: Modern browser-based GUI
- **Real-time Monitoring**: Live performance metrics and progress
- **Comprehensive Reports**: Detailed analysis with QLab compatibility assessment

## 🎯 Architecture

**Clean & Simple Design:**
- **Python Standard Library**: HTTP server, JSON processing, subprocess management
- **FIO**: Industry-standard disk benchmarking tool
- **No External Python Dependencies**: Avoids pip install complications
- **Browser-based GUI**: Works with any modern web browser

## 📋 System Requirements

### **Required:**
- **macOS**: 10.14 or later
- **Python 3.7+**: Standard with macOS (no additional packages needed)
- **Homebrew**: Package manager for FIO installation
- **FIO**: Disk benchmarking tool (installed via Homebrew)

### **NOT Required:**
- ❌ Flask or other web frameworks
- ❌ External Python packages
- ❌ pip install (avoids Python 3.13+ "externally-managed-environment" issues)
- ❌ Virtual environments

## 🚀 Installation

### **Option 1: Automated Setup (Recommended)**

1. **Run Setup Script:**
   ```bash
   python3 setup.py
   ```

2. **What it does:**
   - ✅ Checks Python version
   - ✅ Installs/configures Homebrew (with Apple Silicon PATH fixes)
   - ✅ Installs FIO via Homebrew
   - ✅ Tests system compatibility
   - ✅ No pip install needed!

### **Option 2: Manual Setup**

If automated setup fails, install manually:

1. **Install Homebrew** (if not present):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Configure Homebrew PATH** (Apple Silicon Macs):
   ```bash
   echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
   eval "$(/opt/homebrew/bin/brew shellenv)"
   ```

3. **Install FIO**:
   ```bash
   brew install fio
   ```

## 🎬 Usage

### **Starting the Application**

1. **Launch:**
   ```bash
   ./start-disk-tester.sh
   ```
   Or double-click `start-disk-tester.sh` in Finder

2. **Access Web Interface:**
   - Opens automatically at: http://localhost:8765
   - Or manually navigate to the URL in your browser

### **Running Tests**

1. **Select Target Disk**: Choose the disk/volume to test
2. **Choose Test Type**:
   - **Quick Max Speed**: 3-minute maximum throughput test
   - **QLab ProRes 422 Show**: 2.75-hour realistic show pattern
   - **QLab ProRes HQ Show**: 2.75-hour high-quality show pattern
   - **Max Sustained**: 1.5-hour thermal endurance test
3. **Start Test**: Monitor real-time progress and metrics
4. **Review Results**: Detailed performance analysis and QLab compatibility

## 🔧 Technical Details

### **Test Patterns**

- **Quick Max Speed**: Sequential read test for maximum throughput measurement
- **QLab Show Patterns**: Realistic video playback simulation with:
  - 1x4K + 3xHD ProRes streams
  - Crossfades and transitions
  - Variable load patterns
- **Sustained Tests**: Continuous maximum load for thermal testing

### **Performance Thresholds**

- **ProRes 422**: Minimum 220 MB/s sustained
- **ProRes HQ**: Minimum 440 MB/s sustained
- **4K Playback**: Minimum 100 MB/s for basic compatibility

### **Architecture Components**

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Web Browser   │◄──►│ Bridge Server│◄──►│  diskbench  │
│   (Frontend)    │    │ (Python HTTP)│    │   (FIO)     │
└─────────────────┘    └──────────────┘    └─────────────┘
```

- **Web Browser**: Modern HTML5/JavaScript interface
- **Bridge Server**: Python Standard Library HTTP server
- **diskbench**: FIO wrapper with QLab-specific patterns

## 🛠️ Troubleshooting

### **Common Issues**

**"Homebrew not found"**
- Install Homebrew using the command in Manual Setup
- Restart terminal after installation

**"FIO not found" (Apple Silicon)**
- Run: `echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile`
- Restart terminal and re-run setup

**"externally-managed-environment" (Python 3.13+)**
- ✅ Not an issue! This app uses no external Python packages
- No pip install required

**"Permission denied"**
- Run setup with: `sudo python3 setup.py`
- Or manually install Homebrew first

### **Advanced Troubleshooting**

**FIO Shared Memory Issues**
- The bridge server automatically detects and handles FIO shared memory limitations
- Falls back to compatible parameters on macOS

**Port 8765 in use**
- Change port in `bridge-server/server.py` if needed
- Or stop other services using the port

## 📊 Understanding Results

### **Performance Metrics**

- **Throughput**: MB/s sustained read speed
- **IOPS**: Input/Output operations per second
- **Latency**: Response time for disk operations
- **Consistency**: Performance stability over time

### **QLab Compatibility**

- **✅ Show Ready**: Meets all QLab requirements
- **⚠️ Marginal**: May work but with limited headroom
- **❌ Insufficient**: Does not meet minimum requirements

## 📝 Version History

### **v1.3 (Current)**
- ✅ Removed Flask dependencies (uses Python Standard Library)
- ✅ Fixed Python 3.13+ "externally-managed-environment" issues
- ✅ Simplified installation (no pip install required)
- ✅ Enhanced Apple Silicon Homebrew PATH handling
- ✅ Improved setup script with better error messages

### **v1.2**
- Enhanced setup script with retry logic
- Apple Silicon Homebrew PATH auto-configuration
- Improved error handling and user feedback

### **v1.1**
- Initial DMG package release
- Basic setup automation

## 🔗 Support

For issues or questions:
1. Check this README for common solutions
2. Review setup script output for specific error messages
3. Ensure Homebrew and FIO are properly installed
4. Verify Python 3.7+ is available

## 📄 License

See LICENSE.txt for licensing information.
