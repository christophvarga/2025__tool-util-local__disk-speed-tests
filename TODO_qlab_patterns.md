# TODO: Refactor QLab Test Patterns - qlab_patterns.py

## File: diskbench/core/qlab_patterns.py

### Current test-id strings found:
- `quick_max_speed` (lines 20, 105, 106, 149, 501)
- `qlab_prores_422_show` (lines 26, 107, 108, 337)
- `qlab_prores_hq_show` (lines 32, 109, 110)
- `max_sustained` (lines 38, 111, 112, 614)

### Refactoring tasks:

#### 1. High Priority - Core Pattern Dictionary (lines 19-44)
- [ ] Refactor the `_initialize_patterns()` method to use standardized test identifiers
- [ ] Consider extracting test IDs as constants/enum
- [ ] Update test pattern keys from hardcoded strings to centralized constants

#### 2. Medium Priority - Analysis Methods (lines 105-112)
- [ ] Update conditional logic in `analyze_results()` method
- [ ] Replace hardcoded string comparisons with constant references
- [ ] Ensure test type matching is consistent across all methods

#### 3. Medium Priority - Test Configuration Methods
- [ ] Review `_get_quick_max_speed_config()` method naming and usage
- [ ] Update internal FIO template method calls if needed
- [ ] Verify test configuration consistency

#### 4. Low Priority - Individual Analysis Methods (lines 501-655)
- [ ] Update method names if test IDs change:
  - `_analyze_quick_max_speed()` (line 501)
  - `_analyze_prores_422_show()` (line 534) 
  - `_analyze_prores_hq_show()` (line 574)
  - `_analyze_max_sustained()` (line 614)

#### 5. Documentation & Comments
- [ ] Update method docstrings with new test identifiers
- [ ] Update comments referencing old test names
- [ ] Ensure consistent naming throughout file

### Dependencies to check:
- Test configuration templates may reference these IDs
- External callers may depend on current test ID strings
- Database/storage systems may use these as keys

### Risk Assessment: HIGH
This is the core configuration file - changes here affect entire test framework.
