# Coverage Report

Datum: 2026-02-09 08:44
Gesamt-Stmts: 4066
Covered: 1262
Coverage (Line-Rate): 31.04%
Delta: -4.58% (gegenueber 35.62% am 2026-01-31)

Artefakt: 89_output/test_reports/20260209-0844/coverage-py.xml

Hinweis: Coverage-Rueckgang durch neue Validierungslogik in server.py (60+ LOC)
die nur ueber unit-mocks, nicht via HTTP-Integration getestet wird.

## Top-Module nach Coverage

| Modul | Stmts | Miss | Cover |
|-------|-------|------|-------|
| diskbench/core/monitoring.py | 132 | 10 | 92.42% |
| diskbench/core/exceptions.py | 41 | 4 | 90.24% |
| diskbench/core/retry_logic.py | 91 | 9 | 90.11% |
| diskbench/utils/security.py | 86 | 15 | 82.56% |
| diskbench/core/state_manager.py | 151 | 39 | 74.17% |
| diskbench/commands/test.py | 179 | 52 | 70.95% |
| diskbench/utils/system_info.py | 141 | 56 | 60.28% |

## Coverage-Luecken (kritisch)

| Modul | Cover | Empfehlung |
|-------|-------|------------|
| diskbench/main.py | 0.00% | Entry-Point, Smoke-Test empfohlen |
| diskbench/commands/setup.py | 0.00% | 451 Stmts ungetestet |
| diskbench/commands/list_disks.py | 0.00% | 135 Stmts ungetestet |
| diskbench/core/enhanced_fio_runner.py | 0.00% | 173 Stmts ungetestet |
| diskbench/commands/validate.py | 22.22% | Validation-Logik braucht Tests |
| diskbench/core/health_checks.py | 43.47% | Error-Paths ungetestet |

## Bewertung

Gesamt 35.62% -- Kategorie: **Niedrig** (< 60%, kritisch)
Getesteter Code (unit/): durchschnittlich ~75% -- akzeptabel.
Hauptproblem: Grosse Module ohne jegliche Tests (main.py, setup.py, list_disks.py).

