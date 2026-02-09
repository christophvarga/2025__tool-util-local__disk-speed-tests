# Consolidated Legacy TODOs (Archived)

> Archived: 2026-02-09
> Source: 7 separate TODO files from repo root (all related to test-ID refactoring)
> Status: NEVER EXECUTED -- planning documents only

---

## Overview

All TODO files documented a planned refactoring to standardize test-ID strings
across the codebase. The refactoring was never started. The current test-ID
strings (`quick_max_speed`, `qlab_prores_422_show`, `qlab_prores_hq_show`,
`max_sustained`) remain in use and are functional.

## Impacted Files (from TODO_MASTER_REFACTOR_PLAN.md)

| File | Risk Level | Occurrences |
|------|------------|-------------|
| `diskbench/core/qlab_patterns.py` | CRITICAL | 16 lines |
| `bridge-server/server.py` | CRITICAL | 27 lines |
| `web-gui/app.js` | HIGH | 9 lines |
| `diskbench/main.py` | MEDIUM-HIGH | 5 lines |
| `web-gui/index.html` | MEDIUM | 8 lines |

## Key Planned Tasks (never started)

1. **Extract test IDs as constants/enum** (reduce hardcoded strings)
2. **Update test type mapping dictionaries** in bridge server
3. **Update radio button values** in web GUI
4. **Update CLI argument choices** in main.py
5. **Add backwards compatibility layer** during transition
6. **Migrate persistent state files** that use old IDs as keys

## Original Files Archived

- `TODO_app_js.md` -- Web GUI JavaScript refactoring plan
- `TODO_bridge_server.md` -- Bridge server refactoring plan
- `TODO_main.md` -- CLI main.py refactoring plan
- `TODO_MASTER_REFACTOR_PLAN.md` -- Master plan (9-14 day estimate)
- `TODO_memory_bank.md` -- Memory bank docs refactoring plan
- `TODO_qlab_patterns.md` -- Core patterns refactoring plan
- `TODO_web-gui_index.md` -- Web GUI HTML refactoring plan

## Decision

If this refactoring is still desired, create a new task from this summary.
The original detailed line-by-line plans are no longer accurate since the
codebase has evolved since these files were written.
