# QLab Disk Performance Tester - LLM Context
*Version 1.2 – 9.12.2025*

## Projekt-Mission
Ein professionelles Disk Performance Testing Tool speziell für QLab Video-Playback-Anforderungen. Web-basierte GUI mit FIO-Engine für realistische Show-Pattern-Tests.

## Current State
- **Phase**: MVP abgeschlossen, Alpha-Status
- **Version**: 1.0.0-beta
- **Status**: Funktionsfähig, Architektur finalisiert
- **Branches**: `pre` (default), `main`
- **Last Update**: 9.12.2025 - Cleanup & Branch-Reorganisation

## Architecture
- **Backend**: Python HTTP Bridge (localhost:8765)
- **Frontend**: HTML/CSS/JS Web Interface
- **Engine**: FIO (Homebrew oder vendored binary)
- **Pattern**: Web GUI → HTTP Bridge → diskbench CLI → FIO

## Tech Stack
- **Backend**: Python 3.7+ (Standard Library only)
- **Database**: Keine (JSON für Ergebnisse)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Integration**: Homebrew FIO oder vendor/fio/macos/arm64/fio

## Features
- Quick Max Speed Test (3 Min)
- QLab ProRes 422 Show Pattern (2.75h)
- QLab ProRes HQ Show Pattern (2.75h)
- Thermal Maximum Analyser (1.5h)

## Constraints
- **Budget**: Open Source Projekt
- **Security**: Input-Validierung erforderlich
- **Compliance**: macOS-kompatibel
- **Architecture**: Keine komplexen Frameworks

## Development
- **Language**: Deutsch für Doku, Englisch für Code
- **Date Format**: Österreichisch (30.5.2025)
- **Money Format**: Österreichisch (10.320,00 €)
- **Strategy**: MVP-First, pragmatisch

## HOLDS
- **HOLD-001**: DMG-Packaging (Phase 3)
- **HOLD-002**: Code-Signing (bei 100+ Users)
- **HOLD-003**: Auto-Update Mechanismus (Phase 3)
- **HOLD-004**: FIO SHM Issues (Workaround existiert)
- **HOLD-005**: Browser Security (Monitoring)

## Core Modules
1. **bridge-server/**: HTTP API Server
2. **diskbench/**: CLI Test-Engine
3. **web-gui/**: Browser Interface
4. **tests/**: Unit und Integration Tests
5. **vendor/**: Vendored FIO binary (offline use)

## Recent Changes (9.12.2025)
- Web-GUI Major Rework (UI/UX improvements)
- Bridge Server enhanced error handling
- 7 neue Unit Tests hinzugefügt
- Makefile und Build Scripts
- Vendored FIO binary für offline use
- Branch-Struktur: pre (default) + main
