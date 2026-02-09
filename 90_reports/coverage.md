# Coverage Report

Datum: 2026-02-09 10:13
Gesamt-Stmts: 3800
Covered: 1276
Coverage (Line-Rate): 33.58%
Delta: +2.54% (gegenueber 31.04% nach Security-Hardening)

Artefakt: 89_output/test_reports/20260209-1013/coverage-py.xml

## Top-Module nach Coverage

| Modul | Stmts | Miss | Cover |
|-------|-------|------|-------|
| bridge-server/validation.py | 37 | 2 | 94.59% |
| diskbench/core/monitoring.py | 132 | 10 | 92.42% |
| diskbench/core/exceptions.py | 41 | 4 | 90.24% |
| diskbench/core/retry_logic.py | 91 | 9 | 90.11% |
| diskbench/utils/security.py | 86 | 15 | 82.56% |
| diskbench/core/state_manager.py | 151 | 39 | 74.17% |
| diskbench/commands/test.py | 179 | 52 | 70.95% |
| diskbench/utils/system_info.py | 141 | 56 | 60.28% |
| bridge-server/process_manager.py | 239 | 109 | 54.39% |

## Coverage-Luecken (kritisch)

| Modul | Cover | Empfehlung |
|-------|-------|------------|
| diskbench/main.py | 0.00% | Entry-Point, Smoke-Test empfohlen |
| diskbench/commands/setup.py | 0.00% | 451 Stmts ungetestet |
| diskbench/commands/list_disks.py | 0.00% | 135 Stmts ungetestet |
| diskbench/core/enhanced_fio_runner.py | 0.00% | 173 Stmts ungetestet |
| bridge-server/fio_setup.py | 4.85% | 165 Stmts, FIO-Kompilierung |
| bridge-server/fio_utils.py | 8.50% | 153 Stmts, FIO-Tests |
| diskbench/commands/validate.py | 22.22% | Validation-Logik braucht Tests |

## Bewertung

Gesamt 33.58% -- Kategorie: **Niedrig** (< 60%)
Getesteter Code (unit/): durchschnittlich ~75% -- akzeptabel.
Verbesserung: +36 neue Tests in dieser Session (Security + Process-Cleanup).
Hauptproblem: Grosse Module ohne Tests (main.py, setup.py, list_disks.py, fio_setup.py).

