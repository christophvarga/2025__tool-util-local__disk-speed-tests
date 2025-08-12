# QLab Disk Performance Tester - Process Rules
*Version 1.0 - Erstellt am 29.07.2025*

## ⚙️ Workflow  Regeln

### 📋 Projektplanung
- **Hauptdokumente**: `llm-context.md`, `grand-plan.md`, `architecture.md`
- **Umstellung**: Aufteilung von Phasen in übersichtliche Aufgaben
- **Verfolgung**: Tägliche Updates in `phase-goals.md`

### 🛠️ Entwicklung
- **Code-Prinzipien**: DRY-Prinzip, einfache und modulare Lösungen
- **Tools**: Python 3.7+, Homebrew für FIO, SQLite für State
- **Code Reviews**: Vor jedem Merge in den Hauptzweig
- **State Management**: SQLite (Migration von JSON in Sprint 5)

### ❗ Fehlerbehandlung
- **Fehlertypen**: „Permission Denied“, Testabbrüche
- **Lösungen im Code**: Volumes verwenden, klare Fehlermeldungen
- **Testing**: Beta-Tester für Feedback

### 🌀 Iterationen
- **Sprint Dauer**: 2 Wochen (6 Sprints total)
- **Zielsetzung**: Klar definierte Deliverables
- **Meeting-Kadenz**: Wöchentliche Stand-ups (Freitags), Sprint-Reviews

## ⚡ Kommunikation
- **Slack**: Für tägliche Kommunikation
- **GitHub Issues**: Für Bug Tracking und Feature Requests
- **Qlab Forum**: Für Community Feedback

## 📑 Dokumentation
- **README.md**: Detaillierte Installationsanweisungen
- **FAQ**: Abschnitt für häufige Fragen und bekannte Probleme
- **Erklärung**: Tooltips in der GUI

## 🚦 Risiko Management
- **Tech-Risiken**: macOS Updates, FIO Inkompatibilität
- **Antworten**: Bereitschaftsplan für jedes Major Release

## 📊 KPI Tracking
- **Installationszeit**: Must be < 5 minutes
- **Testabbruch-Rate**: < 5%
- **Benutzerzufriedenheit**: > 4.5/5

## 🚀 Bereitstellung
- **Release Zyklus**: Hauptversion alle 6 Monate
- **Beta Releases**: Häufigere kleinere Updates
- **Distribution**: GitHub, QLab Community

## 🎯 Nächste Schritte (Diese Woche)
1. **roll out improvements**: Start-Script und Fehlerbehandlung
2. **refactoring sprint**: Woche 1 Ziele fertigmachen
3. **prepare beta**: Beta-Tests für frühen September vorbereiten

---

*Versionierung ist pro Document-Update erforderlich*
