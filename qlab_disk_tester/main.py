import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qlab_disk_tester.gui_pyqt.main_window import MainWindow

def main():
    """Entry point for launching the PyQt6 GUI."""
    # Set macOS-specific attributes before creating QApplication
    if sys.platform == "darwin":  # macOS
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
    
    app = QApplication(sys.argv)
    
    # Configure application metadata
    app.setApplicationName("QLab Disk Performance Tester")
    app.setApplicationDisplayName("QLab Disk Performance Tester")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("QLab Tools")
    app.setOrganizationDomain("qlab.app")
    
    # macOS-specific configuration
    if sys.platform == "darwin":
        # Set the application name in the menu bar
        from PyQt6.QtCore import Qt
        app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
        # Ensure proper app name display
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.setApplicationName("QLab Disk Performance Tester")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
