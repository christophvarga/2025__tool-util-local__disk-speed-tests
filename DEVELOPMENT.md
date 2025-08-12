# QLab Disk Performance Tester - Entwicklungsleitfaden

Version 1.1 – 12.8.2025

Diese Dokumentation ist für Entwickler gedacht, die am QLab Disk Performance Tester arbeiten oder beitragen möchten.

## 🛠️ Entwickler-Quickstart (konzis)

Voraussetzungen: macOS 10.14+, Python 3.7+, Git

Schnellstart:
```bash
# Repo klonen
git clone <repository-url>
cd qlab-disk-performance-tester

# Saubere Dev-Umgebung (nur Tests)
python3 -m venv .venv-clean
source .venv-clean/bin/activate
python -m pip install -U pip setuptools wheel pytest

# Tests ausführen
python -m pytest -q
```

Laufzeit (App-Stack):
- ./start.sh startet Bridge-Server und öffnet die Web-GUI. Es wird bei Bedarf FIO via Homebrew installiert. Diese Umgebung ist von .venv-clean getrennt.

## 🏗️ **Projektstruktur**

```
qlab_disk_performance/
├── diskbench/                  # FIO-basierte Test-Engine
│   ├── main.py                # CLI-Einstiegspunkt
│   ├── commands/             # Befehlsimplementierungen
│   ├── core/                 # FIO-Engine und Test-Patterns
│   └── utils/                # Hilfsprogramme und Validierung
├── web-gui/                  # Web-Schnittstelle
│   ├── index.html            # Hauptinterface
│   ├── styles.css            # Styling
│   └── app.js                # Anwendungslogik
├── bridge-server/            # HTTP API Server
│   └── server.py             # Bridge Kommunikation
└── memory-bank/              # Entwicklungsdokumentation
```

## 🚀 **Im Entwicklungsmodus ausführen**

### Web-GUI Anwendung ausführen
```bash
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Anwendung ausführen
./start.sh    # Startscript für vollautomatisierte Umgebung
```

## 🔧 **Entwicklungsrichtlinien**

### Code-Stil
- **PEP 8** Konformität
- **Type Hints** wo angemessen
- **Docstrings** für alle öffentlichen Funktionen
- **Fehlerbehandlung** mit korrekten Ausnahmen

### Architekturprinzipien
- **Modulare Architektur**: Separate Module für klare Trennung
- **Mac-spezifische Optimierungen**: Berücksichtigung von macOS Eigenheiten
- **Sicherheit**: Eingabevalidierung und isoliertes Testen

### Teststrategie
- **Unittests** für einzelne Funktionen
- **Integrationstests** für gesamte Workflows
- **Manuelles Testen** für spezialisierte Hardware

## 📚 Memory Bank System

Das Projekt verwendet eine Memory Bank für Kontext:
- `memory-bank/projectbrief.md` - Projektscope und Ziele
- `memory-bank/techContext.md` - Technische Restriktionen
- `memory-bank/activeContext.md` - Aktueller Entwicklungsstatus
- `memory-bank/progress.md` - Entwicklungsgeschichte

## 🤝 **Beitragen**

### Vor Contribution
1. **Memory Bank** lesen, um den Projekthintergrund zu verstehen
2. **Architekturprinzipien** befolgen
3. **Tests auf mehreren Macs** durchführen
4. **Dokumentation aktualisieren** bei Änderungen

### Pull-Request Prozess
1. **Repository forken**
2. **Feature-Branch** vom Main-Branch erstellen
3. **Änderungen vornehmen** und testen
4. **Dokumentation aktualisieren**
5. **Pull-Request einreichen**

---

**Happy coding! 🚀**

© 2025 varga.media
