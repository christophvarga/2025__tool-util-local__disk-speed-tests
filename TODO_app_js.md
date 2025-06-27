# TODO: Refactor Web GUI JavaScript - app.js

## File: web-gui/app.js

### Current test-id strings found:
- `quick_max_speed` (lines 11, 459, 1579)
- `qlab_prores_422_show` (lines 462, 1580)
- `qlab_prores_hq_show` (lines 465, 468, 1581)
- `max_sustained` (lines 468, 1582)

### Refactoring tasks:

#### 1. High Priority - Class Constructor Default (line 11)
- [ ] Update `selectedTestType` default value in DiskBenchApp constructor
- [ ] Current: `this.selectedTestType = 'qlab_prores_422_show';`
- [ ] Replace with new standardized test identifier

#### 2. High Priority - Test Analysis Switch Logic (lines 459-471)
- [ ] Update conditional statements in `showResults()` method:
  - Line 459: `if (testType === 'quick_max_speed')`
  - Line 462: `else if (testType === 'qlab_prores_422_show')`  
  - Line 465: `else if (testType === 'qlab_prores_hq_show')`
  - Line 468: `else if (testType === 'max_sustained')`

#### 3. High Priority - Test Display Names Map (lines 1578-1583)
- [ ] Update `getTestDisplayName()` function test mapping:
  - Line 1579: `'quick_max_speed': 'Quick Max Speed Test'`
  - Line 1580: `'qlab_prores_422_show': 'ProRes 422 Show Simulation'`
  - Line 1581: `'qlab_prores_hq_show': 'ProRes HQ Show Simulation'` 
  - Line 1582: `'max_sustained': 'Max Sustained Performance'`

#### 4. Medium Priority - Test-Specific Analysis Methods
- [ ] Review analysis method calls that may depend on test IDs
- [ ] Check if CSS classes or DOM IDs are derived from test types
- [ ] Verify any dynamic content generation using test IDs

#### 5. Medium Priority - Progress & Status Updates
- [ ] Check live metrics generation that references test types
- [ ] Review test phase detection logic
- [ ] Ensure progress calculation works with new test IDs

#### 6. Low Priority - Comments & Documentation
- [ ] Update any comments referencing specific test names
- [ ] Review method documentation for accuracy
- [ ] Check console.log statements for outdated test references

### Dependencies to check:
- Backend bridge server API expects these test type strings
- Test duration calculations may be hardcoded by test type
- CSS styling may use test-type-specific classes

### Testing requirements:
- [ ] Verify test selection updates selectedTestType correctly
- [ ] Test all analysis rendering paths with new IDs
- [ ] Confirm test display names appear correctly in UI
- [ ] Check progress tracking for all test types
- [ ] Verify background test detection works

### Risk Assessment: HIGH
This is the main application logic - changes affect all user interactions and test execution flow.
