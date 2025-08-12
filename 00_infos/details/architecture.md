# QLab Disk Performance Tester - Architektur Analyse
*Version 1.0 - Erstellt am 29.07.2025*

## 🏗️ Architektur-Übersicht

### Komponenten-Architektur (3-Tier)
```
┌─────────────────────┐      ┌──────────────────┐      ┌─────────────┐
│   Web Browser       │ ←──→ │  Bridge Server   │ ←──→ │  FIO Engine │
│   (Frontend)        │ HTTP │  (Python HTTP)   │ Proc │  (Homebrew) │
│                     │ 8765 │                  │      │             │
└─────────────────────┘      └──────────────────┘      └─────────────┘
         ↓                            ↓                        ↓
    HTML/CSS/JS                  server.py                diskbench/
    (Vanilla)                  (No Framework)            (CLI Helper)
```

## 🔍 Komponenten-Analyse

### 1. Web GUI (Frontend)
**Technologie**: Vanilla HTML/CSS/JavaScript
- **Keine Frameworks**: Bewusste Entscheidung gegen React/Vue
- **Direkte DOM-Manipulation**: `app.js` mit 1800+ Zeilen
- **Responsive Design**: CSS Grid/Flexbox
- **Real-time Updates**: HTTP-Polling (kein WebSocket)

**Schlüssel-Features**:
- Setup Wizard für FIO-Installation
- Live Progress Monitoring
- 4 QLab-spezifische Test-Pattern
- Test-Result Analyzer

### 2. Bridge Server (Middleware)
**Technologie**: Python HTTP Server (Standard Library)
- **Kein Flask/Django**: `http.server.BaseHTTPRequestHandler`
- **Process Management**: subprocess.Popen für FIO
- **State Persistence**: JSON-basiert
- **Unsandboxed Execution**: Kritisch für macOS FIO

**API Endpoints**:
```python
/api/status          # System & FIO Status
/api/disks           # Disk Discovery
/api/test/start      # Test Initiation
/api/test/{id}       # Progress Monitoring
/api/setup           # FIO Installation
/api/validate        # System Validation
```

**Kritische Architektur-Entscheidungen**:
1. **Process Group Management**: Nutzt `start_new_session=True`
2. **Orphaned Process Cleanup**: Aktives PID-Tracking
3. **macOS SHM Workarounds**: Erkennt und behandelt Shared Memory Issues

### 3. Diskbench CLI (Test Engine)
**Technologie**: Python CLI Tool
- **Modular aufgebaut**: commands/, core/, utils/
- **FIO Wrapper**: Abstrahiert FIO-Komplexität
- **JSON Output**: Strukturierte Ergebnisse

**Test Pattern Engine** (`qlab_patterns.py`):
```python
QLAB_PATTERNS = {
    'quick_max_mix': {        # 5 Min Quick Test
        'duration': 300,
        'fio_template': '...' # Multi-Job Mixed R/W
    },
    'prores_422_real': {      # 30 Min ProRes 422
        'duration': 1800,
        'fio_template': '...' # Realistic Video Pattern
    },
    'prores_422_hq_real': {   # 30 Min ProRes HQ
        'duration': 1800,
        'fio_template': '...' # Higher Bandwidth
    },
    'thermal_maximum': {      # 60 Min Thermal Test
        'duration': 3600,
        'fio_template': '...' # Sustained Maximum Load
    }
}
```

### 4. FIO Integration
**Herausforderung**: macOS Shared Memory Limitations
- **Standard FIO**: Oft `failed to setup shm segment` Fehler
- **Lösung 1**: Homebrew FIO mit Workarounds
- **Lösung 2**: Custom-compiled `fio-nosmh` Version

**FIO Discovery Priority**:
```python
fio_candidates = [
    '/usr/local/bin/fio-nosmh',   # Custom no-SHM (höchste Priorität)
    '/opt/homebrew/bin/fio',      # Apple Silicon Homebrew
    '/usr/local/bin/fio',         # Intel Homebrew
]
```

## 🔄 Datenfluss-Architektur

### Test-Initiierung
```
1. User wählt Test in Web GUI
2. app.js → POST /api/test/start
3. server.py validiert Parameter
4. Spawnt diskbench subprocess
5. diskbench generiert FIO config
6. FIO läuft in separatem Process Group
```

### Progress Monitoring
```
1. Web GUI pollt /api/test/{id} (1s Intervall)
2. Bridge Server tracked Process Status
3. Live Metrics über Process State
4. Graceful Degradation bei Disconnects
```

### Result Processing
```
1. FIO → JSON Output File
2. diskbench parsed & enhanced Results
3. Bridge Server cacht Results
4. Web GUI rendert QLab-spezifische Analyse
```

## 🛡️ Architektur-Patterns

### 1. **Separation of Concerns**
- Frontend: Nur Presentation & User Interaction
- Bridge: Process Management & API
- CLI: Test Logic & FIO Integration

### 2. **Fail-Safe Design**
- Orphaned Process Detection beim Start
- Persistent State über Restarts
- Ehrliche Fehlerkommunikation

### 3. **Platform-Specific Adaptations**
- macOS SHM Issue Handling
- Homebrew Path Detection
- Apple Silicon vs Intel Support

### 4. **No Over-Engineering**
- Keine unnötigen Abstraktionen
- Direkte subprocess Calls
- Einfache JSON-Kommunikation

## 🚨 Kritische Architektur-Risiken

### 1. **Single-Process Bridge Server**
- Kein Load Balancing
- Blockiert bei langen Operations
- Lösung: Async/Threading für lange Tasks

### 2. **HTTP Polling statt WebSocket**
- Höhere Latenz für Updates
- Mehr Requests/Bandbreite
- Trade-off: Einfachheit vs Effizienz

### 3. **Unsandboxed Execution**
- Sicherheitsrisiko bei Fehlkonfiguration
- Notwendig für FIO auf macOS
- Mitigation: Input Validation

### 4. **Process Management Komplexität**
- Orphaned FIO Processes möglich
- Manual Cleanup erforderlich
- PID Tracking nicht 100% zuverlässig

## 📊 Performance-Charakteristika

### Skalierbarkeit
- **Concurrent Tests**: Explizit auf 1 limitiert
- **User Sessions**: Unbegrenzt (stateless)
- **Test Duration**: Bis zu 3+ Stunden

### Resource Usage
- **Memory**: Minimal (~50MB Bridge Server)
- **CPU**: Niedrig außer während FIO Tests
- **Disk I/O**: Komplett von FIO Tests dominiert

### Bottlenecks
1. **FIO Shared Memory**: macOS Limitation
2. **Single-threaded Bridge**: Blockiert bei Tests
3. **File-based State**: Keine echte DB

## 🔧 Erweiterbarkeit

### Gut erweiterbar:
- Neue Test Patterns (einfach in QLAB_PATTERNS)
- Zusätzliche API Endpoints
- Alternative FIO Binaries

### Schwer erweiterbar:
- Concurrent Test Support (Architektur-Änderung)
- Real-time Streaming (WebSocket nötig)
- Cross-platform Support (macOS-spezifisch)

## 🎯 Architektur-Bewertung

### Stärken ✅
- **Pragmatisch**: Funktioniert ohne komplexe Dependencies
- **Wartbar**: Klare Trennung, einfache Komponenten
- **macOS-optimiert**: Spezifische Workarounds implementiert

### Schwächen ❌
- **Skalierbarkeit**: Single-Process Limitations
- **Error Recovery**: Manuelle Intervention oft nötig
- **Testing**: Keine automatisierten Tests sichtbar

### Empfehlungen 💡
1. **Async Bridge Server**: Verhindert Blocking
2. **Process Pool**: Für concurrent Tests
3. **SQLite State**: Robuster als JSON Files
4. **WebSocket Option**: Für echtes Real-time
5. **Docker Option**: Für konsistente Umgebung

## 📐 Architektur-Diagramm (Detailliert)

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   app.js    │  │  styles.css  │  │   index.html    │   │
│  │ (1800+ LOC) │  │ (Material-UI)│  │  (Single Page)  │   │
│  └──────┬──────┘  └──────────────┘  └─────────────────┘   │
└─────────┼───────────────────────────────────────────────────┘
          │ HTTP Requests (JSON)
          │ Port 8765
┌─────────▼───────────────────────────────────────────────────┐
│                    Bridge Server (Python)                   │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  HTTPHandler    │  │ DiskBenchBridge│ │Process Manager│ │
│  │  - GET/POST     │  │ - State Mgmt  │  │ - PID Track  │  │
│  │  - CORS Headers │  │ - Test Queue  │  │ - Cleanup    │  │
│  └────────┬────────┘  └───────┬──────┘  └──────┬───────┘  │
└───────────┼────────────────────┼─────────────────┼──────────┘
            │                    │                  │
            │  subprocess.Popen  │                  │
┌───────────▼────────────────────▼─────────────────▼──────────┐
│                    diskbench CLI (Python)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  main.py    │  │qlab_patterns │  │  fio_runner.py  │   │
│  │ - ArgParse  │  │- Test Configs│  │ - FIO Wrapper   │   │
│  │ - Commands  │  │- Templates   │  │ - Result Parse  │   │
│  └─────────────┘  └──────────────┘  └────────┬────────┘   │
└────────────────────────────────────────────────┼────────────┘
                                                 │
                                    exec()       │
┌────────────────────────────────────────────────▼────────────┐
│                      FIO (Homebrew)                         │
│                 /opt/homebrew/bin/fio                       │
│              oder /usr/local/bin/fio-nosmh                  │
└─────────────────────────────────────────────────────────────┘
```

Diese Architektur ist ein gelungenes Beispiel für pragmatisches Engineering: Sie löst das spezifische Problem (QLab Disk Testing auf macOS) ohne Over-Engineering, macht aber bewusste Trade-offs bei Skalierbarkeit und Eleganz zugunsten von Einfachheit und Funktionalität.
