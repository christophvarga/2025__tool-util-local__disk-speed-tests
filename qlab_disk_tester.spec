# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Define the main script
main_script = os.path.join(current_dir, 'qlab_disk_tester', 'main.py')

# Collect data files
datas = []

# Add the icon file
icon_path = os.path.join(current_dir, 'icon.png')
if os.path.exists(icon_path):
    datas.append((icon_path, '.'))

# Add icon from qlab_disk_tester directory
qlab_icon_path = os.path.join(current_dir, 'qlab_disk_tester', 'icon.png')
if os.path.exists(qlab_icon_path):
    datas.append((qlab_icon_path, 'qlab_disk_tester'))

# Add FIO binary as data file
fio_binary_path = os.path.join(current_dir, 'fio-3.37', 'fio')
if os.path.exists(fio_binary_path):
    datas.append((fio_binary_path, 'fio-3.37'))

# Hidden imports for PyQt6
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'qlab_disk_tester.core.disk_detector',
    'qlab_disk_tester.core.python_disk_engine',
    'qlab_disk_tester.core.temperature_monitor',
    'qlab_disk_tester.gui_pyqt.main_window',
    'qlab_disk_tester.gui_pyqt.styles.qss_styles',
    'subprocess',
    'threading',
    'json',
    'time',
    'os',
    'sys',
    'platform',
    'random',
    're'
]

# Analysis
a = Analysis(
    [main_script],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QLab Disk Performance Tester',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
)

# Create the .app bundle (macOS only)
app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='QLab Disk Performance Tester.app',
    icon=icon_path if os.path.exists(icon_path) else None,
    bundle_identifier='com.qlab.disk-performance-tester',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'QLab Disk Performance Tester',
        'CFBundleDisplayName': 'QLab Disk Performance Tester',
        'CFBundleIdentifier': 'com.qlab.disk-performance-tester',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': 'QLab Disk Performance Tester',
        'CFBundleIconFile': 'icon.png',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.14.0',
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDocumentTypes': [],
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'NSHumanReadableCopyright': '© 2025 QLab Tools',
        'CFBundleGetInfoString': 'QLab Disk Performance Tester v1.0.0',
        'NSAppleEventsUsageDescription': 'This app needs to access system information to detect disk drives.',
        'NSSystemAdministrationUsageDescription': 'This app needs administrator privileges to perform disk performance tests.',
    }
)
