# QLab Disk Performance Tester — LLM Context
*Context Version 1.6 — 13.7.2026*

## Purpose

Lokales Disk-Performance-Werkzeug für QLab-Video-Playback-Anforderungen. Eine
Web-GUI steuert über eine ausschließlich lokale HTTP-Bridge realistische FIO-
Lastprofile. Das Repo ist als Legacy-Werkzeug gepflegt, aber nicht deployed und
betreibt keinen zentralen Dienst.

## Current State
- **Phase**: MVP abgeschlossen, Security-Hardening done
- **Python-Paketversion**: 1.3.0 (`pyproject.toml`)
- **Status**: Funktionsfähig, Architektur finalisiert, Security gehärtet
- **Kanonischer Branch**: `main`
- **Last Documentation Review**: 13.7.2026

## Architecture
- **Backend**: Python HTTP Bridge (localhost:8765), aufgeteilt in 9 Module (Mixin-Pattern)
- **Frontend**: HTML/CSS/JS Web Interface (Vanilla JS, kein Bundler, 9 Module)
- **Engine**: FIO (Homebrew oder vendored binary)
- **Pattern**: Web GUI → HTTP Bridge → diskbench CLI → FIO

## Tech Stack
- **Backend**: Python 3.12+ (Standard Library only)
- **Database**: Keine (JSON für Ergebnisse)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Integration**: Homebrew FIO oder vendor/fio/macos/arm64/fio

## Interfaces

- Lokale Web-Oberfläche: `http://localhost:8765/`.
- HTTP-Bridge: nur localhost; zentrale GET-Routen sind unter anderem
  `/api/status`, `/api/disks`, `/api/validate`, `/api/version`, `/api/tests`,
  `/api/fio-info` und `/api/test/<id>`.
- Steuernde POST-Routen: `/api/test/start`, `/api/test/stop/<id>`,
  `/api/test/stop-all`, `/api/setup` und `/api/validate`.
- CLI: `python -m diskbench.main` beziehungsweise der installierte Befehl
  `diskbench`; Ein- und Ausgabe sind Argumente, Fortschritt und JSON-Ergebnisse.
- Externer Prozess: FIO aus Homebrew oder dem vendorten Offline-Pfad.

Es gibt keine öffentliche URL, Remote-API, Datenbank oder Cross-Repo-
Abhängigkeit. Ergebnis-JSON ist lokale Nutzerausgabe und kein Fleet-Vertrag.

## Bridge-Server Modulstruktur
| Modul | Aufgabe | LOC |
|-------|---------|-----|
| `server.py` | Entry-Point, kombiniert alle Mixins | ~100 |
| `bridge_core.py` | DiskBenchBridgeCore Basis-Klasse | ~252 |
| `bridge_status.py` | BridgeStatusMixin (Status-API) | ~224 |
| `http_handlers.py` | BridgeRequestHandler (HTTP, CORS) | ~299 |
| `test_control.py` | TestControlMixin (Disk-Validation) | ~300 |
| `process_manager.py` | ProcessManagerMixin (Subprocess, PID-Cleanup) | ~280 |
| `fio_utils.py` | FioUtilsMixin (FIO-Tests, Config-Gen) | ~300 |
| `fio_setup.py` | FioSetupMixin (FIO-Installation) | ~299 |
| `validation.py` | Validierung, Sanitizing, Security-Imports | ~75 |

## Security-Hardening (Feb 2026)
- **Path Traversal**: validate_disk_path(), is_system_path() integriert
- **Config Injection**: _validate_custom_fio_params() mit Regex-Whitelists + Newline-Stripping
- **TOCTOU**: tempfile.mkstemp() statt vorhersagbare /tmp-Pfade
- **XSS**: _escapeHTML() für alle innerHTML mit dynamischen Daten (20+ Stellen)
- **CORS**: Eingeschränkt auf localhost-Origins (kein Wildcard mehr)
- **Exception-Leaking**: _sanitize_error() verhindert System-Pfad-Leakage
- **Timeouts**: AbortController + 30s Timeout in callBridgeAPI()
- **Circuit Breaker**: 3-State (closed/open/half-open) mit Exponential Backoff
- **Process-Cleanup**: PID-basiert mit ps aux als Fallback für Orphans

## Features
- Quick Max Speed Test (3 Min)
- QLab ProRes 422 Show Pattern (2.75h)
- QLab ProRes HQ Show Pattern (2.75h)
- Thermal Maximum Analyser (1.5h)

## Constraints
- **Budget**: Open Source Projekt
- **Security**: Input-Validierung implementiert (Feb 2026)
- **Compliance**: macOS-kompatibel
- **Architecture**: Keine komplexen Frameworks

## Development
- **Language**: Deutsch für Doku, Englisch für Code
- **Date Format**: Österreichisch (30.5.2025)
- **Money Format**: Österreichisch (10.320,00 EUR)
- **Strategy**: MVP-First, pragmatisch

## HOLDS
- **HOLD-001**: DMG-Packaging (Phase 3)
- **HOLD-002**: Code-Signing (bei 100+ Users)
- **HOLD-003**: Auto-Update Mechanismus (Phase 3)
- **HOLD-004**: FIO SHM Issues (Workaround existiert)
- **HOLD-005**: Browser Security (Monitoring)
- **HOLD-010**: app.js Frontend-Tests (0% Coverage, nicht security-kritisch)

## Core Modules
1. **bridge-server/**: HTTP API Server (9 Module via Mixin-Pattern)
2. **diskbench/**: CLI Test-Engine
3. **web-gui/**: Browser Interface (Vanilla JS, 9 Module: app.js + app-api/core/disks/persistence/progress/results/setup/test-control.js)
4. **tests/**: 137 Tests (Unit + Integration), 33.73% Gesamt-Coverage
5. **vendor/**: Vendored FIO binary (offline use)

## Tests
- **137 passed**, 0 failed, 1 skipped
- 18 Unit-Test-Files in tests/unit/ (inkl. test_health_checks, test_logging_utils, test_monitoring, test_retry_logic, test_security_utils, test_system_info_utils)
- 25 Security-Tests (test_bridge_security.py)
- 11 Process-Cleanup-Tests (test_cleanup_fio_processes.py)
- 2 diskbench-spezifische Tests (diskbench/tests/: test_enhanced_fio_runner, test_monitoring)
- Coverage: 33.73% gesamt, ~75% auf getestetem Code

## Gelöschte Verzeichnisse (Feb 2026)
- `/commands/` (Legacy-Shim, Imports migriert nach diskbench.commands)
- `/core/` (Legacy-Shim, Imports migriert nach diskbench.core)
- `/qlab-disk-tester/` (Legacy mit eigener venv)
- `/memory-bank/` (Legacy, State migriert nach .state/)
- 7x `TODO_*.md` (konsolidiert in 99_archiv/TODO_consolidated_legacy.md)

## Recent Changes (9.2.2026)
- Security-Hardening: 5 CRITICAL + 6 HIGH Findings behoben
- Bridge-Server: server.py (2674 LOC) aufgeteilt in 9 Module (je <=300 LOC)
- Frontend: XSS-Fix, Circuit Breaker, Timeout-Handling
- Frontend-Modularization: app.js (2749 LOC) aufgeteilt in 9 JS-Module (je <=300 LOC)
  - Module: app-api.js, app-core.js, app-disks.js, app-persistence.js, app-progress.js,
    app-results.js, app-setup.js, app-test-control.js + app.js (Orchestrator)
- Security-Fix 2: Path Traversal in Static Serving, Direct-FIO Validierung, POST Double-Read-Bug (http_handlers.py)
- PID-basiertes Process-Cleanup (statt ps aux String-Matching)
- Legacy-Cleanup: 4 Verzeichnisse + 7 TODO-Dateien entfernt
- Import-Migration: core.*/commands.* → diskbench.core.*/diskbench.commands.*
- 36 neue Tests (25 Security + 11 Process-Cleanup)
- Repo-Name-Referenzen auf suite-schema (infra--ci-cd) aktualisiert

## Stabilität seit 9.2.2026
- Keine weiteren Code-Aenderungen
- 358 Session-End Auto-Commits (nur 90_reports/changes.md + test_reports/latest)

## Ownership and operations

Owner, Review-Evidence und Abhängigkeiten stehen in
`00_infos/repo-contract.yaml`. Setup, Start und Stop sind lokale Nutzerabläufe in
dieser Datei und im README. Ein separates Operations-Runbook ist nicht
anwendbar, weil keine dauerhaft betriebene Instanz existiert.
