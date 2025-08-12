# FIO Parser Tests

This directory contains comprehensive unit tests for the FIO JSON parsing functionality in diskbench.

## Overview

The FIO parser has been designed to handle multiple FIO versions and JSON schema changes gracefully. These tests ensure backwards and forwards compatibility across different FIO versions.

## Test Structure

### Test Files

- `test_fio_parser.py` - Main test suite for FIO JSON parsing
- `fixtures/` - Sample FIO JSON outputs for testing different versions

### Test Fixtures

#### `fio_3_40_output.json`
- Current FIO 3.40 format
- Contains both `bw` (KiB/s) and `bw_bytes` (bytes/s) fields
- Tests the preferred field selection logic

#### `fio_legacy_output.json` 
- Legacy FIO 3.15 format
- Contains only `bw_bytes` field (no `bw` field)
- Tests fallback logic for older versions

#### `fio_very_old_output.json`
- Very old FIO 2.21 format
- Minimal field set for edge case testing
- Tests parsing with limited data availability

## Key Test Cases

### 1. Field Preference Logic
- **Current format**: Prefers `bw` over `bw_bytes` when both are present
- **Legacy format**: Falls back to `bw_bytes / 1024` when `bw` is missing
- **IOPS fields**: Prefers `iops` over `iops_mean` when both are present

### 2. Version Compatibility
- Tests parsing across FIO versions 2.x, 3.15, and 3.40+
- Handles field name changes and schema evolution
- Maintains backwards compatibility

### 3. Error Handling
- Graceful handling of missing fields
- Empty jobs array handling
- Malformed job data recovery
- Zero/invalid value handling

### 4. Aggregation Logic
- Multiple job aggregation
- Correct bandwidth and IOPS summing
- Latency averaging
- Runtime maximum calculation

## Running the Tests

```bash
# Run all parser tests
python -m pytest tests/test_fio_parser.py -v

# Run specific test
python -m pytest tests/test_fio_parser.py::TestFioParser::test_parse_current_fio_format -v

# Run with coverage
python -m pytest tests/test_fio_parser.py --cov=diskbench.core.fio_runner
```

## Field Mapping Reference

### Bandwidth Fields
- **Current FIO 3.35+**: Uses `bw` (KiB/s) as primary field
- **Legacy FIO**: Uses `bw_bytes` (bytes/s), converted to KiB/s by dividing by 1024
- **Parser logic**: `bw` field takes precedence, falls back to `bw_bytes / 1024`

### IOPS Fields  
- **Standard**: Uses `iops` field
- **Fallback**: Uses `iops_mean` field for older versions
- **Parser logic**: `iops` field takes precedence over `iops_mean`

### Latency Fields
- **Current**: Uses `lat_ns.mean` (nanoseconds)
- **Conversion**: Divides by 1,000,000 to convert to milliseconds
- **Fallback**: Handles missing latency data gracefully

## Schema Evolution Handling

The parser implements a robust fallback strategy to handle FIO schema changes:

1. **Primary field check**: Try to use the preferred current field name
2. **Fallback field check**: Try alternative/legacy field names  
3. **Unit conversion**: Apply necessary unit conversions (bytes→KiB, ns→ms)
4. **Default values**: Use sensible defaults for missing data

This ensures that diskbench continues to work across FIO version upgrades and downgrades without breaking existing functionality.

## Adding New Tests

When adding new test cases:

1. Create fixture files in `fixtures/` directory for new FIO output formats
2. Add corresponding test methods in `test_fio_parser.py`
3. Verify both field parsing and aggregation logic
4. Test edge cases and error conditions
5. Update this README with new test coverage

## Test Coverage

Current test coverage includes:

- ✅ FIO 2.x, 3.15, 3.40+ format compatibility
- ✅ Bandwidth field preference (`bw` vs `bw_bytes`)
- ✅ IOPS field preference (`iops` vs `iops_mean`)
- ✅ Latency parsing and unit conversion
- ✅ Multiple job aggregation
- ✅ Missing field handling
- ✅ Empty/malformed data handling
- ✅ Edge case error recovery
