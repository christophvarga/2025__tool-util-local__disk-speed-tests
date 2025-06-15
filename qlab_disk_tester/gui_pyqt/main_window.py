import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QProgressBar, QFrame, QTextEdit, QMessageBox
)
from PyQt6.QtGui import QPainter, QIcon
from PyQt6.QtCore import QTimer, QPointF, Qt, QObject, pyqtSignal
import threading
import time
import re
import json
import subprocess

from qlab_disk_tester.core.disk_detector import DiskDetector
from qlab_disk_tester.core.fio_manager import FioManager
from qlab_disk_tester.core.real_temperature_monitor import RealTemperatureMonitor
from qlab_disk_tester.gui_pyqt.styles.qss_styles import QSS_STYLES
from qlab_disk_tester.gui_pyqt.components.debug_terminal import DebugTerminal

class MainWindow(QMainWindow):
    test_finished_signal = pyqtSignal(str) # Signal to indicate test completion, with results as string
    log_update_signal = pyqtSignal(str) # Signal for thread-safe log updates
    progress_update_signal = pyqtSignal(int, float, int) # Signal for progress updates (progress%, throughput, iops)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QLab Disk Performance Tester")
        self.setMinimumSize(900, 700) # Increased size for better layout
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main vertical layout for the entire window content
        self.overall_layout = QVBoxLayout(self.central_widget)
        self.overall_layout.setContentsMargins(0, 0, 0, 0) # No margins for the overall layout
        self.overall_layout.setSpacing(0) # No spacing between header and main content

        # Apply stylesheet to the application
        self.setStyleSheet(QSS_STYLES)

        # Production-safe engines - FIO first, no fallbacks
        self.fio_manager = FioManager()
        self.disk_detector = DiskDetector()
        self.temperature_monitor = RealTemperatureMonitor()
        
        # Check system status at startup
        self.fio_status = self.fio_manager.get_fio_status()
        self.temp_status = self.temperature_monitor.get_temperature_status()
        
        # Temperature monitoring
        self.current_temperature = None
        # Performance tracking
        self.current_throughput = 0.0
        self.current_iops = 0

        self._create_header() # This will add to overall_layout

        # Main horizontal layout for the content below the header
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10) # Margins for content
        self.content_layout.setSpacing(10) # Spacing between left and right panels
        self.overall_layout.addLayout(self.content_layout)

        # Left Panel (Drive Selection, Test Configuration)
        self.left_panel = QVBoxLayout()
        self.left_panel.setContentsMargins(0, 0, 0, 0) # No margins for inner panels
        self.left_panel.setSpacing(10) # Spacing between cards
        self.content_layout.addLayout(self.left_panel, 1) # Takes 1/3 of space

        # Right Panel (Live Progress, Results)
        self.right_panel = QVBoxLayout()
        self.right_panel.setContentsMargins(0, 0, 0, 0) # No margins for inner panels
        self.right_panel.setSpacing(10) # Spacing between cards
        self.content_layout.addLayout(self.right_panel, 2) # Takes 2/3 of space

        self._create_drive_selection_card()
        self._create_test_configuration_card()
        self._create_live_progress_card()
        self._create_results_card()
        self._create_debug_terminal()

        # Test state
        self.running = False

        # Connect signals for thread-safe UI updates
        self.test_finished_signal.connect(self._handle_test_finished_on_main_thread)
        self.log_update_signal.connect(self._handle_log_update_on_main_thread)
        self.progress_update_signal.connect(self._handle_progress_update_on_main_thread)

    def _create_header(self):
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame") # For QSS styling
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel("QLab Disk Performance Tester - Production Safe")
        title_label.setObjectName("TitleLabel")
        header_layout.addWidget(title_label)

        # Production-safe status display
        if self.fio_status['available']:
            fio_text = f"✅ FIO Ready ({self.fio_status['version']})"
            fio_color = "color: green;"
        else:
            fio_text = "❌ FIO Missing - No real tests possible"
            fio_color = "color: red;"
        
        self.engine_status_label = QLabel(fio_text)
        self.engine_status_label.setObjectName("EngineStatusLabel")
        self.engine_status_label.setStyleSheet(fio_color)
        header_layout.addWidget(self.engine_status_label)

        # Temperature status
        if self.temp_status['available']:
            temp_text = "🌡️ Temp Monitor Ready"
            temp_color = "color: green;"
        else:
            temp_text = "🌡️ Temp Monitor Limited"
            temp_color = "color: orange;"
        
        self.temp_status_label = QLabel(temp_text)
        self.temp_status_label.setObjectName("TempStatusLabel")
        self.temp_status_label.setStyleSheet(temp_color)
        header_layout.addWidget(self.temp_status_label)

        # Add header to the overall vertical layout
        self.overall_layout.addWidget(header_frame)
        self.setMenuBar(None) # Remove default menu bar if not needed


    def _create_drive_selection_card(self):
        card_frame = QFrame()
        card_frame.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("1. Select Target Drive")
        title_label.setObjectName("CardTitleLabel")
        card_layout.addWidget(title_label)

        # Drive selection combobox
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Drive:"))
        self.drive_combo = QComboBox()
        self.drive_combo.setMinimumWidth(300)
        drive_layout.addWidget(self.drive_combo)
        drive_layout.addStretch() # Push combobox to left
        card_layout.addLayout(drive_layout)

        # Drive info display (simplified for now)
        self.drive_info_label = QLabel("Selected Drive Info: N/A")
        card_layout.addWidget(self.drive_info_label)
        
        # Populate drives after drive_info_label is initialized
        self._populate_drives()

        self.left_panel.addWidget(card_frame)
        self.left_panel.setContentsMargins(0, 0, 0, 0) # Remove default margins

    def _populate_drives(self):
        drives_info = self.disk_detector.get_large_drives()
        self.drive_options = []
        display_values = []
        for d in drives_info:
            display_name = f"{d.get('Name', 'Unknown')} ({d.get('Mount Point', 'Unknown')})"
            self.drive_options.append({'display': display_name, 'data': d})
            display_values.append(display_name)

        self.drive_combo.addItems(display_values)
        if self.drive_options:
            self.drive_combo.setCurrentIndex(0)
            self._on_drive_selected(0) # Trigger initial display
        self.drive_combo.currentIndexChanged.connect(self._on_drive_selected)

    def _on_drive_selected(self, index):
        if index >= 0 and index < len(self.drive_options):
            selected_data = self.drive_options[index]['data']
            info_text = (
                f"Name: {selected_data.get('Name', 'N/A')}\n"
                f"Capacity: {selected_data.get('Capacity', 'N/A')}\n"
                f"Free Space: {selected_data.get('Free', 'N/A')}\n"
                f"Type: {selected_data.get('Type', 'N/A')}"
            )
            self.drive_info_label.setText(info_text)
        else:
            self.drive_info_label.setText("Selected Drive Info: N/A")

    def _on_profile_selected(self, profile_name):
        """Update profile description when a new profile is selected."""
        descriptions = {
            "Setup Check": (
                "🔧 SETUP CHECK (10 minutes)\n"
                "• Quick write test (5 min) + read test (5 min)\n"
                "• Verifies basic disk functionality\n"
                "• Ideal for initial compatibility testing\n"
                "• Uses 1GB test files with 64KB/4KB blocks"
            ),
            "QLab ProRes 422 Pattern": (
                "🎬 QLAB PRORES 422 PATTERN (2.75 hours)\n"
                "• Phase 1: Normal load (30 min) - 656 MB/s baseline\n"
                "• Phase 2: Show simulation (1.5h) - Crossfades every 3 min to 2100 MB/s\n"
                "• Phase 3: Thermal recovery (30 min) - Return to baseline\n"
                "• Phase 4: Max speed test (5 min) - Absolute peak performance\n"
                "• Simulates 4x video streams (1x 4K + 3x HD) with realistic QLab workload"
            ),
            "QLab ProRes HQ Pattern": (
                "🎭 QLAB PRORES HQ PATTERN (2.75 hours)\n"
                "• Phase 1: Normal load (30 min) - 950 MB/s baseline\n"
                "• Phase 2: Show simulation (1.5h) - Crossfades every 3 min to 3200 MB/s\n"
                "• Phase 3: Thermal recovery (30 min) - Return to baseline\n"
                "• Phase 4: Max speed test (5 min) - Absolute peak performance\n"
                "• High-quality ProRes HQ simulation for premium productions"
            ),
            "Max Sustained": (
                "🚀 MAX SUSTAINED THROUGHPUT (2 hours)\n"
                "• Continuous maximum speed test\n"
                "• Uses 4x 2GB files with 1MB blocks\n"
                "• Round-robin reading for sustained load\n"
                "• Measures absolute peak performance over time\n"
                "• Tests thermal throttling and sustained capability"
            )
        }
        
        description = descriptions.get(profile_name, "Select a test profile to see details...")
        self.profile_description.setText(description)

    def _create_test_configuration_card(self):
        card_frame = QFrame()
        card_frame.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("2. Configure Test")
        title_label.setObjectName("CardTitleLabel")
        card_layout.addWidget(title_label)

        # Test profile selection with descriptions
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems([
            "Setup Check", "QLab ProRes 422 Pattern", "QLab ProRes HQ Pattern", "Max Sustained"
        ])
        self.profile_combo.currentTextChanged.connect(self._on_profile_selected)
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addStretch()
        card_layout.addLayout(profile_layout)

        # Profile description area
        self.profile_description = QLabel("Select a test profile to see details...")
        self.profile_description.setWordWrap(True)
        self.profile_description.setMinimumHeight(100)
        self.profile_description.setObjectName("ProfileDescription")
        card_layout.addWidget(self.profile_description)
        
        # Set initial profile description
        self._on_profile_selected("Setup Check")

        # Start/Stop Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Test")
        self.start_button.setObjectName("StartButton")
        self.start_button.clicked.connect(self._on_start_test)
        self.stop_button = QPushButton("Stop Test")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_test)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        card_layout.addLayout(button_layout)

        self.left_panel.addWidget(card_frame)
        self.left_panel.addStretch() # Push cards to top

    def _create_live_progress_card(self):
        card_frame = QFrame()
        card_frame.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("3. Live Progress")
        title_label.setObjectName("CardTitleLabel")
        card_layout.addWidget(title_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        card_layout.addWidget(self.progress_bar)

        # Live Performance Display
        self.performance_display = QLabel("Throughput: -- MB/s | IOPS: -- | SSD Temp: --")
        self.performance_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.performance_display.setMinimumHeight(80)  # Increased height
        self.performance_display.setMaximumHeight(120)  # Set max height
        self.performance_display.setWordWrap(True)  # Enable word wrapping
        self.performance_display.setObjectName("PerformanceDisplay")
        self.performance_display.setStyleSheet("""
            QLabel#PerformanceDisplay {
                background-color: #f0f0f0;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }
        """)
        card_layout.addWidget(self.performance_display)
        
        # Start temperature monitoring only if available
        def temp_callback(temp):
            self.current_temperature = temp
        
        if self.temp_status['available']:
            self.temperature_monitor.start_monitoring(temp_callback)

        # Log Output (using QTextEdit for better scrolling and text display)
        self.log_output = QTextEdit("Ready to start test...")
        self.log_output.setReadOnly(True)
        self.log_output.setObjectName("LogOutputLabel") # For QSS styling
        card_layout.addWidget(self.log_output, 1) # Add stretch factor

        self.right_panel.addWidget(card_frame)
        self.right_panel.setContentsMargins(0, 0, 0, 0) # Remove default margins

        # Chart update timer
        self.chart_timer = QTimer()
        self.chart_timer.setInterval(1000) # Update every 1 second
        self.chart_timer.timeout.connect(self._update_chart)
        self.chart_data = [] # Stores (timestamp, value)

    def _create_results_card(self):
        card_frame = QFrame()
        card_frame.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("4. Test Results")
        title_label.setObjectName("CardTitleLabel")
        card_layout.addWidget(title_label)

        self.results_text = QTextEdit("Results will appear here after test completion.")
        self.results_text.setReadOnly(True)
        self.results_text.setObjectName("ResultsTextLabel") # For QSS styling
        card_layout.addWidget(self.results_text, 1) # Add stretch factor

        self.right_panel.addWidget(card_frame)
        self.right_panel.addStretch() # Push cards to top

    def _create_debug_terminal(self):
        """Create and add the debug terminal to the bottom of the window."""
        self.debug_terminal = DebugTerminal()
        self.overall_layout.addWidget(self.debug_terminal)
        
        # Log startup information
        self.debug_terminal.log_info("QLab Disk Performance Tester initialized")
        self.debug_terminal.log_debug(f"FIO Status: {self.fio_status}")
        self.debug_terminal.log_debug(f"Temperature Monitor: {self.temp_status}")
        self.debug_terminal.log_debug(f"Available drives: {len(self.drive_options)}")

    def _on_start_test(self):
        # Production-safe pre-flight checks
        if not self.fio_status['available']:
            QMessageBox.critical(self, "FIO Not Available", 
                               f"Cannot perform real disk tests without FIO.\n\n"
                               f"Error: {self.fio_status['error']}\n\n"
                               f"Installation Guide:\n" + 
                               "\n".join(self.fio_status.get('installation_guide', [])))
            return
        
        # Validate drive selection
        selected_drive_index = self.drive_combo.currentIndex()
        if selected_drive_index == -1 or not self.drive_options:
            QMessageBox.critical(self, "No Drive Selected", 
                               "Please select a target drive for testing.\n\n"
                               "If no drives appear in the list, check that you have\n"
                               "external drives connected or sufficient free space.")
            return

        selected_drive_data = self.drive_options[selected_drive_index]['data']
        selected_drive_path = selected_drive_data.get('Mount Point')
        
        if not selected_drive_path or not os.path.exists(selected_drive_path):
            QMessageBox.critical(self, "Invalid Drive Path", 
                               f"Selected drive path is invalid: {selected_drive_path}\n\n"
                               "Please select a different drive.")
            return
        
        # Test write permissions
        test_file_path = os.path.join(selected_drive_path, 'qlab_test_permissions')
        try:
            with open(test_file_path, 'w') as f:
                f.write('test')
            os.remove(test_file_path)
        except Exception as e:
            QMessageBox.critical(self, "Permission Error", 
                               f"Cannot write to selected drive: {selected_drive_path}\n\n"
                               f"Error: {e}\n\n"
                               "Please check drive permissions or select a different drive.")
            return
        
        # Check available space
        try:
            import shutil
            free_space_bytes = shutil.disk_usage(selected_drive_path).free
            free_space_gb = free_space_bytes / (1024**3)
            if free_space_gb < 5:  # Need at least 5GB for tests
                QMessageBox.warning(self, "Low Disk Space", 
                                   f"Selected drive has only {free_space_gb:.1f}GB free space.\n\n"
                                   "At least 5GB is recommended for reliable testing.\n"
                                   "Continue anyway?")
        except:
            pass  # Continue if we can't check space
        
        # Reset performance metrics
        self.current_throughput = 0.0
        self.current_iops = 0
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Enhanced logging with debug info
        debug_info = [
            "🚀 STARTING REAL DISK TEST WITH FIO",
            f"📁 Target Drive: {selected_drive_data.get('Name', 'Unknown')}",
            f"📂 Mount Point: {selected_drive_path}",
            f"💾 Free Space: {selected_drive_data.get('Free', 'Unknown')}",
            f"🔧 FIO Path: {self.fio_manager.fio_path}",
            f"📊 Test Profile: {self.profile_combo.currentText()}",
            "─" * 50
        ]
        self.log_output.setText("\n".join(debug_info))
        
        self.results_text.setText("Results will appear here after test completion.")
        self.chart_data = []
        self.chart_timer.start()

        test_mode = self.profile_combo.currentText()

        # Map profile name to test mode
        test_mode_map = {
            "Setup Check": "setup_check",
            "QLab ProRes 422 Pattern": "qlab_pattern",
            "QLab ProRes HQ Pattern": "qlab_hq_pattern",
            "Max Sustained": "baseline_streaming"
        }
        test_mode_internal = test_mode_map.get(test_mode, "setup_check")

        # Execute REAL FIO disk test in a separate thread
        self.running = True
        self.test_thread = threading.Thread(target=self._run_real_fio_test_threaded, args=(test_mode_internal, selected_drive_path, 2))
        self.test_thread.daemon = True
        self.test_thread.start()

    def _run_real_fio_test_threaded(self, test_mode, disk_path, test_size_gb):
        """Execute REAL FIO disk tests in a separate thread."""
        try:
            # Use a production-safe monitor with enhanced error handling
            class ProductionMonitor:
                def __init__(self, parent_window):
                    self.parent_window = parent_window
                    self.start_time = time.time()
                    self.total_runtime = 0
                    self.log_messages = []

                def set_test_phase(self, phase_name, runtime):
                    self.total_runtime = runtime
                    message = f"🔥 REAL TEST: {phase_name} (Runtime: {runtime}s)"
                    self.log_messages.append(message)
                    self._update_log_display()

                def log_error(self, error_message):
                    """Log error messages for display in the GUI"""
                    self.log_messages.append(f"❌ ERROR: {error_message}")
                    self._update_log_display()

                def _update_log_display(self):
                    """Update the log display with all messages using signals"""
                    if len(self.log_messages) > 30:  # Keep more messages for debugging
                        self.log_messages = self.log_messages[-30:]
                    
                    log_text = "\n".join(self.log_messages)
                    self.parent_window.log_update_signal.emit(log_text)

                def update_with_fio_data(self, line):
                    # Log ALL FIO output for debugging
                    clean_line = line.strip()
                    if clean_line:  # Only log non-empty lines
                        self.log_messages.append(f"FIO: {clean_line}")
                    
                    # Parse real FIO performance data
                    # Look for FIO patterns like "read: IOPS=1234, BW=500MiB/s"
                    fio_match = re.search(r'read:.*?BW=(\d+\.?\d*)([KMGT]?i?B/s)', line)
                    if fio_match:
                        bw_value = float(fio_match.group(1))
                        bw_unit = fio_match.group(2)
                        
                        # Convert to MB/s
                        if 'KiB/s' in bw_unit or 'KB/s' in bw_unit:
                            mbps = bw_value / 1024
                        elif 'MiB/s' in bw_unit or 'MB/s' in bw_unit:
                            mbps = bw_value
                        elif 'GiB/s' in bw_unit or 'GB/s' in bw_unit:
                            mbps = bw_value * 1024
                        else:
                            mbps = bw_value
                        
                        # Extract IOPS if available
                        iops_match = re.search(r'IOPS=(\d+)', line)
                        iops = int(iops_match.group(1)) if iops_match else int(mbps * 256)
                        
                        # Use signal for thread-safe progress update
                        self.parent_window.progress_update_signal.emit(0, mbps, iops)
                    
                    self._update_log_display()

            monitor = ProductionMonitor(self)
            
            # Enhanced pre-test logging
            monitor.log_messages.append("🚀 THREAD STARTED: FIO disk performance test")
            monitor.log_messages.append(f"📁 Target Directory: {disk_path}")
            monitor.log_messages.append(f"📊 Test Mode: {test_mode}")
            monitor.log_messages.append(f"💾 Test Size: {test_size_gb}GB")
            monitor.log_messages.append(f"🔧 FIO Manager Status: {self.fio_manager.get_fio_status()}")
            monitor._update_log_display()
            
            # Test directory access before starting FIO
            try:
                test_access_file = os.path.join(disk_path, 'qlab_access_test')
                with open(test_access_file, 'w') as f:
                    f.write('access test')
                os.remove(test_access_file)
                monitor.log_messages.append(f"✅ Directory access confirmed: {disk_path}")
                monitor._update_log_display()
            except Exception as access_error:
                monitor.log_error(f"Directory access failed: {access_error}")
                self.test_finished_signal.emit(f"❌ Cannot access target directory: {access_error}")
                return
            
            # Check if FIO manager is properly initialized
            if not self.fio_manager.is_fio_available():
                fio_status = self.fio_manager.get_fio_status()
                monitor.log_error(f"FIO not available: {fio_status}")
                self.test_finished_signal.emit(f"❌ FIO not available: {fio_status.get('error', 'Unknown error')}")
                return
            
            monitor.log_messages.append("🔥 Starting FIO execution...")
            monitor._update_log_display()
            
            # Execute FIO test with enhanced error handling
            results = self.fio_manager.execute_real_disk_test(test_mode, disk_path, test_size_gb, monitor=monitor)
            
            # Enhanced result handling
            if results:
                monitor.log_messages.append("✅ FIO test completed successfully")
                monitor._update_log_display()
                self.test_finished_signal.emit(json.dumps(results, indent=2))
            else:
                monitor.log_error("FIO test returned no results")
                self.test_finished_signal.emit("❌ FIO test failed - no results returned")

        except Exception as e:
            # Enhanced exception handling with full traceback
            import traceback
            error_details = traceback.format_exc()
            error_message = f"❌ THREAD EXCEPTION: {e}\n\nFull traceback:\n{error_details}"
            
            # Try to emit the error, but handle if that fails too
            try:
                self.test_finished_signal.emit(error_message)
            except Exception as signal_error:
                print(f"Failed to emit error signal: {signal_error}")
                print(f"Original error: {error_message}")
        
        finally:
            # Ensure UI is reset even if everything fails
            try:
                self.log_update_signal.emit("🔄 Test thread finished (cleanup)")
            except:
                pass

    def _run_python_test_threaded(self, test_mode, disk_path, test_size_gb):
        try:
            # Use a simple monitor for now, will integrate LiveMonitor later
            class SimpleMonitor:
                def __init__(self, parent_window):
                    self.parent_window = parent_window
                    self.start_time = time.time()
                    self.total_runtime = 0 # Will be updated by fio output
                    self.log_messages = [] # Store all log messages

                def set_test_phase(self, phase_name, runtime):
                    self.total_runtime = runtime
                    message = f"Phase: {phase_name} (Runtime: {runtime}s)"
                    self.log_messages.append(message)
                    self._update_log_display()

                def log_error(self, error_message):
                    """Log error messages for display in the GUI"""
                    self.log_messages.append(f"ERROR: {error_message}")
                    self._update_log_display()

                def _update_log_display(self):
                    """Update the log display with all messages using signals"""
                    # Keep only last 20 messages to prevent overflow
                    if len(self.log_messages) > 20:
                        self.log_messages = self.log_messages[-20:]
                    
                    log_text = "\n".join(self.log_messages)
                    # Use signal for thread-safe UI update
                    self.parent_window.log_update_signal.emit(log_text)

                def update_with_fio_data(self, line):
                    # Log all output for debugging
                    self.log_messages.append(f"{line.strip()}")
                    
                    # Parse performance data from Python engine output
                    # Look for patterns like "Progress: 50.0% | Read: 1024.0 MB/s | Target: 656 MB/s"
                    progress_match = re.search(r'Progress:\s*(\d+\.?\d*)%.*?Read:\s*(\d+\.?\d*)\s*MB/s.*?Target:\s*(\d+\.?\d*)\s*MB/s', line)
                    if progress_match:
                        progress_percent = float(progress_match.group(1))
                        read_mbps = float(progress_match.group(2))
                        target_mbps = float(progress_match.group(3))
                        
                        # Use signal for thread-safe progress update
                        self.parent_window.progress_update_signal.emit(int(progress_percent), read_mbps, int(read_mbps * 256))
                    
                    # Also look for simple throughput patterns
                    simple_match = re.search(r'Read:\s*(\d+\.?\d*)\s*MB/s', line)
                    if simple_match and not progress_match:
                        read_mbps = float(simple_match.group(1))
                        # Use signal for thread-safe progress update
                        self.parent_window.progress_update_signal.emit(0, read_mbps, int(read_mbps * 256))
                    
                    self._update_log_display()

                def _convert_to_mbps(self, value, unit):
                    if 'KiB/s' in unit: return value / 1024
                    if 'MiB/s' in unit: return value
                    if 'GiB/s' in unit: return value * 1024
                    if 'TiB/s' in unit: return value * (1024**2)
                    return value # Assume MB/s if no unit or unknown

                def print_live_status(self, force_newline=False):
                    pass # Not needed for PyQt6 live update

            monitor = SimpleMonitor(self)
            
            # Use Python engine directly
            monitor.log_messages.append("Starting Python disk performance test...")
            monitor._update_log_display()
            results = self.python_engine.execute_disk_test(test_mode, disk_path, test_size_gb, monitor=monitor)
            
            # Update results on main thread
            # Emit signal to update UI on main thread
            if results:
                self.test_finished_signal.emit(json.dumps(results, indent=2))
            else:
                self.test_finished_signal.emit("Python disk engine failed to produce results.")

        except Exception as e:
            self.test_finished_signal.emit(f"An error occurred: {e}")

    def _handle_test_finished_on_main_thread(self, results_text):
        # This slot runs on the main GUI thread
        try:
            # Try to parse JSON and format it nicely
            results_data = json.loads(results_text)
            formatted_results = self._format_results_for_display(results_data)
            self.results_text.setText(formatted_results)
        except json.JSONDecodeError:
            # If not JSON, display as-is
            self.results_text.setText(results_text)
        
        self._reset_ui_on_finish()
        # Clean up test files after test finishes
        selected_drive_index = self.drive_combo.currentIndex()
        if selected_drive_index != -1:
            selected_drive_path = self.drive_options[selected_drive_index]['data'].get('Mount Point')
            self.fio_manager.cleanup_test_files(selected_drive_path)

    def _handle_log_update_on_main_thread(self, log_text):
        """Handle log updates on the main thread"""
        self.log_output.setText(log_text)
        # Auto-scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)

    def _handle_progress_update_on_main_thread(self, progress_percent, throughput, iops):
        """Handle progress updates on the main thread"""
        self.progress_bar.setValue(progress_percent)
        self.current_throughput = throughput
        self.current_iops = iops
        
        # Add data to chart
        if hasattr(self, 'chart_data'):
            current_time = time.time()
            if hasattr(self, '_chart_start_time'):
                elapsed = current_time - self._chart_start_time
            else:
                self._chart_start_time = current_time
                elapsed = 0
            
            self.chart_data.append((elapsed, throughput))
            
            # Keep only last 60 points
            if len(self.chart_data) > 60:
                self.chart_data = self.chart_data[-60:]

    def _update_chart(self):
        # Update performance display with latest data
        throughput_text = f"{self.current_throughput:.1f} MB/s"
        iops_text = f"{self.current_iops:,}"
        
        # Get temperature status
        temp_text = self.temperature_monitor.get_temperature_status() if self.current_temperature else "🔍 Detecting..."
        
        self.performance_display.setText(f"Throughput: {throughput_text} | IOPS: {iops_text} | SSD: {temp_text}")

    def _on_stop_test(self):
        self.running = False
        # Stop the FIO manager test
        self.fio_manager.stop_test()
        self._reset_ui_on_finish()
        # Clean up test files if stopped manually
        selected_drive_index = self.drive_combo.currentIndex()
        if selected_drive_index != -1:
            selected_drive_path = self.drive_options[selected_drive_index]['data'].get('Mount Point')
            self.fio_manager.cleanup_test_files(selected_drive_path)

    def _format_results_for_display(self, results_data):
        """Format JSON results into a beautiful, modern display."""
        if not results_data:
            return "No results available."
        
        formatted_text = []
        test_mode = results_data.get('test_mode', 'Unknown')
        jobs = results_data.get('jobs', [])
        
        if not jobs:
            return "No job results found."
        
        # Calculate overall metrics
        max_read_bw = 0
        avg_read_bw = 0
        max_write_bw = 0
        total_runtime = 0
        read_jobs = []
        
        for job in jobs:
            if 'read' in job:
                read_bw = job['read'].get('bw', 0)
                max_read_bw = max(max_read_bw, read_bw)
                read_jobs.append(read_bw)
                runtime_ms = job['read'].get('runtime_msec', 0)
                total_runtime += runtime_ms / 1000
            if 'write' in job:
                write_bw = job['write'].get('bw', 0)
                max_write_bw = max(max_write_bw, write_bw)
        
        avg_read_bw = sum(read_jobs) / len(read_jobs) if read_jobs else 0
        
        # Determine overall rating
        if max_read_bw >= 2000:
            rating = "🟢 AUSGEZEICHNET"
            rating_desc = "Perfekt für QLab Production"
        elif max_read_bw >= 1000:
            rating = "🟡 GUT"
            rating_desc = "Geeignet für die meisten QLab Shows"
        elif max_read_bw >= 500:
            rating = "🟠 AUSREICHEND"
            rating_desc = "Funktioniert für einfache QLab Setups"
        else:
            rating = "🔴 PROBLEMATISCH"
            rating_desc = "Nicht empfohlen für QLab"
        
        # Header with overall rating
        formatted_text.append("┌─ 📊 TESTERGEBNIS ÜBERSICHT ─────────────────────┐")
        formatted_text.append(f"│ {rating} für QLab Production           │")
        
        # Show test type specific info
        if 'prores_422' in test_mode:
            formatted_text.append(f"│ 🎬 ProRes 422: {avg_read_bw:.0f} MB/s | 🔥 Max: {max_read_bw:.0f} MB/s │")
        elif 'prores_hq' in test_mode:
            formatted_text.append(f"│ 🎭 ProRes HQ: {avg_read_bw:.0f} MB/s | 🔥 Max: {max_read_bw:.0f} MB/s │")
        else:
            formatted_text.append(f"│ 📈 Durchschnitt: {avg_read_bw:.0f} MB/s | 🔥 Max: {max_read_bw:.0f} MB/s │")
        
        formatted_text.append("└─────────────────────────────────────────────────┘")
        formatted_text.append("")
        
        # Performance Details Card
        formatted_text.append("┌─ 📈 PERFORMANCE DETAILS ───────────────────────┐")
        formatted_text.append(f"│ • Durchschnitt: {avg_read_bw:.0f} MB/s                     │")
        formatted_text.append(f"│ • Spitzenwert: {max_read_bw:.0f} MB/s                      │")
        
        # Latency analysis (simulated for now)
        if max_read_bw >= 1000:
            latency_status = "✅ <5ms (Ausgezeichnet)"
            jitter_status = "✅ Keine erkannt"
        elif max_read_bw >= 500:
            latency_status = "⚠️ 5-15ms (Akzeptabel)"
            jitter_status = "⚠️ Gelegentlich"
        else:
            latency_status = "🔴 >15ms (Problematisch)"
            jitter_status = "🔴 Häufige Ruckler"
        
        formatted_text.append(f"│ • Latenz: {latency_status}               │")
        formatted_text.append(f"│ • Ruckler: {jitter_status}                     │")
        
        if max_write_bw > 0:
            formatted_text.append(f"│ • Schreibgeschwindigkeit: {max_write_bw:.0f} MB/s           │")
        
        formatted_text.append("└─────────────────────────────────────────────────┘")
        formatted_text.append("")
        
        # QLab Assessment Card
        formatted_text.append("┌─ 🎭 QLAB EINSCHÄTZUNG ─────────────────────────┐")
        
        # Calculate stream estimates
        prores_422_streams = int(max_read_bw / 25) if max_read_bw > 0 else 0  # ~25 MB/s per 4K ProRes 422
        prores_hq_streams = int(max_read_bw / 40) if max_read_bw > 0 else 0   # ~40 MB/s per 4K ProRes HQ
        
        formatted_text.append(f"│ • 4K ProRes 422 Streams: ~{prores_422_streams} gleichzeitig       │")
        formatted_text.append(f"│ • 4K ProRes HQ Streams: ~{prores_hq_streams} gleichzeitig        │")
        
        # Crossfade capability
        if max_read_bw >= 2100:
            crossfade_status = "✅ Exzellent"
        elif max_read_bw >= 1500:
            crossfade_status = "✅ Gut"
        elif max_read_bw >= 1000:
            crossfade_status = "⚠️ Begrenzt"
        else:
            crossfade_status = "🔴 Problematisch"
        
        formatted_text.append(f"│ • Crossfade-Fähigkeit: {crossfade_status}            │")
        
        # Show suitability
        if max_read_bw >= 1500:
            show_level = "✅ Profi-Level"
        elif max_read_bw >= 800:
            show_level = "✅ Semi-Profi"
        elif max_read_bw >= 400:
            show_level = "⚠️ Einfache Shows"
        else:
            show_level = "🔴 Nur Audio/Bilder"
        
        formatted_text.append(f"│ • Show-Tauglichkeit: {show_level}            │")
        formatted_text.append("└─────────────────────────────────────────────────┘")
        formatted_text.append("")
        
        # Detailed Phase Results (if multiple phases)
        if len(jobs) > 1:
            formatted_text.append("┌─ 📋 DETAILLIERTE PHASEN-ERGEBNISSE ────────────┐")
            
            for i, job in enumerate(jobs, 1):
                job_name = job.get('jobname', f'Phase {i}')
                
                # Clean up job name for display
                display_name = job_name.replace('_', ' ').title()
                if 'prores_422' in job_name:
                    if 'normal' in job_name:
                        display_name = "📹 ProRes 422 Normal"
                    elif 'show' in job_name:
                        display_name = "🎬 ProRes 422 Show"
                    elif 'recovery' in job_name:
                        display_name = "🔄 ProRes 422 Recovery"
                    elif 'max_speed' in job_name:
                        display_name = "🚀 ProRes 422 Max Speed"
                elif 'prores_hq' in job_name:
                    if 'normal' in job_name:
                        display_name = "📹 ProRes HQ Normal"
                    elif 'show' in job_name:
                        display_name = "🎭 ProRes HQ Show"
                    elif 'recovery' in job_name:
                        display_name = "🔄 ProRes HQ Recovery"
                    elif 'max_speed' in job_name:
                        display_name = "🚀 ProRes HQ Max Speed"
                elif 'sustained' in job_name:
                    display_name = "🚀 Max Sustained"
                
                formatted_text.append(f"│ {display_name:<30} │")
                
                if 'read' in job:
                    read_bw = job['read'].get('bw', 0)
                    read_iops = job['read'].get('iops', 0)
                    runtime_s = job['read'].get('runtime_msec', 0) / 1000
                    
                    formatted_text.append(f"│   📖 Read: {read_bw:.0f} MB/s | IOPS: {read_iops:,}     │")
                    
                    if runtime_s > 60:
                        runtime_display = f"{runtime_s/60:.1f} min"
                    else:
                        runtime_display = f"{runtime_s:.0f} sec"
                    formatted_text.append(f"│   ⏱️ Laufzeit: {runtime_display}                    │")
                
                if 'write' in job:
                    write_bw = job['write'].get('bw', 0)
                    formatted_text.append(f"│   ✏️ Write: {write_bw:.0f} MB/s                    │")
                
                formatted_text.append("│                                                 │")
            
            formatted_text.append("└─────────────────────────────────────────────────┘")
            formatted_text.append("")
        
        # Recommendations
        formatted_text.append("┌─ 💡 EMPFEHLUNGEN ──────────────────────────────┐")
        
        if max_read_bw >= 2000:
            formatted_text.append("│ ✅ Perfekt für große QLab Produktionen          │")
            formatted_text.append("│ ✅ Multi-Screen 4K Video ohne Probleme          │")
            formatted_text.append("│ ✅ Komplexe Crossfades und Effekte möglich      │")
        elif max_read_bw >= 1000:
            formatted_text.append("│ ✅ Gut für die meisten QLab Shows               │")
            formatted_text.append("│ ✅ 4K Video mit moderaten Crossfades            │")
            formatted_text.append("│ ⚠️ Bei komplexen Shows Pufferung empfohlen      │")
        elif max_read_bw >= 500:
            formatted_text.append("│ ⚠️ Nur für einfache QLab Setups                 │")
            formatted_text.append("│ ⚠️ HD Video bevorzugen, 4K vermeiden            │")
            formatted_text.append("│ ⚠️ Crossfades sparsam verwenden                 │")
        else:
            formatted_text.append("│ 🔴 Nicht für Video-QLab geeignet                │")
            formatted_text.append("│ 🔴 Nur Audio und statische Bilder               │")
            formatted_text.append("│ 🔴 SSD-Upgrade dringend empfohlen               │")
        
        formatted_text.append("└─────────────────────────────────────────────────┘")
        
        return "\n".join(formatted_text)

    def _reset_ui_on_finish(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100)
        self.chart_timer.stop()
        self.log_output.setText("Test finished.")
