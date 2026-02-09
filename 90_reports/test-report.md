# Test Report

Datum: 2026-02-09 09:59
Suite: pytest (Python 3.12.2)
Ergebnis: 126 passed, 0 failed, 1 skipped (4 warnings)
Dauer: 2.90s
Coverage: ~31% (Gesamtprojekt)

Artefakte:
- JUnit: 89_output/test_reports/20260209-0959/junit-py.xml
- Coverage (XML): 89_output/test_reports/20260209-0959/coverage-py.xml
- Latest-Symlink: 89_output/test_reports/latest -> 20260209-0959

Notizen:
- Refactoring: server.py (2773 LOC) aufgeteilt in 9 Module (je <=300 LOC).
- Alle 126 Tests unveraendert und gruen nach Refactoring.
- 1 Skipped: integration/test_full_workflow_skeleton.py (Skeleton-Placeholder).
- 4 Warnings: PytestCollectionWarning (TestId Enum), 3x DeprecationWarning (quick_max_speed).

## Historie

| Datum | Tests | Passed | Failed | Skipped | Coverage |
|-------|-------|--------|--------|---------|----------|
| 2026-02-09 (refactor) | 127 | 126 | 0 | 1 | ~31% |
| 2026-02-09 | 127 | 126 | 0 | 1 | 31.04% |
| 2026-01-31 | 102 | 101 | 0 | 1 | 35.62% |
| 2025-09-05 | 56 | 55 | 0 | 1 | 18.09% |

