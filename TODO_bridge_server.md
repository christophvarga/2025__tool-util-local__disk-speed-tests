# TODO: Refactor Bridge Server - server.py

## File: bridge-server/server.py

### Current test-id strings found:
- `quick_max_speed` (lines 437, 445, 469, 952, 954, 1417)
- `qlab_prores_422_show` (lines 438, 471, 952, 1425)
- `qlab_prores_hq_show` (lines 439, 473, 952, 1433)
- `max_sustained` (lines 440, 475, 955, 927)

### Refactoring tasks:

#### 1. High Priority - Test Type Mapping Dictionary (lines 436-446)
- [ ] Update `test_type_mapping` in `start_test()` method
- [ ] Current mapping maps web GUI names to diskbench test names:
  ```python
  test_type_mapping = {
      'quick_max_speed': 'quick_max_speed',
      'qlab_prores_422_show': 'qlab_prores_422_show', 
      'qlab_prores_hq_show': 'qlab_prores_hq_show',
      'max_sustained': 'max_sustained'
  }
  ```
- [ ] Replace keys and/or values with new standardized identifiers

#### 2. High Priority - Duration Mapping Logic (lines 469-478)
- [ ] Update estimated duration calculation conditionals:
  - Line 469: `if diskbench_test_type == 'quick_max_speed':`
  - Line 471: `elif diskbench_test_type == 'qlab_prores_422_show':`
  - Line 473: `elif diskbench_test_type == 'qlab_prores_hq_show':`
  - Line 475: `elif diskbench_test_type == 'max_sustained':`

#### 3. High Priority - Test Status Analysis (lines 864-873)
- [ ] Update enhanced progress calculation in `get_test_status()`:
  - Line 864: `if test_type == 'qlab_prores_422_show':`
  - Line 866: `elif test_type == 'qlab_prores_hq_show':`
  - Line 868: `elif test_type == 'max_sustained':`
  - Line 870: `elif test_type == 'quick_max_speed':`

#### 4. High Priority - Live Metrics Generation (lines 896-946)
- [ ] Update `_get_live_test_metrics()` method conditionals:
  - Line 896: `if test_type == 'quick_max_speed':`
  - Line 906: `elif 'show' in test_type:`
  - Line 927: `elif test_type == 'max_sustained':`

#### 5. High Priority - QLab Performance Analysis (lines 950-975)
- [ ] Update `qlab_requirements` dictionary in `_get_qlab_performance_analysis()`:
  ```python
  qlab_requirements = {
      'qlab_prores_422_show': {'min_throughput': 220, 'name': 'ProRes 422'},
      'qlab_prores_hq_show': {'min_throughput': 440, 'name': 'ProRes HQ'},
      'quick_max_speed': {'min_throughput': 100, 'name': 'Basic'},
      'max_sustained': {'min_throughput': 300, 'name': 'Sustained'}
  }
  ```

#### 6. Medium Priority - QLab Test Implementation (lines 1410-1456)
- [ ] Update direct QLab test patterns in `run_qlab_test_direct()`:
  - Line 1417: `if test_type == 'quick_max_speed':`
  - Line 1425: `elif test_type == 'qlab_prores_422_show':`
  - Line 1433: `elif test_type == 'qlab_prores_hq_show':`

#### 7. Low Priority - Comments & Documentation
- [ ] Update any comments referencing specific test names
- [ ] Review log messages for consistency with new test IDs
- [ ] Update error messages that may reference test types

### Dependencies to check:
- Diskbench CLI must accept the same test type strings
- Persistent state storage uses these test IDs as keys
- Web GUI sends these exact test type strings via API
- Log files and error messages reference these names

### Testing requirements:
- [ ] Verify test start API accepts new test type parameters
- [ ] Test duration calculations work correctly for all types
- [ ] Confirm live progress updates use correct test type logic
- [ ] Check persistent state save/restore with new IDs
- [ ] Verify QLab-specific analysis works with new types

### Risk Assessment: CRITICAL
This is the core bridge between GUI and CLI - changes affect entire test execution pipeline and API compatibility.
