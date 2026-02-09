# Test Report

Datum: 2026-02-09 11:26
Suite: pytest (Python 3.12.2)
Ergebnis: 137 passed, 0 failed, 1 skipped (4 warnings)
Dauer: 14.44s
Coverage: 33.76% (Gesamtprojekt)

Artefakte:
- JUnit: 89_output/test_reports/20260209-1126/junit-py.xml
- Coverage (XML): 89_output/test_reports/20260209-1126/coverage-py.xml
- Latest-Symlink: 89_output/test_reports/latest -> 20260209-1126

Notizen:
- Alle Findings aus Code-Analyse abgearbeitet (C-1 bis C-5, H-1 bis H-6, LF-1 bis LF-3)
- MF-3 abgeschlossen: app.js (2749 LOC) in 9 Module aufgeteilt (je <=300 LOC)
- process_manager.py unter 300 LOC gebracht (334->274 LOC)
- fio_utils.py bereinigt: unbenutzte get_optimal_fio_path entfernt, DRY log_cb (317->293 LOC)
- llm-context.md aktualisiert auf v1.3
- 1 Skipped: integration/test_full_workflow_skeleton.py (Skeleton-Placeholder)

## Historie

| Datum | Tests | Passed | Failed | Skipped | Coverage |
|-------|-------|--------|--------|---------|----------|
| 2026-02-09 (modular) | 138 | 137 | 0 | 1 | 33.76% |
| 2026-02-09 (all-done) | 138 | 137 | 0 | 1 | 33.58% |
| 2026-02-09 (security) | 127 | 126 | 0 | 1 | 31.04% |
| 2026-01-31 | 102 | 101 | 0 | 1 | 35.62% |
| 2025-09-05 | 56 | 55 | 0 | 1 | 18.09% |

