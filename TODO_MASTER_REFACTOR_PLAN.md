# MASTER REFACTOR PLAN: QLab Test-ID Strings

## Overview
Comprehensive refactoring plan for standardizing test-id strings across the QLab Disk Performance Tester codebase.

## Current Test-ID Strings Found
- `quick_max_speed` - Found in 6 files, 16+ locations
- `qlab_prores_422_show` - Found in 6 files, 15+ locations  
- `qlab_prores_hq_show` - Found in 5 files, 12+ locations
- `max_sustained` - Found in 5 files, 10+ locations

## Impacted Files Summary

| File | Risk Level | Occurrences | Components Affected |
|------|------------|-------------|-------------------|
| `diskbench/core/qlab_patterns.py` | **CRITICAL** | 16 lines | Core test configuration, analysis methods |
| `bridge-server/server.py` | **CRITICAL** | 27 lines | API bridge, test execution pipeline |
| `web-gui/app.js` | **HIGH** | 9 lines | Frontend logic, test selection, analysis |
| `diskbench/main.py` | **MEDIUM-HIGH** | 5 lines | CLI argument parser, help text |
| `web-gui/index.html` | **MEDIUM** | 8 lines | UI test selection, pattern info |
| `memory-bank/*.md` | **LOW** | 4 lines | Documentation context files |

## Refactoring Strategy

### Phase 1: Planning & Design
- [ ] **Define new standardized test-id naming convention**
- [ ] **Create constants/enum for test identifiers**
- [ ] **Plan backwards compatibility approach**
- [ ] **Design migration strategy for persistent data**

### Phase 2: Core Infrastructure (CRITICAL)
#### 2.1 diskbench/core/qlab_patterns.py
- [ ] Extract test IDs as constants/enum
- [ ] Update `_initialize_patterns()` method
- [ ] Refactor analysis method conditionals  
- [ ] Update method names if needed

#### 2.2 bridge-server/server.py  
- [ ] Update test type mapping dictionary
- [ ] Refactor duration calculation logic
- [ ] Update test status analysis conditionals
- [ ] Fix live metrics generation
- [ ] Update QLab performance analysis

### Phase 3: User Interfaces (HIGH)
#### 3.1 web-gui/app.js
- [ ] Update default selectedTestType
- [ ] Fix test analysis switch logic
- [ ] Update test display names mapping
- [ ] Review progress & status updates

#### 3.2 web-gui/index.html
- [ ] Update radio button values
- [ ] Fix pattern info function calls
- [ ] Verify default selection

### Phase 4: CLI & Documentation (MEDIUM)
#### 4.1 diskbench/main.py
- [ ] Update CLI argument choices
- [ ] Fix help documentation
- [ ] Update examples

#### 4.2 memory-bank/*.md
- [ ] Update context documentation
- [ ] Fix code examples

## Testing Strategy

### Unit Tests Required
- [ ] Test configuration loading with new IDs
- [ ] CLI argument parsing validation
- [ ] API endpoint parameter handling
- [ ] Test type validation across all components

### Integration Tests Required  
- [ ] End-to-end test execution flow
- [ ] GUI → Bridge → CLI communication
- [ ] Test result analysis pipeline
- [ ] Persistent state save/restore

### User Acceptance Tests
- [ ] All test types can be selected and executed
- [ ] Results display correctly for each test type
- [ ] Help documentation is accurate
- [ ] No broken UI elements or error messages

## Risk Mitigation

### High-Risk Changes
1. **API Compatibility**: Bridge server changes affect GUI communication
2. **CLI Compatibility**: Main.py changes affect automation scripts  
3. **Data Migration**: Persistent state may use old test IDs as keys

### Mitigation Strategies
- [ ] Implement backwards compatibility layer during transition
- [ ] Create test ID translation/mapping functions
- [ ] Maintain old test IDs alongside new ones temporarily
- [ ] Add migration logic for persistent state files

## Rollback Plan
- [ ] Keep original test-id constants available as aliases
- [ ] Implement feature flag to switch between old/new IDs
- [ ] Document rollback procedure for each component
- [ ] Test rollback scenario before deployment

## Dependencies & Coordination

### Internal Dependencies
- Core patterns → Bridge server → Web GUI
- CLI parser → Bridge server API
- Persistent state storage keys
- Test result analysis pipeline

### External Dependencies  
- User automation scripts using CLI
- Existing test result files/logs
- Documentation and training materials

## Timeline Estimate
- **Phase 1 (Planning)**: 1-2 days
- **Phase 2 (Core)**: 3-4 days  
- **Phase 3 (UI)**: 2-3 days
- **Phase 4 (CLI/Docs)**: 1-2 days
- **Testing & Validation**: 2-3 days
- **Total**: 9-14 days

## Success Criteria
- [ ] All test types work with new identifiers
- [ ] No functional regressions introduced
- [ ] Documentation updated and accurate
- [ ] Backwards compatibility maintained (if required)
- [ ] Clean, consistent codebase with no hardcoded old IDs
