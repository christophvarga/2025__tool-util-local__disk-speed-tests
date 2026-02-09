# Test Report

Datum: 2026-02-09 08:44
Suite: pytest (Python 3.12.2)
Ergebnis: 126 passed, 0 failed, 1 skipped (4 warnings)
Dauer: 3.15s
Coverage: 31.04% (Gesamtprojekt)

Artefakte:
- JUnit: 89_output/test_reports/20260209-0844/junit-py.xml
- Coverage (XML): 89_output/test_reports/20260209-0844/coverage-py.xml
- Latest-Symlink: 89_output/test_reports/latest -> 20260209-0844

Notizen:
- 25 neue Security-Tests in test_bridge_security.py (C-1 bis C-5, H-5).
- Coverage-Rueckgang (35% -> 31%) durch neuen Code in server.py ohne HTTP-Level-Testabdeckung.
- 1 Skipped: integration/test_full_workflow_skeleton.py (Skeleton-Placeholder).
- 4 Warnings: PytestCollectionWarning (TestId Enum), 3x DeprecationWarning (quick_max_speed).

## Historie

| Datum | Tests | Passed | Failed | Skipped | Coverage |
|-------|-------|--------|--------|---------|----------|
| 2026-02-09 | 127 | 126 | 0 | 1 | 31.04% |
| 2026-01-31 | 102 | 101 | 0 | 1 | 35.62% |
| 2025-09-05 | 56 | 55 | 0 | 1 | 18.09% |

