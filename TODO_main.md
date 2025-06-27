# TODO: Refactor Main CLI - main.py

## File: diskbench/main.py

### Current test-id strings found:
- `quick_max_speed` (line 81)

### Refactoring tasks:

#### 1. High Priority - CLI Argument Choices (line 81)
- [ ] Update the `--test` argument choices in `create_parser()` function
- [ ] Current choices list includes: `'quick_max_speed', 'qlab_prores_422_show', 'qlab_prores_hq_show', 'max_sustained'`
- [ ] Replace with new standardized test identifiers
- [ ] Ensure backwards compatibility if needed

#### 2. Medium Priority - Help Documentation
- [ ] Update help text and examples in argument parser
- [ ] Review epilog examples (lines 66-72) for consistency with new test IDs
- [ ] Update any inline documentation

#### 3. Low Priority - Validation & Error Messages
- [ ] Check if any error messages reference specific test types by name
- [ ] Update validation logic that may depend on specific test ID formats
- [ ] Ensure test type validation still works correctly

### Dependencies to check:
- TestCommand class likely expects these exact test ID strings
- CLI help documentation may need updates
- Any shell scripts or automation that calls this CLI

### Testing requirements:
- [ ] Verify CLI accepts new test ID arguments
- [ ] Test help output displays correctly
- [ ] Confirm backwards compatibility approach if maintaining old IDs
- [ ] Test error handling for invalid test types

### Risk Assessment: MEDIUM-HIGH
This is the main CLI entry point - changes affect all command-line usage and scripts.
