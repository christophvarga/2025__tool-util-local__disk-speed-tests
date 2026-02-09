# Changes Report


## [2026-02-09 10:15] Session 20260209-101506

### Commits
3842549 chore(reports): final test report - all findings resolved (137 passed, 33.58% coverage)
8b20d15 chore(session): Auto-commit at session end
69114aa chore(session): Auto-commit at session end
7a1f9ff chore(cleanup): remove legacy dirs (qlab-disk-tester, memory-bank) + consolidate TODO files
c186ef7 chore(cleanup): remove legacy dirs (qlab-disk-tester, memory-bank) + consolidate TODO files
9e02ebd chore(session): Auto-commit at session end
82b87a7 chore(session): Auto-commit at session end
74dfc41 chore(reports): update test reports after MF-1/MF-2/MF-5 completion (126 passed)
5195361 refactor(bridge-server): split server.py (2773 LOC) into 9 modules (<=300 LOC each)
aa9b94b chore(session): Auto-commit at session end

### Staged Changes
- Keine staged Changes

### Unstaged Changes
- Keine unstaged Changes

---

## [2026-02-09 10:12] Session 20260209-101223

### Commits
69114aa chore(session): Auto-commit at session end
7a1f9ff chore(cleanup): remove legacy dirs (qlab-disk-tester, memory-bank) + consolidate TODO files
c186ef7 chore(cleanup): remove legacy dirs (qlab-disk-tester, memory-bank) + consolidate TODO files
9e02ebd chore(session): Auto-commit at session end
82b87a7 chore(session): Auto-commit at session end
74dfc41 chore(reports): update test reports after MF-1/MF-2/MF-5 completion (126 passed)
5195361 refactor(bridge-server): split server.py (2773 LOC) into 9 modules (<=300 LOC each)
aa9b94b chore(session): Auto-commit at session end
ce5aae3 chore(session): Auto-commit at session end
5788085 fix(web-gui): escape dynamic data in innerHTML to prevent XSS

### Staged Changes
- Keine staged Changes

### Unstaged Changes
.coverage                     | Bin 53248 -> 53248 bytes
 89_output/test_reports/latest |   2 +-
 2 files changed, 1 insertion(+), 1 deletion(-)

---

## [2026-02-09 10:11] Session 20260209-101156

### Commits
7a1f9ff chore(cleanup): remove legacy dirs (qlab-disk-tester, memory-bank) + consolidate TODO files
c186ef7 chore(cleanup): remove legacy dirs (qlab-disk-tester, memory-bank) + consolidate TODO files
9e02ebd chore(session): Auto-commit at session end
82b87a7 chore(session): Auto-commit at session end
74dfc41 chore(reports): update test reports after MF-1/MF-2/MF-5 completion (126 passed)
5195361 refactor(bridge-server): split server.py (2773 LOC) into 9 modules (<=300 LOC each)
aa9b94b chore(session): Auto-commit at session end
ce5aae3 chore(session): Auto-commit at session end
5788085 fix(web-gui): escape dynamic data in innerHTML to prevent XSS
89ec807 chore(session): Auto-commit at session end

### Staged Changes
- Keine staged Changes

### Unstaged Changes
.coverage                        | Bin 53248 -> 53248 bytes
 90_reports/changes.md            |  34 +++++++++
 90_reports/test-report.md        |  22 +++---
 bridge-server/process_manager.py | 161 +++++++++++++++++++++++++++++++--------
 4 files changed, 174 insertions(+), 43 deletions(-)

---

## [2026-02-09 10:10] Refactor: PID-based FIO process cleanup (H-3)

### Aenderung
cleanup_fio_processes() refactored von fragilem `ps aux` String-Matching
auf PID-basiertes Tracking ueber self.running_processes.

### Vorher
- Einziger Mechanismus: `ps aux` parsen + nach "fio"/"diskbench" Pattern suchen
- test_id Parameter wurde akzeptiert aber ignoriert
- Fragil: konnte fremde Prozesse matchen

### Nachher
- **Primaer**: PID-basiertes Tracking ueber self.running_processes (subprocess.Popen-Objekte)
- **Fallback**: `ps aux` nur bei allgemeinem Sweep (test_id=None) fuer echte Orphans
- os.kill(pid, 0) fuer Liveness-Checks statt ps-Parsing
- test_id wird korrekt genutzt fuer gezieltes Cleanup

### Neue Hilfsmethoden
- `_kill_tracked_process()`: Terminiert tracked Popen, raeume Registry auf
- `_pid_alive()`: os.kill(pid, 0) Liveness-Check
- `_kill_pid()`: SIGTERM -> wait -> SIGKILL Eskalation
- `_find_orphan_fio_pids()`: ps aux Fallback, excludiert tracked PIDs

### Betroffene Dateien
- bridge-server/process_manager.py (refactored)
- tests/unit/test_cleanup_fio_processes.py (NEU: 11 Tests)
- 90_reports/test-report.md, changes.md (aktualisiert)

Tests added: 11 neue Tests (test_cleanup_fio_processes.py)
Tests updated: 0 (alle 126 bestehenden Tests unveraendert und gruen)
Risiken/HOLDs: Keine neuen. H-3 geloest.

---

## [2026-02-09 10:09] Legacy Cleanup

### Aenderung
Entfernung von Legacy-Verzeichnissen und Konsolidierung von TODO-Dateien.

### Teil 1: qlab-disk-tester/ entfernt
- Keine produktiven Referenzen gefunden (nur in Claude-Plan-Datei)
- `rm -rf qlab-disk-tester/`

### Teil 2: memory-bank/ entfernt
- 2 Code-Referenzen gefunden und migriert:
  - bridge-server/bridge_core.py: state_file Pfad `memory-bank/` -> `.state/`
  - diskbench/core/state_manager.py: db_dir Pfad `memory-bank/` -> `.state/`
- `.state/` in .gitignore aufgenommen
- `rm -rf memory-bank/`

### Teil 3: TODO-Dateien konsolidiert
- 7 TODO_*.md (alle zum selben nie ausgefuehrten Test-ID-Refactoring) konsolidiert
- Archiviert nach: 99_archiv/TODO_consolidated_legacy.md
- Geloescht: TODO_app_js.md, TODO_bridge_server.md, TODO_main.md,
  TODO_MASTER_REFACTOR_PLAN.md, TODO_memory_bank.md, TODO_qlab_patterns.md,
  TODO_web-gui_index.md

### Betroffene Dateien
- bridge-server/bridge_core.py (state_file Pfad geaendert)
- diskbench/core/state_manager.py (db_dir Pfad geaendert)
- .gitignore (.state/ hinzugefuegt)
- 99_archiv/TODO_consolidated_legacy.md (NEU)
- 90_reports/test-report.md, changes.md (aktualisiert)

Tests: 126 passed, 0 failed, 1 skipped
Risiken/HOLDs: Keine neuen.

---

## [2026-02-09 10:08] Session 20260209-100801

### Commits
82b87a7 chore(session): Auto-commit at session end
74dfc41 chore(reports): update test reports after MF-1/MF-2/MF-5 completion (126 passed)
5195361 refactor(bridge-server): split server.py (2773 LOC) into 9 modules (<=300 LOC each)
aa9b94b chore(session): Auto-commit at session end
ce5aae3 chore(session): Auto-commit at session end
5788085 fix(web-gui): escape dynamic data in innerHTML to prevent XSS
89ec807 chore(session): Auto-commit at session end
1be15cb chore(session): Auto-commit at session end
714c1f1 fix(security): harden bridge-server input validation + frontend timeouts

### Staged Changes
- Keine staged Changes

### Unstaged Changes
89_output/test_reports/latest | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

---

## [2026-02-09 10:02] Session 20260209-100246

### Commits
74dfc41 chore(reports): update test reports after MF-1/MF-2/MF-5 completion (126 passed)
5195361 refactor(bridge-server): split server.py (2773 LOC) into 9 modules (<=300 LOC each)
aa9b94b chore(session): Auto-commit at session end
ce5aae3 chore(session): Auto-commit at session end
5788085 fix(web-gui): escape dynamic data in innerHTML to prevent XSS
89ec807 chore(session): Auto-commit at session end
1be15cb chore(session): Auto-commit at session end
714c1f1 fix(security): harden bridge-server input validation + frontend timeouts

### Staged Changes
- Keine staged Changes

### Unstaged Changes
.coverage | Bin 53248 -> 53248 bytes
 1 file changed, 0 insertions(+), 0 deletions(-)

---

## [2026-02-09 10:01] Mittelfristige Massnahmen (MF-1, MF-2, MF-5)

### C-4/MF-1: innerHTML XSS-Fix
- _escapeHTML() Hilfsmethode zur DiskBenchApp Klasse hinzugefuegt
- 20+ innerHTML-Stellen mit dynamischen Backend-Daten durch _escapeHTML() abgesichert
- Statische HTML-Templates (Icons, Layout) bewusst belassen
- Betroffene Datei: web-gui/app.js

### H-6/MF-5: Circuit Breaker + Retry-Logik
- 3-State Circuit Breaker (closed/open/half-open) fuer Status-Polling
- Exponential Backoff: 2s -> 4s -> 8s -> ... -> 30s max bei Fehlern
- Max 5 konsekutive Fehler -> Circuit Open, Max 30 total -> Hard Stop
- Reconnect-Button bei offenem Circuit
- Connection-Warning-Banner mit CSS (inkl. Dark Mode)
- Betroffene Dateien: web-gui/app.js, web-gui/styles.css

---

## [2026-02-09 09:59] Refactor: Split server.py into modules

### Aenderung
server.py (2773 LOC) in 9 Module aufgeteilt (je <=300 LOC, gesamt 2041 LOC):
- validation.py (75): Regex-Konstanten, _sanitize_error, _validate_custom_fio_params
- bridge_core.py (252): DiskBenchBridgeCore Basisklasse (init, state, JSON, commands)
- bridge_status.py (224): BridgeStatusMixin (background tests, live metrics)
- process_manager.py (236): ProcessManagerMixin (subprocess, FIO config, cleanup)
- test_control.py (300): TestControlMixin (start/stop/stop-all)
- fio_utils.py (257): FioUtilsMixin (direct FIO, QLab tests)
- fio_setup.py (299): FioSetupMixin (SHM detection, compilation, auto-fix)
- http_handlers.py (299): BridgeRequestHandler + ThreadedHTTPServer
- server.py (99): Thin entry-point, composite class, re-exports

### Pattern
Mixin-Pattern mit Mehrfachvererbung. server.py assembliert DiskBenchBridge
aus 6 Mixins. Alle `import server as bridge` Patterns bleiben kompatibel
durch Modul-Re-Exports.

### Betroffene Dateien
- bridge-server/server.py (rewritten)
- bridge-server/validation.py (NEU)
- bridge-server/bridge_core.py (NEU)
- bridge-server/bridge_status.py (NEU)
- bridge-server/process_manager.py (NEU)
- bridge-server/test_control.py (NEU)
- bridge-server/fio_utils.py (NEU)
- bridge-server/fio_setup.py (NEU)
- bridge-server/http_handlers.py (NEU)

Tests: 0 geaendert, 126 passed (alle unveraendert)
Risiken/HOLDs: Keine neuen.

---

## [2026-02-09 09:48] Session 20260209-094832

### Commits
ce5aae3 chore(session): Auto-commit at session end
5788085 fix(web-gui): escape dynamic data in innerHTML to prevent XSS
89ec807 chore(session): Auto-commit at session end
1be15cb chore(session): Auto-commit at session end
714c1f1 fix(security): harden bridge-server input validation + frontend timeouts

### Staged Changes
- Keine staged Changes

### Unstaged Changes
.coverage                     | Bin 53248 -> 53248 bytes
 89_output/test_reports/latest |   2 +-
 2 files changed, 1 insertion(+), 1 deletion(-)

---

## [2026-02-09 09:47] Session 20260209-094738

### Commits
5788085 fix(web-gui): escape dynamic data in innerHTML to prevent XSS
89ec807 chore(session): Auto-commit at session end
1be15cb chore(session): Auto-commit at session end
714c1f1 fix(security): harden bridge-server input validation + frontend timeouts

### Staged Changes
- Keine staged Changes

### Unstaged Changes
89_output/test_reports/latest |  2 +-
 web-gui/styles.css            | 50 +++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 51 insertions(+), 1 deletion(-)

---

## [2026-02-09 09:41] Session 20260209-094134

### Commits
1be15cb chore(session): Auto-commit at session end
714c1f1 fix(security): harden bridge-server input validation + frontend timeouts

### Staged Changes
- Keine staged Changes

### Unstaged Changes
89_output/test_reports/latest | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

---

## [2026-02-09 08:46] Session 20260209-084606

### Commits
714c1f1 fix(security): harden bridge-server input validation + frontend timeouts

### Staged Changes
- Keine staged Changes

### Unstaged Changes
- Keine unstaged Changes

---
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


