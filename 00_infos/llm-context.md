# QLab Disk Performance Tester - LLM Context
*Version 1.4 – 9.2.2026*

## Projekt-Mission
Ein professionelles Disk Performance Testing Tool speziell für QLab Video-Playback-Anforderungen. Web-basierte GUI mit FIO-Engine für realistische Show-Pattern-Tests.

## Current State
- **Phase**: MVP abgeschlossen, Security-Hardening done
- **Version**: 1.0.0-beta
- **Status**: Funktionsfähig, Architektur finalisiert, Security gehärtet
- **Branches**: `pre` (default), `main`
- **Last Update**: 9.2.2026 - Security-Hardening + Refactoring + Legacy-Cleanup

## Architecture
- **Backend**: Python HTTP Bridge (localhost:8765), aufgeteilt in 9 Module (Mixin-Pattern)
- **Frontend**: HTML/CSS/JS Web Interface (Vanilla JS, kein Bundler)
- **Engine**: FIO (Homebrew oder vendored binary)
- **Pattern**: Web GUI → HTTP Bridge → diskbench CLI → FIO

## Tech Stack
- **Backend**: Python 3.12+ (Standard Library only)
- **Database**: Keine (JSON für Ergebnisse)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Integration**: Homebrew FIO oder vendor/fio/macos/arm64/fio

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
3. **web-gui/**: Browser Interface (Vanilla JS)
4. **tests/**: 137 Tests (Unit + Integration), 33.58% Gesamt-Coverage
5. **vendor/**: Vendored FIO binary (offline use)

## Tests
- **137 passed**, 0 failed, 1 skipped
- 25 Security-Tests (test_bridge_security.py)
- 11 Process-Cleanup-Tests (test_cleanup_fio_processes.py)
- Coverage: 33.58% gesamt, ~75% auf getestetem Code

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
- PID-basiertes Process-Cleanup (statt ps aux String-Matching)
- Legacy-Cleanup: 4 Verzeichnisse + 7 TODO-Dateien entfernt
- Import-Migration: core.*/commands.* → diskbench.core.*/diskbench.commands.*
- 36 neue Tests (25 Security + 11 Process-Cleanup)
