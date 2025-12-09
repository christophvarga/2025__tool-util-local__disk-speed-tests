# Changes Report

Datum: 2025-09-08

Änderungen:
- Makefile: test-report Runner auf `python -m pytest` + tests/ beschränkt
- pytest.ini: Header auf [pytest] korrigiert
- scripts/evaluate_results.py: Neues Evaluationsskript (striktere QLab-Schwellen)
- docs/evaluation-criteria.md: Kriterien und Mindestwerte dokumentiert
- docs/fio-fallback/: FIO-Templates + README (vorher hinzugefügt) – Referenzen im README ergänzt
- scripts/clean.sh: Cleanup-Skript (Artefakte aufräumen, latest-Report erhalten)
- README.md: Version 1.3.1 – 8.9.2025; Evaluator/Runner/Cleanup-Verweise ergänzt
- WARP.md: Version 1.1 – 8.9.2025; Runner/Evaluator/Cleanup ergänzt
- Archiv: README_v1.3_2025-09-05.md, WARP_v1.0_2025-08-24.md

Risiken/HOLDs:
- Keine Architektur-Änderungen; keine neuen Dependencies. HOLDS (DMG/Signing/Auto-Update) unberührt.
- Coverage gering (18.09%), akzeptiert da Fokus auf Doku/Runner.

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
- web-gui/index.html; README.md (v1.1 → v1.2; Offline Checklist, Launcher, Packaging, Gatekeeper)
- vendor/fio/* docs/placeholders
- tests/unit/test_fio_path_resolution.py

Risks/HOLDs:
- FIO binary is not included in repo due to licensing; needs to be placed under vendor/fio/macos/arm64/fio on release media.
- Font Awesome icons removed (no CDN); icons may degrade; consider local assets follow-up.
- PyInstaller packaging relies on dev having pyinstaller.


