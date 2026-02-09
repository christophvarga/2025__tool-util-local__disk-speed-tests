# Test Report

Datum: 2026-02-09 10:09
Suite: pytest (Python 3.12.2)
Ergebnis: 126 passed, 0 failed, 1 skipped (4 warnings)
Dauer: 2.99s
Coverage: 32.28% (Gesamtprojekt)

Artefakte:
- JUnit: 89_output/test_reports/20260209-1009/junit-py.xml
- Coverage (XML): 89_output/test_reports/20260209-1009/coverage-py.xml
- Latest-Symlink: 89_output/test_reports/latest -> 20260209-1009

Notizen:
- Cleanup: qlab-disk-tester/ und memory-bank/ Legacy-Verzeichnisse entfernt
- Cleanup: 7 TODO_*.md vom Root konsolidiert nach 99_archiv/TODO_consolidated_legacy.md
- Fix: state_file Pfade von memory-bank/ auf .state/ migriert (bridge_core.py, state_manager.py)
- Alle 126 Tests gruen nach allen Aenderungen.
- 1 Skipped: integration/test_full_workflow_skeleton.py (Skeleton-Placeholder).

## Historie

| Datum | Tests | Passed | Failed | Skipped | Coverage |
|-------|-------|--------|--------|---------|----------|
| 2026-02-09 (cleanup) | 127 | 126 | 0 | 1 | 32.28% |
| 2026-02-09 (final) | 127 | 126 | 0 | 1 | 32.28% |
| 2026-02-09 (security) | 127 | 126 | 0 | 1 | 31.04% |
| 2026-01-31 | 102 | 101 | 0 | 1 | 35.62% |
| 2025-09-05 | 56 | 55 | 0 | 1 | 18.09% |

