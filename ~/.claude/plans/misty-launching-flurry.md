# Tiefgehende Code-Analyse: QLab Disk Performance Tester

## Context

Das Projekt ist ein 3-Tier Disk-Performance-Testing-Tool (Web-GUI -> Python Bridge-Server -> FIO CLI) im MVP/Alpha-Status. Die Analyse deckt schwerwiegende Sicherheitsluecken auf: Existierende Validierungsfunktionen in `security.py` werden im Bridge-Server nicht aufgerufen, das Frontend nutzt `innerHTML` mit Backend-Daten (XSS), und die Frontend-Backend-Kommunikation hat weder Timeouts noch Retry-Logik. Strukturell gibt es Legacy-Duplikate und ueberdimensionierte Dateien (server.py: 2674 LOC, app.js: 2544 LOC).

---

## CRITICAL Findings

### C-1: disk_path nicht validiert (Path Traversal)
- **`bridge-server/server.py:558`** — `test_params.get('disk_path', '/tmp')` wird direkt an CLI uebergeben
- `validate_disk_path()` existiert in `diskbench/utils/security.py:13-49`, wird aber **nie importiert/aufgerufen** im Bridge-Server
- **Risiko:** Beliebige Pfade als FIO-Testziel, inkl. System-Verzeichnisse

### C-2: Custom FIO Config Injection
- **`bridge-server/server.py:621-683`** — `_generate_custom_fio_config()` schreibt Parameter unvalidiert in INI-Config
- `block_size` (Z.627), `target_rate` (Z.631) werden direkt interpoliert: `bs={block_size}`
- **Risiko:** Newline-Injection in INI-Format kann FIO-Verhalten manipulieren
- Numerische Params `duration`, `numjobs`, `iodepth` ohne Range-Checks → DoS moeglich

### C-3: Vorhersagbare /tmp Pfade (TOCTOU)
- **`server.py:564`** — `/tmp/diskbench-{test_id}.json` mit test_id = `test_{int(time.time())}`
- **`server.py:673`** — `/tmp/custom_test_{timestamp}.fio`
- **Fix:** `tempfile.mkstemp()` oder `tempfile.NamedTemporaryFile()`

### C-4: XSS via innerHTML mit Backend-Daten
- **`web-gui/app.js`** — 35+ Stellen mit `innerHTML` und unescapten Backend-Daten
- Disk-Namen, Error-Messages, Testergebnisse werden direkt ins DOM injiziert
- **Fix:** `textContent` fuer User-/Backend-Daten, oder DOMPurify

### C-5: CORS Wildcard
- **`server.py:2327`** — `Access-Control-Allow-Origin: *`
- Jede Website kann Requests an den Bridge-Server senden
- **Fix:** Auf `http://localhost:*` einschraenken

---

## HIGH Findings

### H-1: Keine fetch() Timeouts / Retry-Logik
- **`app.js:2000-2036`** — `callBridgeAPI()` ohne `AbortController`, kein Retry, kein Backoff
- Server-Crash → endloses Haengen

### H-2: Hardcoded Server-URL
- **`app.js:2001`** — `const baseUrl = 'http://localhost:8765'` nicht konfigurierbar

### H-3: Process-Cleanup via ps aux String-Matching
- **`server.py:685-745`** — fragiles Pattern-Matching statt PID-File oder psutil

### H-4: check_available_space() nie aufgerufen
- Existiert in `diskbench/utils/security.py:203-229`, wird im Bridge-Server ignoriert
- `size_gb` aus HTTP POST unkontrolliert → Disk-Fuellattacke

### H-5: Exception-Messages leaken System-Pfade
- **`server.py:618, 2493`** — `str(e)` direkt an Client gesendet

### H-6: Endloses Polling ohne Circuit Breaker
- **`app.js`** — Status-Polling alle 2s ohne Max-Retry oder Recovery-Mechanismus

---

## MEDIUM Findings

### M-1: Race Condition UI vs Backend State
- `isTestRunning` wird client-seitig sofort gesetzt, Server-Response kann abweichen

### M-2: API Response Schema nicht validiert
- Frontend nimmt Felder wie `success`, `test_id`, `progress` als gegeben an

### M-3: Fehlende Loading-States
- Kein Spinner, keine Button-Deaktivierung waehrend API-Calls

---

## Strukturelle Probleme

### S-1: Legacy-Duplikation
- `/commands/` und `/core/` auf Root-Level sind Compatibility-Shims auf `diskbench.*`
- Koennen entfernt werden nach Import-Migration

### S-2: Ueberdimensionierte Dateien
| Datei | LOC | Regel |
|-------|-----|-------|
| `bridge-server/server.py` | 2674 | <300 |
| `web-gui/app.js` | 2544 | <300 |

### S-3: Legacy-Artefakte
- `qlab-disk-tester/` mit eigener venv (keine Referenz aus produktivem Code)
- 7 TODO_*.md Dateien auf Root-Level
- `memory-bank/` Verzeichnis (Legacy)

---

## Test-Coverage Gaps

| Bereich | Tests | Risiko |
|---------|-------|--------|
| Frontend (app.js, 2544 LOC) | **0** | CRITICAL |
| Bridge-Server Input-Validierung | Nicht getestet (wird nicht aufgerufen) | CRITICAL |
| Custom Config Injection | Kein Test | CRITICAL |
| Integration End-to-End | 1 Skip-markierter Skeleton | HIGH |
| Concurrent Requests | Kein Test | HIGH |
| Error Recovery | Kein Test | HIGH |

---

## Priorisierte Empfehlungen

### Quick Wins (je 15min-1h)

| # | Massnahme | Datei | Zeilen |
|---|-----------|-------|--------|
| QW-1 | `validate_disk_path()` im Bridge-Server aufrufen | `server.py` | 484-560 |
| QW-2 | Range-Checks: duration<=43200, numjobs<=16, iodepth<=256 | `server.py` | 626-631 |
| QW-3 | block_size Whitelist: `^\d+[kKmMgG]$` | `server.py` | 627 |
| QW-4 | `tempfile.mkstemp()` statt `/tmp/` Pfade | `server.py` | 564, 673 |
| QW-5 | Exception-Sanitizing (keine Pfade an Client) | `server.py` | 618, 2493 |
| QW-6 | CORS auf localhost einschraenken | `server.py` | 2327 |
| QW-7 | `AbortController` + 30s Timeout in `callBridgeAPI()` | `app.js` | 2019 |

### Mittelfristig (1-2 Wochen)

| # | Massnahme | Impact |
|---|-----------|--------|
| MF-1 | innerHTML → textContent/DOM-API (35+ Stellen) | XSS-Eliminierung |
| MF-2 | server.py aufteilen: handlers, bridge, process_mgr, config | <300 LOC |
| MF-3 | app.js modularisieren (ES Modules) | Testbarkeit |
| MF-4 | Process-Cleanup auf PID-File basieren | Zuverlaessigkeit |
| MF-5 | Retry-Logik + Circuit Breaker fuer Polling | Stabilitaet |
| MF-6 | Integration-Tests implementieren | Regressions-Schutz |

### Langfristig (Cleanup)

| # | Massnahme |
|---|-----------|
| LF-1 | Root-Level `/commands/` + `/core/` Shims entfernen |
| LF-2 | `qlab-disk-tester/` Verzeichnis entfernen |
| LF-3 | TODO-Dateien konsolidieren oder entfernen |
| LF-4 | Frontend-Test-Suite einfuehren |

---

## Kritische Dateien

- `bridge-server/server.py` — Alle Backend-Security-Issues (C-1 bis C-3, H-3 bis H-5)
- `web-gui/app.js` — XSS, fehlende Timeouts, Hardcoded URL (C-4, H-1, H-2, H-6)
- `diskbench/utils/security.py` — Existierende Validierung die integriert werden muss
- `tests/unit/test_security_utils.py` — Pattern fuer neue Validierungs-Tests

## Verifikation

1. `pytest tests/ -v` — bestehende Tests muessen gruen bleiben
2. Manuell: Test starten mit manipuliertem disk_path → muss abgelehnt werden
3. Manuell: Custom Test mit block_size="1M\nfilename=/etc/passwd" → muss validiert werden
4. Browser DevTools: innerHTML-Stellen pruefen mit `<img onerror=alert(1)>` als Disk-Name
