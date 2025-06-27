# TODO: Refactor Web GUI - index.html

## File: web-gui/index.html

### Current test-id strings found:
- `quick_max_speed` (lines 194, 197)
- `qlab_prores_422_show` (lines 205, 208)  
- `qlab_prores_hq_show` (lines 217, 220)
- `max_sustained` (lines 228, 231)

### Refactoring tasks:

#### 1. High Priority - Test Selection Radio Buttons (lines 194-236)
- [ ] Update radio button values in test type selection section
- [ ] Update `value` attributes for input elements:
  - Line 194: `value="quick_max_speed"`
  - Line 205: `value="qlab_prores_422_show"`
  - Line 217: `value="qlab_prores_hq_show"` 
  - Line 228: `value="max_sustained"`

#### 2. Medium Priority - Info Function Calls (lines 197, 208, 220, 231)
- [ ] Update `showPatternInfo()` function calls with new test IDs:
  - Line 197: `onclick="showPatternInfo('quick_max_speed')"`
  - Line 208: `onclick="showPatternInfo('qlab_prores_422_show')"`
  - Line 220: `onclick="showPatternInfo('qlab_prores_hq_show')"`
  - Line 231: `onclick="showPatternInfo('max_sustained')"`

#### 3. Medium Priority - Default Selection
- [ ] Verify default checked radio button (line 205) uses correct new test ID
- [ ] Update any JavaScript that initializes selectedTestType with default value

#### 4. Low Priority - User-Facing Labels
- [ ] Review test card titles and descriptions for consistency
- [ ] Ensure test names match new identifier conventions
- [ ] Update any tooltip or help text

### Dependencies to check:
- JavaScript app.js file likely references these test IDs
- Modal content for pattern info may use these IDs as keys
- CSS classes may be derived from test IDs

### Testing requirements:
- [ ] Verify radio button selection works with new IDs
- [ ] Test pattern info modal displays correctly
- [ ] Confirm form submission sends correct test type values

### Risk Assessment: MEDIUM
UI changes are visible to users but contained within this interface layer.
