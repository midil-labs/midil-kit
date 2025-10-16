---
slug: /cli/commands/test
title: Test Command
description: Run tests with pytest integration, coverage reporting, and MIDIL-style options
---

# Test Command

The `test` command provides integrated testing functionality using pytest with coverage reporting, HTML output, and MIDIL-specific configurations.

## Usage

```bash
midil test [--coverage] [--file FILE] [--verbose] [--html-cov]
```

### Options

- `--coverage, -c`: Enable coverage reporting
- `--file, -f FILE`: Test specific file or directory
- `--verbose, -v`: Run in verbose mode
- `--html-cov`: Generate HTML coverage report

## Examples

### Basic Testing

```bash
# Run all tests
midil test

# Run with verbose output
midil test --verbose

# Test specific file
midil test --file tests/test_auth.py

# Test specific directory
midil test --file tests/auth/
```

### Coverage Testing

```bash
# Run with coverage
midil test --coverage

# Generate HTML coverage report
midil test --coverage --html-cov

# Test specific file with coverage
midil test --file tests/test_auth.py --coverage
```

## Test Runner Detection

The command automatically detects the appropriate test runner:

### Poetry Projects
```bash
# Detected command
poetry run pytest [options]
```

### Direct Python Projects
```bash
# Detected command
python -m pytest [options]
```

## Coverage Configuration

### Built-in Coverage Options

The test command automatically adds coverage options:

```bash
# Generated pytest command with coverage
pytest --cov=midil --cov-report=term-missing --cov-report=html
```

### Coverage Reports

1. **Terminal Report**: Shows coverage percentage and missing lines
2. **HTML Report**: Generates detailed HTML report in `htmlcov/` directory

## Test Discovery

### File Patterns

The command discovers tests using standard pytest patterns:

- **Test Files**: `test_*.py`
- **Test Classes**: `Test*`
- **Test Functions**: `test_*`

### Directory Structure

```
tests/
├── __init__.py
├── test_auth.py
├── test_cli.py
├── auth/
│   ├── __init__.py
│   ├── test_authenticator.py
│   └── test_authorizer.py
└── cli/
    ├── __init__.py
    └── test_commands.py
```

## MIDIL-Specific Configuration

### Pytest Options

The command automatically adds MIDIL-specific pytest options:

```bash
# Standard MIDIL test command
pytest --strict-markers --strict-config -p pytest_asyncio
```

### Async Test Support

Full pytest-asyncio integration for testing async code:

```python
# Example async test
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Error Handling

### Common Errors

1. **Test Path Not Found**
   ```
   Test path 'tests/nonexistent.py' does not exist
   ```
   **Solution**: Verify the file path exists

2. **No Tests Found**
   ```
   No tests found in the specified path
   ```
   **Solution**: Check test file naming conventions

3. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'midil'
   ```
   **Solution**: Install dependencies with `poetry install` or `pip install -e .`

### Exit Codes

- **0**: All tests passed
- **1**: Tests failed or error occurred
- **130**: Tests interrupted by user (Ctrl+C)

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Run Tests
  run: midil test --coverage --html-cov

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Development Workflow

```bash
# 1. Run tests during development
midil test --verbose

# 2. Check coverage before commit
midil test --coverage

# 3. Generate HTML report for review
midil test --coverage --html-cov

# 4. Open coverage report
open htmlcov/index.html
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: midil test --coverage
        language: system
        pass_filenames: false
```

## Advanced Usage

### Custom Test Configuration

Create a `pytest.ini` file for custom configuration:

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --strict-config -p pytest_asyncio
markers =
    asyncio: mark test as async
    slow: mark test as slow
    integration: mark test as integration
```

### Parallel Testing

```bash
# Install pytest-xdist for parallel testing
pip install pytest-xdist

# Run tests in parallel
midil test --file tests/ -n auto
```

### Test Filtering

```bash
# Run only fast tests
midil test --file tests/ -m "not slow"

# Run only integration tests
midil test --file tests/ -m "integration"
```

## Troubleshooting

### Tests Not Running

1. **Check Dependencies**:
   ```bash
   pip list | grep pytest
   pip list | grep pytest-cov
   ```

2. **Verify Test Files**:
   ```bash
   find . -name "test_*.py" -type f
   ```

3. **Check Python Path**:
   ```bash
   python -c "import sys; print(sys.path)"
   ```

### Coverage Issues

1. **Missing Coverage**:
   ```bash
   # Check coverage configuration
   midil test --coverage --verbose
   ```

2. **HTML Report Not Generated**:
   ```bash
   # Ensure htmlcov directory is writable
   chmod 755 htmlcov/
   ```

### Performance Issues

1. **Slow Tests**:
   ```bash
   # Run with timing
   midil test --verbose --durations=10
   ```

2. **Memory Issues**:
   ```bash
   # Run specific test files
   midil test --file tests/unit/
   ```

<!-- source: midil-kit-main/midil/cli/commands/test.py -->
<!-- source: midil-kit-main/midil/cli/core/testing/builder.py -->
<!-- source: midil-kit-main/midil/cli/core/testing/options.py -->
<!-- source: midil-kit-main/midil/cli/core/testing/runner.py -->
