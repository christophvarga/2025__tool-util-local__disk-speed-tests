# QLab Disk Performance Tester

Version 1.3.3 – 9.9.2025

Professionelles Disk Performance Testing Tool optimiert für QLab Audio/Video-Anwendungen. Web-basierte Architektur mit Python Bridge Server und FIO Engine für realistische Show-Pattern-Tests.

## 🏗️ Architektur-Übersicht

Drei-Schichten-Architektur für maximale Flexibilität und einfache Wartung:

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Web Browser   │ ←→  │  Bridge Server   │ ←→  │  FIO Engine │
│   (Frontend)    │HTTP │  (Python HTTP)   │Proc │  (Homebrew) │
│                 │8765 │                  │     │             │
└─────────────────┘     └──────────────────┘     └─────────────┘
```

### Komponenten:

1. **Web GUI** (`web-gui/`) - Moderne Browser-basierte Oberfläche
2. **Bridge Server** (`bridge-server/server.py`) - HTTP API Server und Process Manager
3. **Diskbench CLI** (`diskbench/`) - Test Engine und FIO Wrapper
4. **FIO** - Industry-Standard Disk Benchmark (via Homebrew)

• Alles läuft lokal auf Ihrem Mac  
• Keine Sandbox-Beschränkungen  
• Open Source ohne Lizenzkosten

## 🚀 Quick Start (< 5 Minuten)

### Offline Start (ohne Internet, ohne SIP‑Eingriff)

Variante A – Offline Bundle (empfohlen für neuen Mac ohne Python/Internet):
1) Bundle bauen (einmalig auf einem Dev-Mac):
   ```bash
   bash scripts/build_offline_bundle.sh
   ```
   Das erzeugt: `dist/offline_bundle-<arch>/`
2) Ordner `dist/offline_bundle-<arch>/` auf eine externe SSD kopieren.
3) Auf dem Ziel-Mac: Doppelklick auf `Start Diskbench Bridge.command`.

Variante B – Aus dem Quellcode (benötigt System-Python):
Voraussetzung: Vendortes FIO-Binary vorhanden unter `vendor/fio/macos/<arch>/fio` (wird bei Bedarf automatisch aus Homebrew kopiert).

1) Repo auf den Ziel-Mac kopieren (AirDrop/USB)
2) Start im Terminal:
   ```bash
   bash scripts/start.sh
   # alternativ
   ./start.sh
   ```
3) Browser öffnet http://localhost:8765/

Variante C – Direktstart per Doppelklick (aus Repo-Root):
1) Doppelklick auf `Start Diskbench Bridge.command`
   - nutzt automatisch onedir-/onefile-Build, falls vorhanden; sonst Python-Fallback
2) Browser öffnet http://localhost:8765/

Hinweise:
- Das Bundle enthält eine vendorte FIO-Binary und ist offline lauffähig.
- Gatekeeper: Beim ersten Start ggf. Rechtsklick → Öffnen bestätigen (kein SIP-Eingriff nötig).

#### Offline Checklist
- FIO-Binary liegt unter `vendor/fio/macos/arm64/fio` und ist ausführbar (`chmod +x vendor/fio/macos/arm64/fio`).
- Optional: Packaged Bridge vorhanden unter `dist/diskbench-bridge` (gebaut via PyInstaller) – dann kein System-Python nötig.
- Gatekeeper: Beim ersten Start ggf. Rechtsklick → Öffnen bestätigen (kein SIP-Eingriff nötig).
- Internet: Nicht erforderlich für Laufzeit (UI, Bridge, FIO laufen lokal).

#### Launcher-Übersicht
- Doppelklick (Repo-Root): `Start Diskbench Bridge.command`
- Start (Terminal): `bash scripts/start.sh` – nutzt automatisch das PyInstaller-Binary, sonst `python3`; optional `--no-browser`/`--no-venv`.
- Alternativ: `./start.sh`

### Online Setup (Alternative)

```bash
# 1. FIO installieren (falls nicht vorhanden)
brew install fio

# 2. Bridge Server starten
python3 bridge-server/server.py

# 3. Browser öffnen
open http://localhost:8765/
```

### Server stoppen:

```bash
./stop.sh
```

## 📋 Verfügbare Test-Patterns

### QLab-optimierte Tests:

1. **Quick Max Mix Test** (5 Minuten) ⭐ *Empfohlen für schnelle Analyse*
   - Gemischte Read/Write Workloads
   - Maximale Performance-Ermittlung
   - Test-ID: `quick_max_mix`
   - Dauer: 5 Minuten

2. **ProRes 422 Real-World Test** (30 Minuten)
   - Realistische ProRes 422 Playback-Simulation
   - Mehrere Streams mit Crossfades
   - Test-ID: `prores_422_real`
   - Dauer: 30 Minuten

3. **ProRes 422 HQ Real-World Test** (30 Minuten)
   - Höhere Bandbreite für ProRes HQ
   - 6 parallele Jobs für Heavy Load
   - Test-ID: `prores_422_hq_real`
   - Dauer: 30 Minuten

4. **Thermal Maximum Test** (60 Minuten)
   - Langzeit-Belastungstest
   - Thermal Throttling Erkennung
   - Test-ID: `thermal_maximum`
   - Dauer: 60 Minuten

## 🔧 Start & Imports

- Empfohlener Start (aus dem Projekt-Root):
  ```bash
  python -m diskbench.main --help
  ```
- Warum? So werden alle Module über den Paketnamen diskbench importiert (konsistente Imports).
- Alternativ: Paket im Editiermodus installieren (macht diskbench überall importierbar und installiert einen CLI-Befehl `diskbench`):
  ```bash
  # aus dem Projekt-Root
  python -m pip install -e .
  # danach funktionieren z. B.
  python -m diskbench.main --list-disks --json
  # oder der CLI-Befehl (Konsole)
  diskbench --list-disks --json
  ```

Hinweise zu Imports
- Innerhalb der Codebasis nutzen wir absolute Paket-Imports (from diskbench.…. import …). Das ist robust gegen unterschiedliche Startverzeichnisse.
- Für Legacy-Tests existieren Kompatibilitäts-Shims (commands/*, core/*) auf Root-Ebene, die alte Imports (from commands.… / from core.… ) weiterleiten. Langfristig bitte auf diskbench.* umstellen.

## 🔧 Diskbench CLI Befehle

Das `diskbench` CLI Tool bietet umfassende Kommandozeilen-Funktionalität:

### System-Validierung
```bash
cd diskbench
python main.py --validate
```

### Verfügbare Disks anzeigen
```bash
python main.py --list-disks --json
```

### Performance Tests ausführen
```bash
# Quick Max Mix Test (5 Min)
python main.py --test quick_max_mix --disk /Volumes/Media --size 10 --output quick.json

# ProRes 422 Real-World Test (30 Min)
python main.py --test prores_422_real --disk /Volumes/Media --size 10 --output prores422.json

# ProRes 422 HQ Real-World Test (30 Min)
python main.py --test prores_422_hq_real --disk /Volumes/Media --size 10 --output prores422hq.json

# Thermal Maximum Test (60 Min)
python main.py --test thermal_maximum --disk /Volumes/Media --size 10 --output thermal.json
```

### Kommandozeilen-Optionen
- `--test`: Test-Pattern (quick_max_mix, prores_422_real, prores_422_hq_real, thermal_maximum)
- `--disk`: Ziel-Disk Pfad (/dev/diskX oder /Volumes/Name)
- `--size`: Test-Dateigröße in GB (1-100)
- `--output`: Output JSON Datei
- `--progress`: Zeige Fortschritt während Test
- `--json`: Formatiere Output als JSON
- `--validate`: System-Validierung durchführen
- `--list-disks`: Liste verfügbare Disks
- `--version`: Version anzeigen

## 📊 Understanding Results

- Bewertungstool: `python scripts/evaluate_results.py --input /path/to/results.json [--test-type ...]`  
  - Alternativ via Makefile: `make evaluate INPUT=/path/to/results.json [TEST_TYPE=...] [OUTPUT=/path/to/report.json]`
- Kriterien: siehe `docs/evaluation-criteria.md`  
- Fallback (direktes fio): siehe `docs/fio-fallback/README.md`

### QLab Performance Analysis

Hinweis: Die Mindestdurchsatzwerte in der Bridge-Oberfläche wurden auf unsere strengeren Ziele angehoben (quick ≥ 300 MB/s, ProRes 422 ≥ 350 MB/s, ProRes 422 HQ ≥ 700 MB/s, Thermal ≥ 400 MB/s).

Results include QLab-specific performance analysis:

- **Excellent** ✅: Perfect for complex shows, 4K video, rapid cue triggering
- **Good** ✅: Suitable for most QLab applications, standard video playback
- **Fair** ⚠️: Basic usage only, pre-load cues, avoid rapid sequences
- **Poor** ❌: Not suitable for live performance, upgrade recommended

### Key Metrics

- **Sequential Read/Write**: Large file streaming (video files)
- **Random Read/Write**: Small file access (audio samples, cues)
- **IOPS**: Input/Output Operations Per Second
- **Latency**: Response time for disk operations
- **Bandwidth**: Data transfer rate (MB/s)

### Recommendations

The tool provides specific recommendations based on test results:
- Hardware upgrade suggestions
- QLab configuration tips
- Performance optimization advice
- Workflow recommendations

## 🛠️ Development

### Installation (optional, empfohlen für globale Nutzung)

#### Packaging (PyInstaller, dev)
- Erzeugt ein self-contained Binary für Apple Silicon.
- Build:
  ```bash
  bash scripts/build_bridge_pyinstaller.sh
  ```
- Artefakte: `dist/diskbench-bridge` (onefile) oder `dist/diskbench-bridge/` (onedir).
- Der Launcher (.command) verwendet das Binary automatisch, falls vorhanden.

- Editiermodus (entwicklungsfreundlich):
  ```bash
  python -m pip install -e .
  ```
- Danach kann das CLI überall mit python -m diskbench.main aufgerufen werden.

### Project Structure

### Project Structure

```
├── diskbench/              # CLI entry point + engine
│   ├── main.py             # CLI entry point
│   ├── commands/           # Commands (test, list-disks, validate, setup)
│   ├── core/               # FIO runner and QLab patterns
│   └── utils/              # Utilities and validation
├── bridge-server/          # HTTP API server (Bridge)
│   └── server.py           # Bridge communication and process mgmt
├── docs/                   # Documentation
│   └── fio-fallback/       # Direct FIO usage templates and guide
├── tests/                  # Unit & integration tests
└── memory-bank/            # Development documentation
```

### Testing

- Test-Report Runner (LLM-Rule konform):
  ```bash
  make test-report
  # Artefakte unter 89_output/test_reports/<TS>/, symlink: 89_output/test_reports/latest
  ```

```bash
# Test helper binary
cd diskbench && python test_diskbench.py

# Test FIO availability
cd diskbench && python main.py --validate

# Test disk listing
cd diskbench && python main.py --list-disks
```

### Adding Custom Test Patterns

1. Edit `diskbench/core/qlab_patterns.py`
2. Add new test configuration
3. Update web GUI test options
4. Test with `--test custom_pattern_name`

## 🔒 Security & Safety

### Built-in Safety Features

- **Disk path validation**: Prevents access to system-critical paths
- **Space checking**: Ensures sufficient free space before testing
- **Parameter sanitization**: Validates all user inputs
- **Safe test directories**: Uses isolated test locations
- **Cleanup procedures**: Removes test files after completion

### Permissions

- **Web GUI**: Runs in browser sandbox with no system access
- **Helper Binary**: Requires disk access permissions for testing
- **Raw device access**: May require admin privileges for `/dev/disk*` testing

## 📈 Performance Expectations

### SSD Performance (Typical)
- Sequential Read: 400-600 MB/s
- Sequential Write: 350-500 MB/s
- Random Read: 40,000-80,000 IOPS
- Random Write: 35,000-70,000 IOPS
- Latency: <1ms

### HDD Performance (Typical)
- Sequential Read: 100-150 MB/s
- Sequential Write: 80-120 MB/s
- Random Read: 100-300 IOPS
- Random Write: 80-200 IOPS
- Latency: 8-15ms

## 🎯 QLab-Specific Recommendations

### For Excellent QLab Performance
- Use SSD storage for all media files
- Ensure >50,000 random read IOPS
- Maintain <2ms average latency
- Have >300 MB/s sequential read bandwidth

### For Basic QLab Usage
- Minimum 5,000 random read IOPS
- <10ms average latency
- >100 MB/s sequential read bandwidth
- Pre-load cues when possible

## 🐛 Troubleshooting

### Common Issues

**"FIO not found"**
- Ensure FIO is installed or use bundled version
- Check PATH environment variable
- Run `diskbench --validate` to verify

**"Permission denied"**
- Raw device testing requires admin privileges
- Use mounted volumes instead of raw devices
- Run with `sudo` if necessary for `/dev/disk*` access

**"Insufficient space"**
- Ensure target disk has enough free space
- Reduce test size parameter
- Clean up existing test files

**Web GUI not loading disks**
- Check that helper binary is working: `cd diskbench && python main.py --list-disks`
- Verify browser console for JavaScript errors
- Ensure all files are in correct locations

### Maintenance

- Aufräumen (nur Artefakte innerhalb des Repos; neueste Testreports bleiben erhalten):
  ```bash
  bash scripts/clean.sh
  ```

### Getting Help

### macOS Gatekeeper Hinweis
- Beim ersten Start eines nicht signierten Binaries kann macOS den Start blockieren.
- Lösung: Rechtsklick auf „Start Diskbench Bridge.command“ → Öffnen → Bestätigen.
- Dies ist kein Eingriff in SIP und erfordert keine Internetverbindung.

1. Run system validation: `cd diskbench && python main.py --validate`
2. Check the browser console for errors
3. Verify FIO installation and permissions
4. Test helper binary independently

## 📄 Lizenz

Dieses Projekt wird als Open Source für professionelle Audio/Video-Anwendungen bereitgestellt. MIT License.

## ✅ Validierung und aktuelle Änderungen

- Testsuite: 27/27 Tests erfolgreich (Stand: 2025-08-12)
- Behobene Punkte:
  - QLabTestPatterns korrekt als Klasse implementiert (Methoden und Attribute waren zuvor außerhalb des Klassenblocks)
  - Konsistente Testlisten-Ausgabe: JSON nutzt String-Test-IDs für Keys und die Reihenfolge-Liste
- Relevante Dateien:
  - diskbench/core/qlab_patterns.py
  - diskbench/main.py (Ausgabe von --list-tests)

## 🔄 Versions-Historie

- v0.9.0-beta (Juli 2025)
  - Web-basierte Architektur
  - 4 QLab-spezifische Test-Patterns
  - FIO Integration mit macOS Workarounds
  - Basis-Fehlerbehandlung

- v1.0.0 (geplant)
  - Vereinfachtes Setup mit start.sh
  - Verbesserte Fehlerbehandlung
  - Schnelle Test-Optionen (5–10 Min)
  - Chart.js Visualisierung
  - SQLite State Management
  - Stabilisierung und Beta-Tests
