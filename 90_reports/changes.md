# Change Summary

Date: 2025-09-04 18:50

Changes:
- Offline operation goal implemented: vendored FIO preference, PyInstaller packaging, offline launcher.
- Launchers unified: Start Diskbench Bridge.command (end-user), scripts/start.sh (dev), start.sh delegates.
- Bridge and runner refactored to prepend vendor FIO to PATH and set FIO_DISABLE_SHM=1.
- README updated with Offline Quick Start; web-gui de-duplicated from external CDNs.
- Tests added: vendored FIO path resolution and validation acceptance.

Files affected (high-level):
- bridge-server/server.py
- diskbench/core/fio_runner.py
- diskbench/commands/validate.py
- Start Diskbench Bridge.command; scripts/start.sh; start.sh
- scripts/build_bridge_pyinstaller.sh
- web-gui/index.html; README.md
- vendor/fio/* docs/placeholders
- tests/unit/test_fio_path_resolution.py

Risks/HOLDs:
- FIO binary is not included in repo due to licensing; needs to be placed under vendor/fio/macos/arm64/fio on release media.
- Font Awesome icons removed (no CDN); icons may degrade; consider local assets follow-up.
- PyInstaller packaging relies on dev having pyinstaller.


