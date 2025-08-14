# Test Suite Documentation

## Overview
Comprehensive test suite for Sublime Sensitive Text Hider, covering both standalone script and Sublime plugin functionality.

## Test Structure

### Standalone Script Tests (`test_standalone_script.py`)
- **26 unit tests** covering all core functionality
- Tests pattern matching for emails, SSNs, credit cards, IP addresses, API keys, passwords
- Validates file backup/restore mechanisms
- Tests custom pattern loading and configuration

### Sublime Plugin Tests (`test_sublime_plugin.py`)
- **19 unit tests** for Sublime Text integration
- Tests all plugin commands and event listeners
- Validates in-memory and file-based storage
- Tests user interaction flows

## Running Tests

### Quick Start
```bash
# Run standalone tests (no Sublime dependencies)
make test

# Or using Python directly
python3 run_tests.py --standalone
```

### All Test Options
```bash
# Run all tests
make test-all

# Run with verbose output
make test-verbose

# Clean test artifacts
make clean

# Show coverage analysis
python3 test_coverage.py
```

### Using the Test Runner
```bash
# Run specific test module
python3 -m unittest tests.test_standalone_script

# Run specific test class
python3 -m unittest tests.test_standalone_script.TestHideSensitiveText

# Run specific test method
python3 -m unittest tests.test_standalone_script.TestHideSensitiveText.test_hide_email_addresses
```

## Test Coverage

### Business Logic Coverage
- ✅ Pattern matching for sensitive data types
- ✅ Text hiding and revealing operations
- ✅ Backup file creation and management
- ✅ Custom pattern configuration
- ✅ Error handling and edge cases

### Critical Path Coverage
- ✅ Main workflow: hide → backup → reveal
- ✅ File I/O operations
- ✅ Configuration loading
- ✅ Command-line interface
- ✅ Sublime Text integration

## CI/CD Integration
Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Multiple Python versions (3.8-3.12)
- Multiple OS platforms (Ubuntu, macOS, Windows)

## Test Data
Tests use temporary files and in-memory data structures to avoid side effects.
All test artifacts are automatically cleaned up after test execution.

## Contributing
When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add coverage for edge cases
4. Update this documentation