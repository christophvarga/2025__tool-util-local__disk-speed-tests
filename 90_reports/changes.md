# Changes Report

Datum: 2026-02-09

Aenderungen (Security Hardening - Quick Wins):
- C-1: validate_disk_path() + is_system_path() + check_available_space() im Bridge-Server integriert
- C-2: _validate_custom_fio_params() mit Range-Checks (duration, numjobs, iodepth) und Whitelist (block_size, target_rate)
- C-2: Newline-Stripping in _generate_custom_fio_config() gegen INI-Injection
- C-3: tempfile.mkstemp() statt vorhersagbarer /tmp Pfade (output + config)
- C-5: CORS von '*' auf localhost-Origins eingeschraenkt
- H-1: AbortController + 30s Timeout in callBridgeAPI() (Frontend)
- H-2: Konfigurierbare BRIDGE_URL als statisches Klassenattribut
- H-5: _sanitize_error() fuer alle Exception-an-Client Stellen (5 Stellen)

Betroffene Dateien:
- bridge-server/server.py (Imports, Validierung, tempfile, CORS, Exception-Handling)
- web-gui/app.js (AbortController, Timeout, BRIDGE_URL)
- tests/unit/test_bridge_security.py (NEU: 25 Tests)
- tests/unit/test_bridge_server_logic.py (Anpassung fuer neue Validierung)
- 90_reports/test-report.md, coverage.md, changes.md

Tests added: 25 neue Security-Tests
Tests updated: 2 (test_bridge_server_logic.py Disk-Validation-Mocking)
Risiken/HOLDs: Keine neuen. HOLD-001 bis HOLD-005 unveraendert.

---

# Changes Report (vorherig)

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


