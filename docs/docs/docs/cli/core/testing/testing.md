---
slug: /cli/testing
title: Testing Framework
description: Integrated testing framework with pytest, coverage reporting, and MIDIL-specific configurations
---

# Testing Framework

The testing framework provides integrated pytest functionality with coverage reporting, HTML output, and MIDIL-specific configurations. It automatically detects the appropriate test runner and applies consistent testing standards.

## Overview

The testing framework includes:
- **Test Runner Detection**: Automatic detection of Poetry vs direct Python execution
- **Coverage Integration**: Built-in coverage reporting with multiple output formats
- **Command Building**: Flexible command construction with various options
- **Error Handling**: Comprehensive error handling and user feedback

## Core Components

### TestOptions

Configuration class for test options:

```python
@dataclass
class TestOptions:
    coverage: bool = False
    file: Optional[str] = None
    verbose: bool = False
    html_cov: bool = False
```

**Purpose**: Encapsulates all test configuration options.

**Usage**: Pass to `PytestRunner` for test execution.

### PytestCommandBuilder

Builder pattern for constructing pytest commands:

```python
class PytestCommandBuilder:
    def __init__(self, options: TestOptions):
        self.options = options
        self.command: list[str] = []
```

#### Key Methods

##### determine_runner()

```python
def determine_runner(self) -> "PytestCommandBuilder":
    if Path("pyproject.toml").exists():
        self.command = ["poetry", "run", "pytest"]
    else:
        self.command = ["python", "-m", "pytest"]
    return self
```

**Purpose**: Detects whether to use Poetry or direct Python execution.

**Detection Logic**:
- If `pyproject.toml` exists → Use `poetry run pytest`
- Otherwise → Use `python -m pytest`

##### add_options()

```python
def add_options(self) -> "PytestCommandBuilder":
    if self.options.verbose:
        self.command.append("-v")
    
    if self.options.coverage or self.options.html_cov:
        self.command.extend(["--cov=midil", "--cov-report=term-missing"])
        
        if self.options.html_cov:
            self.command.append("--cov-report=html")
    
    if self.options.file:
        path = Path(self.options.file)
        if not path.exists():
            raise FileNotFoundError(f"Test path '{self.options.file}' does not exist")
        self.command.append(str(path))
    
    self.command.extend([
        "--strict-markers", 
        "--strict-config", 
        "-p", "pytest_asyncio"
    ])
    return self
```

**Purpose**: Adds various pytest options based on configuration.

**Options Added**:
- `-v`: Verbose output
- `--cov=midil`: Coverage for midil package
- `--cov-report=term-missing`: Terminal coverage report
- `--cov-report=html`: HTML coverage report
- `--strict-markers`: Strict marker validation
- `--strict-config`: Strict configuration validation
- `-p pytest_asyncio`: Async test support

##### build()

```python
def build(self) -> list[str]:
    return self.command
```

**Purpose**: Returns the final command as a list of arguments.

### PytestRunner

Test execution runner with comprehensive error handling:

```python
class PytestRunner:
    def __init__(self, options: TestOptions):
        self.options = options
    
    def run(self):
        # Execute tests with error handling
        pass
```

#### Key Methods

##### run()

```python
def run(self):
    try:
        builder = PytestCommandBuilder(self.options)
        command = builder.determine_runner().add_options().build()
        
        if self.options.html_cov:
            console.print("📊 HTML coverage report will be generated in htmlcov/", style="cyan")
        
        console.print(f"Running: {' '.join(command)}", style="dim")
        result = subprocess.run(command)
        
        if result.returncode == 0:
            console.print("✅ All tests passed!", style="green")
        else:
            console.print(f"❌ Tests failed with exit code {result.returncode}", style="red")
        sys.exit(result.returncode)
        
    except FileNotFoundError as e:
        console.print(f"❌ {e}", style="red")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n⚠️  Tests interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error running tests: {e}", style="red")
        sys.exit(1)
```

**Purpose**: Executes tests with proper error handling and user feedback.

**Error Handling**:
- `FileNotFoundError`: Test path doesn't exist
- `KeyboardInterrupt`: User interrupted tests
- `Exception`: General errors
- `subprocess.CalledProcessError`: Test execution failed

## Usage Examples

### Basic Testing

```python
from midil.cli.core.testing import TestOptions, PytestRunner

# Run all tests
options = TestOptions()
runner = PytestRunner(options)
runner.run()
```

### Coverage Testing

```python
# Run with coverage
options = TestOptions(coverage=True)
runner = PytestRunner(options)
runner.run()
```

### Specific File Testing

```python
# Test specific file
options = TestOptions(file="tests/test_auth.py", verbose=True)
runner = PytestRunner(options)
runner.run()
```

### HTML Coverage Report

```python
# Generate HTML coverage report
options = TestOptions(coverage=True, html_cov=True)
runner = PytestRunner(options)
runner.run()
```

## Generated Commands

### Poetry Projects

```bash
# Basic test command
poetry run pytest --strict-markers --strict-config -p pytest_asyncio

# With coverage
poetry run pytest --cov=midil --cov-report=term-missing --strict-markers --strict-config -p pytest_asyncio

# With HTML coverage
poetry run pytest --cov=midil --cov-report=term-missing --cov-report=html --strict-markers --strict-config -p pytest_asyncio

# Specific file
poetry run pytest tests/test_auth.py --strict-markers --strict-config -p pytest_asyncio
```

### Direct Python Projects

```bash
# Basic test command
python -m pytest --strict-markers --strict-config -p pytest_asyncio

# With coverage
python -m pytest --cov=midil --cov-report=term-missing --strict-markers --strict-config -p pytest_asyncio
```

## Configuration Integration

### pyproject.toml Integration

The testing framework respects pytest configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=midil",
    "--cov-report=term-missing",
    "--cov-report=html",
    "-p",
    "pytest_asyncio",
]
markers = [
    "asyncio: mark test as async",
]
```

### Environment Variables

The framework respects pytest environment variables:

```bash
# Set pytest options via environment
export PYTEST_ADDOPTS="--verbose --tb=short"
midil test
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

4. **Coverage Not Available**
   ```
   No module named 'pytest_cov'
   ```
   **Solution**: Install pytest-cov: `pip install pytest-cov`

### Exit Codes

- **0**: All tests passed
- **1**: Tests failed or error occurred
- **130**: Tests interrupted by user (Ctrl+C)

## Integration Examples

### CLI Integration

```python
# In commands/test.py
@click.command("test")
@click.option("--coverage", "-c", is_flag=True, help="Run with coverage")
@click.option("--file", "-f", type=str, help="Run tests for a specific file or dir")
@click.option("--verbose", "-v", is_flag=True, help="Run in verbose mode")
@click.option("--html-cov", is_flag=True, help="Generate HTML coverage report")
def test_command(coverage, file, verbose, html_cov):
    options = TestOptions(
        coverage=coverage, file=file, verbose=verbose, html_cov=html_cov
    )
    runner = PytestRunner(options)
    runner.run()
```

### CI/CD Integration

```yaml
# GitHub Actions
- name: Run Tests
  run: midil test --coverage --html-cov

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
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

```python
# Custom test options
options = TestOptions(
    coverage=True,
    file="tests/integration/",
    verbose=True,
    html_cov=True
)
runner = PytestRunner(options)
runner.run()
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

## Best Practices

### Test Organization

- Use descriptive test file names
- Group related tests in directories
- Follow pytest naming conventions
- Use appropriate test markers

### Coverage Configuration

- Set reasonable coverage thresholds
- Exclude test files from coverage
- Use coverage reports for quality gates
- Monitor coverage trends over time

### Error Handling

- Test error conditions
- Use appropriate assertions
- Provide meaningful error messages
- Handle edge cases properly

## Troubleshooting

### Common Issues

1. **Tests Not Running**
   - Check pytest installation
   - Verify test file naming
   - Check Python path configuration

2. **Coverage Issues**
   - Install pytest-cov
   - Check coverage configuration
   - Verify source paths

3. **Import Errors**
   - Install project dependencies
   - Check PYTHONPATH
   - Verify virtual environment

### Debug Mode

```bash
# Enable verbose output
midil test --verbose

# Check command that will be executed
midil test --verbose --dry-run
```

<!-- source: midil-kit-main/midil/cli/core/testing/builder.py -->
<!-- source: midil-kit-main/midil/cli/core/testing/options.py -->
<!-- source: midil-kit-main/midil/cli/core/testing/runner.py -->
