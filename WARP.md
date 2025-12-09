# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Version 1.1 – 8.9.2025

Hinweis: Lies zuerst 00_infos/llm-context.md (Projektregeln, Phase, HOLDS).


1) Häufige Befehle (Build, Lint, Tests, Development)

- Voraussetzungen (macOS):
  - FIO installieren: brew install fio
  - Optionales venv (empfohlen, pro Repo eigenes venv):
    - python3 -m venv .venv && source .venv/bin/activate
    - Für Tests: python -m pip install -U pip pytest [pytest-cov]

- Diskbench CLI (lokal, ohne Build-Schritt):
  - Systemvalidierung: 
    - python diskbench/main.py --validate --json
  - Version + FIO-Status:
    - python diskbench/main.py --version --check-fio --json
  - Verfügbare Disks listen (nur gemountete Volumes, QLab-relevant):
    - python diskbench/main.py --list-disks --json
  - Verfügbare Tests (inkl. Anzeige-Reihenfolge + Labels):
    - python diskbench/main.py --list-tests --json
  - Einen Test ausführen (Beispiel Quick Max Mix, 10 GB, JSON-Ausgabe):
    - python diskbench/main.py --test quick_max_mix --disk /Volumes/TargetDisk \
      --size 10 --output /tmp/diskbench_quick.json --json --progress
  - Custom FIO-Config (Platzhalter ${DISK_PATH}, ${TEST_SIZE} werden ersetzt):
    - python diskbench/main.py --custom-config ./path/to/custom.fio --disk /Volumes/TargetDisk \
      --size 10 --output /tmp/custom.json --json
  - Setup-/Wartungsbefehle (Homebrew-FIO-Check/Workarounds):
    - Erkennen: python diskbench/main.py --detect
    - Installieren/Fix: python diskbench/main.py --install
    - Setup-Validierung: python diskbench/main.py --setup-validate

- Bridge Server (HTTP-Bridge, steuert diskbench und FIO):
  - Start: python bridge-server/server.py
  - Web-Oberfläche/API (lt. README): http://localhost:8765/
  - Nach Code-Änderungen: Server neu starten (Restart-Rule)

- Tests (pytest):
  - Test-Report (Runner, Artefakte + Coverage): make test-report
  - Alle Tests (direkt): python -m pytest tests -q
  - Einzelner Test: python -m pytest tests/test_fio_parser.py::TestFioParser::test_parse_current_fio_format -q
  - Coverage (direkt): python -m pytest tests --cov=diskbench.core.fio_runner -q
  - Ad-hoc Testscript: python diskbench/test_diskbench.py

- Lint/Format:
  - In diesem Repo nicht konfiguriert (keine .flake8/.ruff/.pylintrc gefunden).

- Auswertung & Cleanup:
  - Bewertung (diskbench oder fio JSON): python scripts/evaluate_results.py --input /path/to/results.json [--test-type ...]
    - Alternativ: make evaluate INPUT=/path/to/results.json [TEST_TYPE=...] [OUTPUT=/path/to/report.json]
  - Kriterien: docs/evaluation-criteria.md
  - Cleanup Artefakte (neuester Report bleibt): bash scripts/clean.sh


2) Big-Picture Architektur und Struktur

Ziel: Realistische, QLab-orientierte Disk-Performance-Tests über eine lokale Web-GUI, einen Python-Bridge-Server und die FIO-Engine.

- High-Level (lt. README):
  - Web GUI (Browser) ←HTTP→ Bridge Server (Python) ←Proc→ FIO (Homebrew)
  - Alles lokal auf macOS; Fokus auf gemountete Volumes (QLab-Realität)

- Zentrale Komponenten (nur die wichtigen, big-picture):
  - bridge-server/server.py
    - Lokaler HTTP-Server als „Bridge“: Start/Stop von Tests, Status-Abfrage, Persistenz
    - Prozess- und Zustandsmanagement:
      - Single-Instance-Enforcement (nur ein Test gleichzeitig)
      - Tracking laufender Tests und Subprozesse (FIO) inkl. Prozessgruppen-Kill
      - Persistenter Zustand in memory-bank/diskbench_bridge_state.json
      - Aufräumen verwaister FIO-Prozesse (ps aux → SIGTERM/SIGKILL)
    - Robustheit: Extrahiert JSON aus gemischter STDOUT-Ausgabe; setzt env (FIO_DISABLE_SHM=1, PATH mit Homebrew)
    - Mapped Web-Test-IDs auf diskbench-Test-IDs (Abwärtskompatibilität)

  - diskbench/main.py (CLI Entry Point)
    - Argument-Parser mit exklusiven Modi: --test, --custom-config, --list-disks, --validate, --version, --detect/--install/--setup-validate, --list-tests
    - Validierungen: Disk-Pfad, Zielverzeichnis beschreibbar, Größe (1–1000 GB)
    - Orchestrierung: leitet an Commands weiter, schreibt JSON-Resultate in --output

  - diskbench/commands/
    - test.py (DiskTestCommand)
      - Holt Testkonfigurationen aus core/qlab_patterns.py, injiziert Pfade/Größe
      - Startet FIO via core/fio_runner.FioRunner
      - Safety: Pfadvalidierung, Speicherprüfung, eigener Test-Ordner (utils.security)
      - Abwärtskompatibel: Legacy-Test-IDs → neue IDs (Mapping)
    - list_disks.py
      - Ermittelt Volumes via utils.system_info.get_disk_info() (system_profiler; Fallback df)
      - Filtert auf gemountete, geeignete Volumes; reichert Info an (Größe, frei, FS, Typ)
    - validate.py
      - System-/Toolchecks (diskutil, system_profiler, df, vm_stat, sysctl) und FIO-Verfügbarkeit (Homebrew-Pfade)

  - diskbench/core/
    - qlab_patterns.py
      - TestId-Enum (quick_max_mix, prores_422_real, prores_422_hq_real, thermal_maximum)
      - Templates der FIO-Jobs als Strings (mit ${TEST_FILE}, ${TEST_SIZE})
      - Anzeige-Reihenfolge und Display-Labels (Test 1/3/4/2)
      - get_test_config injiziert Pfade/Größe in Templates und liefert lauffähige FIO-Config zurück
    - fio_runner.py (FIO Execution + Parsing)
      - Sucht FIO-Binary (bevorzugt no-SHM/noshm, sonst Homebrew, sonst PATH)
      - Ausführung mit sauberer env; schreibt FIO-JSON in tmp-Datei; säubert/parsed JSON robust
      - Summary-Bildung mit Fallbacks über FIO-Versionen:
        - Bandbreite: bevorzugt bw (KiB/s), fällt auf bw_bytes/1024 zurück
        - IOPS: bevorzugt iops, fällt auf iops_mean zurück
        - Latenzen: ns → ms gemittelt über Jobs
      - Automatisches Cleanup des Testverzeichnisses

  - diskbench/utils/
    - security.py: Pfad-/Datei-Validierung, sichere Testverzeichnisse, Filter gefährlicher FIO-Parameter
    - system_info.py: System-/Disk-Infos (system_profiler; Fallback df -h), Memory/CPU-Daten, Admin-Check
    - logging.py: einheitliche Logger-Konfiguration

  - tests/
    - test_fio_parser.py: Umfassende Tests der Parser-Fallbacklogik (bw vs. bw_bytes, iops vs. iops_mean, Latenzen, Aggregation, Edge-Cases)
    - test_test_ids.py: Backward-Compatibility für TestId-Aliases


3) Repository-konventionen (aus 00_infos/llm-context.md)

- Phase: MVP-Phase (pragmatisch, einfach halten); Architektur ist gesetzt
- Python Standard Library bevorzugt; neue Packages sparsam und nur bei Bedarf (Rückfrage)
- Venv pro Repo; Deutsch in Doku, Datumsformat AT (z. B. 24.8.2025)
- HOLDS beachten (z. B. DMG-Packaging, Code-Signing, Auto-Update): nicht umsetzen
- Versionierung: Dateien mit Versionszeile versehen; bei Änderungen Version erhöhen und alte Versionen in 99_archiv/old_versions/ ablegen
- Struktur respektieren (nummerierte Ordner). Keine Struktur-Expansion ohne Freigabe
- Nach Code-Änderungen: Bridge Server neu starten (Restart-Rule)

Ende.

