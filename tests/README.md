# Racer Tests

This directory contains tests for the Racer project.

## Test Structure

- `test_basic.py` - Basic unit tests for core functionality
- `test_integration_simple.py` - Simple integration tests for API endpoints
- `unit/` - Detailed unit tests (currently not working due to import issues)
- `integration/` - Complex integration tests (currently not working due to import issues)

## Running Tests

### All Tests
```bash
make test
```

### Unit Tests Only
```bash
make test-unit
```

### Integration Tests Only
```bash
make test-integration
```

### Quick Tests (No Docker/API)
```bash
make test-quick
```

### With Coverage
```bash
make test-coverage
```

## Test Categories

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test API endpoints and full workflows
- **Docker Tests**: Tests that require Docker to be running
- **API Tests**: Tests that require the API server to be running

## Current Status

✅ **Working Tests:**
- Basic functionality tests (`test_basic.py`)
- Simple integration tests (`test_integration_simple.py`)

❌ **Not Working:**
- Complex unit tests in `unit/` directory (import path issues)
- Complex integration tests in `integration/` directory (import path issues)

## Test Coverage

Current test coverage is around 13% due to the limited number of working tests. The basic tests cover:

- Dockerfile generation
- Project validation
- CLI imports
- API client imports
- Docker manager imports
- Backend module imports
- API health endpoint
- API root endpoint
- API validate endpoint

## Future Improvements

1. Fix import path issues in unit tests
2. Add more comprehensive test coverage
3. Add Docker-specific tests
4. Add performance tests
5. Add end-to-end workflow tests
