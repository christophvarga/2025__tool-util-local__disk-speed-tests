# QLab Disk Performance Tester - LLM Context
*Version 1.1 – 12.8.2025*

## 🎯 Projekt-Mission
Ein professionelles Disk Performance Testing Tool speziell für QLab Video-Playback-Anforderungen. Web-basierte GUI mit FIO-Engine für realistische Show-Pattern-Tests.

## 🚀 Current State 
- **Phase**: MVP-Phase (abgeschlossen, Alpha-Status)
- **Version**: 1.0.0-beta
- **Status**: Funktionsfähig, Architektur finalisiert
- **Next Steps**: 
  1. Dokumentation standardisieren
  2. Code-Organisation verbessern
  3. Test-Coverage erhöhen

## 🏗️ Architecture
- **Backend**: Python HTTP Bridge (localhost:8765)
- **Frontend**: HTML/CSS/JS Web Interface
- **Engine**: FIO (Homebrew) für Disk-Tests
- **Pattern**: Web GUI → HTTP Bridge → diskbench CLI → FIO

## 💻 Tech Stack
- **Backend**: Python 3.7+ (Standard Library only)
- **Database**: Keine (JSON für Ergebnisse)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Integration**: Homebrew FIO

## 🎨 Features
- Quick Max Speed Test (3 Min)
- QLab ProRes 422 Show Pattern (2.75h)
- QLab ProRes HQ Show Pattern (2.75h)
- Thermal Maximum Analyser (1.5h)

## 🔒 Constraints
- **Budget**: Open Source Projekt
- **Security**: Input-Validierung erforderlich
- **Compliance**: macOS-kompatibel
- **Architecture**: Keine komplexen Frameworks

## 🌍 Development
- **Language**: Deutsch für Doku, Englisch für Code
- **Date Format**: Österreichisch (30.5.2025)
- **Money Format**: Österreichisch (10.320,00 €)
- **Strategy**: MVP-First, pragmatisch

## ⚠️ HOLDS
- **HOLD-001**: DMG-Packaging (nicht MVP-kritisch)
- **HOLD-002**: Code-Signing (später evaluieren)
- **HOLD-003**: Auto-Update Mechanismus (Phase 2)

## 📦 Core Modules
1. **bridge-server/**: HTTP API Server
2. **diskbench/**: CLI Test-Engine
3. **web-gui/**: Browser Interface
4. **memory-bank/**: Entwicklungs-Doku

## 🔄 Current Focus
Dokumentation und Code-Organisation nach Standards aufräumen, bestehende Funktionalität erhalten.
