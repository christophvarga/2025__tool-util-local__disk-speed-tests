import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QCheckBox, QFrame, QScrollBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
import threading
import queue

class DebugTerminal(QWidget):
    """
    Professional debug terminal widget with real-time logging,
    color coding, filtering, and terminal-like appearance.
    """
    
    def __init__(self):
        super().__init__()
        self.log_queue = queue.Queue()
        self.is_visible = False
        self.auto_scroll = True
        
        # Log level filters
        self.show_debug = True
        self.show_info = True
        self.show_warning = True
        self.show_error = True
        
        self._setup_ui()
        self._setup_timer()
        
    def _setup_ui(self):
        """Setup the terminal UI with professional styling."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with toggle and controls
        self.header_frame = QFrame()
        self.header_frame.setObjectName("DebugTerminalHeader")
        self.header_frame.setStyleSheet("""
            QFrame#DebugTerminalHeader {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-bottom: 2px solid #007acc;
                padding: 5px;
            }
        """)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Terminal title and toggle
        self.title_label = QLabel("🖥️ DEBUG TERMINAL")
        self.title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Filter checkboxes
        self.debug_cb = QCheckBox("DEBUG")
        self.debug_cb.setChecked(True)
        self.debug_cb.setStyleSheet("color: #87ceeb; font-size: 10px;")
        self.debug_cb.toggled.connect(self._on_filter_changed)
        header_layout.addWidget(self.debug_cb)
        
        self.info_cb = QCheckBox("INFO")
        self.info_cb.setChecked(True)
        self.info_cb.setStyleSheet("color: #90ee90; font-size: 10px;")
        self.info_cb.toggled.connect(self._on_filter_changed)
        header_layout.addWidget(self.info_cb)
        
        self.warning_cb = QCheckBox("WARN")
        self.warning_cb.setChecked(True)
        self.warning_cb.setStyleSheet("color: #ffa500; font-size: 10px;")
        self.warning_cb.toggled.connect(self._on_filter_changed)
        header_layout.addWidget(self.warning_cb)
        
        self.error_cb = QCheckBox("ERROR")
        self.error_cb.setChecked(True)
        self.error_cb.setStyleSheet("color: #ff6b6b; font-size: 10px;")
        self.error_cb.toggled.connect(self._on_filter_changed)
        header_layout.addWidget(self.error_cb)
        
        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border: 1px solid #666;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.clear_btn.clicked.connect(self._clear_terminal)
        header_layout.addWidget(self.clear_btn)
        
        # Toggle button
        self.toggle_btn = QPushButton("🔽 Hide")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_terminal)
        header_layout.addWidget(self.toggle_btn)
        
        layout.addWidget(self.header_frame)
        
        # Terminal text area
        self.terminal_text = QTextEdit()
        self.terminal_text.setObjectName("DebugTerminalText")
        
        # Terminal styling - professional dark theme
        terminal_font = QFont("Monaco", 10)  # macOS monospace font
        if not terminal_font.exactMatch():
            terminal_font = QFont("Courier New", 10)  # Fallback
        terminal_font.setFixedPitch(True)
        
        self.terminal_text.setFont(terminal_font)
        self.terminal_text.setStyleSheet("""
            QTextEdit#DebugTerminalText {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
                selection-background-color: #264f78;
                font-family: 'Monaco', 'Courier New', monospace;
            }
        """)
        
        self.terminal_text.setReadOnly(True)
        self.terminal_text.setMinimumHeight(200)
        self.terminal_text.setMaximumHeight(400)
        
        layout.addWidget(self.terminal_text)
        
        # Initially hide the terminal content
        self.terminal_text.hide()
        self.setMaximumHeight(40)  # Just header height
        
    def _setup_timer(self):
        """Setup timer for processing log queue."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_log_queue)
        self.timer.start(100)  # Process every 100ms
        
    def _toggle_terminal(self):
        """Toggle terminal visibility."""
        if self.is_visible:
            self.terminal_text.hide()
            self.setMaximumHeight(40)
            self.toggle_btn.setText("🔽 Show")
            self.is_visible = False
        else:
            self.terminal_text.show()
            self.setMaximumHeight(450)  # Header + terminal
            self.toggle_btn.setText("🔼 Hide")
            self.is_visible = True
            
    def _on_filter_changed(self):
        """Update filter settings when checkboxes change."""
        self.show_debug = self.debug_cb.isChecked()
        self.show_info = self.info_cb.isChecked()
        self.show_warning = self.warning_cb.isChecked()
        self.show_error = self.error_cb.isChecked()
        
    def _clear_terminal(self):
        """Clear terminal content."""
        self.terminal_text.clear()
        
    def _process_log_queue(self):
        """Process pending log messages from queue."""
        try:
            while True:
                level, message = self.log_queue.get_nowait()
                self._append_log_message(level, message)
        except queue.Empty:
            pass
            
    def _append_log_message(self, level, message):
        """Append a log message with proper formatting."""
        # Check if this level should be shown
        if level == "DEBUG" and not self.show_debug:
            return
        if level == "INFO" and not self.show_info:
            return
        if level == "WARNING" and not self.show_warning:
            return
        if level == "ERROR" and not self.show_error:
            return
            
        # Get current timestamp
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Color mapping for different log levels
        colors = {
            "DEBUG": "#87ceeb",    # Sky blue
            "INFO": "#90ee90",     # Light green
            "WARNING": "#ffa500",  # Orange
            "ERROR": "#ff6b6b",    # Light red
            "STDERR": "#ff8c00",   # Dark orange
            "STDOUT": "#d4d4d4",   # Default
            "SUBPROCESS": "#dda0dd", # Plum
            "THREAD": "#98fb98"    # Pale green
        }
        
        # Format the log line
        color = colors.get(level, "#d4d4d4")
        
        # Move cursor to end
        cursor = self.terminal_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Insert timestamp in gray
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor("#888888"))
        cursor.insertText(f"[{timestamp}] ", timestamp_format)
        
        # Insert level in appropriate color
        level_format = QTextCharFormat()
        level_format.setForeground(QColor(color))
        level_format.setFontWeight(700)  # Bold
        cursor.insertText(f"[{level:8}] ", level_format)
        
        # Insert message in default color
        message_format = QTextCharFormat()
        message_format.setForeground(QColor("#d4d4d4"))
        cursor.insertText(f"{message}\n", message_format)
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            scrollbar = self.terminal_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def log_debug(self, message):
        """Log a debug message."""
        self.log_queue.put(("DEBUG", str(message)))
        
    def log_info(self, message):
        """Log an info message."""
        self.log_queue.put(("INFO", str(message)))
        
    def log_warning(self, message):
        """Log a warning message."""
        self.log_queue.put(("WARNING", str(message)))
        
    def log_error(self, message):
        """Log an error message."""
        self.log_queue.put(("ERROR", str(message)))
        
    def log_stderr(self, message):
        """Log stderr output."""
        self.log_queue.put(("STDERR", str(message)))
        
    def log_stdout(self, message):
        """Log stdout output."""
        self.log_queue.put(("STDOUT", str(message)))
        
    def log_subprocess(self, message):
        """Log subprocess-related message."""
        self.log_queue.put(("SUBPROCESS", str(message)))
        
    def log_thread(self, message):
        """Log thread-related message."""
        self.log_queue.put(("THREAD", str(message)))
