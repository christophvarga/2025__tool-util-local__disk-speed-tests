# Coverage Report

Datum: 2026-02-09 11:26
Gesamt-Stmts: 3786
Covered: 1278
Coverage (Line-Rate): 33.76%
Delta: +0.18% (gegenueber 33.58% nach All-Done)

Artefakt: 89_output/test_reports/20260209-1126/coverage-py.xml

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
| bridge-server/process_manager.py | 195 | 102 | 47.69% |

## Coverage-Luecken (kritisch)

| Modul | Cover | Empfehlung |
|-------|-------|------------|
| diskbench/main.py | 0.00% | Entry-Point, Smoke-Test empfohlen |
| diskbench/commands/setup.py | 0.00% | 451 Stmts ungetestet |
| diskbench/commands/list_disks.py | 0.00% | 135 Stmts ungetestet |
| diskbench/core/enhanced_fio_runner.py | 0.00% | 173 Stmts ungetestet |
| bridge-server/fio_setup.py | 4.85% | 165 Stmts, FIO-Kompilierung |
| bridge-server/fio_utils.py | 28.42% | 183 Stmts, FIO-Tests |
| diskbench/commands/validate.py | 22.22% | Validation-Logik braucht Tests |

## Bewertung

Gesamt 33.76% -- Kategorie: **Niedrig** (< 60%)
Getesteter Code (unit/): durchschnittlich ~75% -- akzeptabel.
Hauptproblem: Grosse Module ohne Tests (main.py, setup.py, list_disks.py, fio_setup.py).
Frontend (web-gui/): 0% Coverage (kein Test-Framework, HOLD-010).

