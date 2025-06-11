# QLab Disk Performance Tester - Standalone Edition

**Professioneller Disk-Performance-Tester für QLab Video-Workflows**

## 🎯 Überblick

Ein speziell für QLab-Anwendungen entwickelter Disk-Performance-Tester, der realistisch ProRes 422 4K+HD Streaming-Szenarien simuliert. **Vollständig standalone** - funktioniert auf neuen Apple Silicon Macs ohne externe Dependencies.

## ✨ Hauptmerkmale

- **🔋 Vollständig Standalone**: Keine pip, Homebrew oder Internet-Verbindung erforderlich
- **🍎 Apple Silicon Exclusive**: Optimiert für M1/M2/M3 Macs
- **🎬 QLab-Optimiert**: Realistische ProRes 422 Test-Szenarien mit fio-Engine
- **🌡️ Live-Monitoring**: SSD-Temperatur und I/O-Aktivität in Echtzeit
- **⚡ Moderne Test-Modi**: 3 optimierte Test-Profile für verschiedene Anwendungsfälle
- **📊 Professionelle Berichte**: Detaillierte Performance-Analyse mit QLab-spezifischen Empfehlungen

## 🚀 Installation

### Für frische macOS Systeme (empfohlen):

```bash
# 1. Paket entpacken/herunterladen
cd qlab-disk-tester

# 2. Installation prüfen
chmod +x install.sh
./install.sh

# 3. Direkt starten
python3 qlab_disk_tester.py
```

**Das war's!** Keine weiteren Dependencies erforderlich.

## 📋 System-Anforderungen

- **macOS**: 10.15+ (Catalina oder neuer)
- **Python**: 3.7+ (standardmäßig auf macOS vorhanden)
- **Architektur**: Apple Silicon (M1/M2/M3) **ONLY**
- **Speicher**: Minimum 1GB freier Speicherplatz für Tests

## 🎮 Test-Modi

### 0. Setup Check (30s)
- **Zweck**: Schnelle Funktionsüberprüfung
- **Dauer**: 30 Sekunden
- **Ideal für**: Erste Installation, schnelle Verifikation

### 1. QLab Show-Pattern Test (2.5h)
- **Phase 1**: Show-Vorbereitung (30 Min) - 400 MB/s
- **Phase 2**: Normale Show-Last (90 Min) - 700 MB/s mixed I/O
- **Phase 3**: Finale/Überblendungen (30 Min) - 1800 MB/s peaks
- **Ideal für**: Realistische QLab-Workflows mit thermischem Stress-Test

### 2. Max Sustained Performance (2h)
- **Zweck**: Maximum sustained Durchsatz über 2 Stunden
- **Parameter**: 4MB Blöcke, 16 parallele Jobs, maximale I/O-Tiefe
- **Ideal für**: Thermal-Throttling-Tests, absolute Performance-Grenzen

## 📊 Performance-Bewertung

### ProRes 422 Streaming-Standards:
- **✅ EXCELLENT**: ≥2100 MB/s (volle Überblendungs-Performance)
- **⚠️ ACCEPTABLE**: ≥656 MB/s (normale Show-Performance)
- **❌ POOR**: <656 MB/s (ungeeignet für 4K+HD Setup)

### Live-Monitoring zeigt:
- 🌡️ **SSD-Temperatur** (mit Thermal-Throttling-Erkennung)
- 💻 **CPU-Auslastung** während I/O-Tests
- 💾 **Aktuelle I/O-Rate** in MB/s
- ⏱️ **Echtzeit-Status** alle 2 Sekunden

## 📁 Ausgabe-Dateien

```
results/
├── qlab_test_report_[Disk]_[Modus]_[Timestamp].json
└── monitoring_log.json (bei langen Tests)

~/fio_debug/
└── fio_debug_[timestamp].log (Debug-Informationen)
```

## 🔧 Technische Details

### Standalone-Architektur:
- **Python Standard Library**: Keine externen pip packages
- **Bundled fio**: Vorkompilierte Binary für Apple Silicon
- **Native macOS APIs**: powermetrics, pmset für Temperatur-Monitoring
- **Zero-Dependency**: Funktioniert auf "nackten" neuen Apple Silicon Macs

### ProRes 422 Test-Spezifikationen:
```
4K ProRes 422 @ 50fps: 440 MB/s
HD ProRes 422 @ 50fps: 72 MB/s
Normal-Szenario: 1x 4K + 3x HD = 656 MB/s
Überblendung: 3x Normal = 1968 MB/s
Safety Buffer: 2100 MB/s
```

### Thermal-Management:
- Kontinuierliche SSD-Temperatur-Überwachung
- Thermal-Throttling-Erkennung via macOS pmset
- Intelligente Lastverteilung bei kritischen Temperaturen

## 🏢 Professionelle Anwendung

### Für QLab System-Designer:
- Validierung neuer Hardware vor Installation
- Performance-Baseline für verschiedene Storage-Lösungen
- Thermal-Verhalten bei langen Shows (2+ Stunden)

### Für Technical Directors:
- Show-spezifische Performance-Tests
- Backup-Storage-Validierung
- Disaster-Recovery-Planung

### Für Venue Engineers:
- Regelmäßige System-Health-Checks
- Preventive Maintenance Scheduling
- Performance-Degradation-Tracking

## 🚨 Wichtige Hinweise

### Storage-Kompatibilität:
- ✅ **Externe SSDs/HDDs**: Vollständig unterstützt
- ✅ **Thunderbolt/USB-C**: Optimale Performance
- ⚠️ **Time Machine Volumes**: Oft schreibgeschützt
- ⚠️ **System Volume**: Nur bei ausreichend freiem Speicher

### Performance-Faktoren:
- **Verbindungstyp**: Thunderbolt > USB 3.2 > USB 3.0
- **Storage-Medium**: NVMe SSD > SATA SSD > HDD
- **Thermal-Management**: Aktive Kühlung empfohlen für Dauerbetrieb
- **Fragmentierung**: Defragmentierte Volumes für optimale Performance

## 📞 Support & Troubleshooting

### Debug-Informationen:
- Vollständige fio-Logs: `~/fio_debug/`
- JSON-Reports: `results/`
- Live-Monitoring-Logs: `monitoring_log.json`

### Häufige Probleme:

**"Volume ist schreibgeschützt"**
→ Verwenden Sie externe Datenplatten statt System-/Backup-Volumes

**"fio binary not found"**
→ Führen Sie `./install.sh` erneut aus oder prüfen Sie `bin/` Ordner

**Niedrige Performance bei USB**
→ Prüfen Sie USB-Verbindung und Thermal-Throttling

**Thermal-Throttling**
→ Verbessern Sie Belüftung oder verwenden Sie aktive Kühlung

## 🎯 Entwicklung für QLab-Profis

Dieses Tool wurde von QLab-Praktikern für QLab-Praktiker entwickelt. Es berücksichtigt:

- **Reale Show-Patterns**: Warm-up, normale Belastung, Überblendungs-Peaks
- **Thermal-Realität**: Stunden-lange Tests simulieren echte Show-Bedingungen
- **Hardware-Vielfalt**: Von MacBook Pro bis Mac Studio, alle Formfaktoren
- **Venue-Constraints**: Portable Testing ohne Internet-Abhängigkeiten

---

**Made for QLab Professionals** | Apple Silicon Exclusive | fio-Based | Zero Dependencies | Professional Grade