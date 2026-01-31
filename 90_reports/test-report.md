# Test Report

Datum: 2026-01-31 23:19
Suite: pytest (Python 3.13.11)
Ergebnis: 101 passed, 0 failed, 1 skipped (4 warnings)
Dauer: 3.40s
Coverage: 35.62% (Gesamtprojekt)

Artefakte:
- JUnit: 89_output/test_reports/20260131-2319/junit-py.xml
- Coverage (XML): 89_output/test_reports/20260131-2319/coverage-py.xml
- Latest-Symlink: 89_output/test_reports/latest -> 20260131-2319

Notizen:
- 87_tests/ als Symlink auf tests/ angelegt (kanonische Struktur).
- psutil und pytest-cov nachinstalliert (fehlten in .venv).
- 1 Skipped: integration/test_full_workflow_skeleton.py (Skeleton-Placeholder).
- 4 Warnings: PytestCollectionWarning (TestId Enum), 3x DeprecationWarning (quick_max_speed).

## Historie

| Datum | Tests | Passed | Failed | Skipped | Coverage |
|-------|-------|--------|--------|---------|----------|
| 2026-01-31 | 102 | 101 | 0 | 1 | 35.62% |
| 2025-09-05 | 56 | 55 | 0 | 1 | 18.09% |

