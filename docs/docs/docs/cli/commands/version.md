---
slug: /cli/commands/version
title: Version Command
description: Display version information for midil-kit and service projects
---

# Version Command

The `version` command displays version information for midil-kit and service projects, with support for both detailed and short output formats.

## Usage

```bash
midil version [--short]
```

### Options

- `--short, -s`: Display only the short version number

## Examples

### Detailed Version Information

```bash
# Display full version information with logo
midil version
```

**Output:**
```
⚡ Ingenuity ⚡
by midil.io

midil-kit
  └── version: 3.4.4

my-service
  └── version: 0.1.0
```

### Short Version

```bash
# Display short version only
midil version --short
```

**Output:**
```
midil-kit 3.4.4
```

## Version Detection

### midil-kit Version

The command displays the installed midil-kit version from `__version__`:

```python
# From midil.version
__version__ = "3.4.4"
```

### Service Version

When run from within a service directory, it also displays the service version:

1. **Directory Detection**: Checks if "services" is in the current path
2. **Service Name**: Extracts service name from directory structure
3. **Version Source**: Reads from `__service_version__` in the service

### Service Directory Structure

```
project/
├── services/
│   ├── my-api/          # Service directory
│   │   ├── main.py
│   │   └── pyproject.toml
│   └── another-service/
└── other-files/
```

## Version Sources

### midil-kit Version

- **Source**: `midil.version.__version__`
- **Format**: Semantic versioning (e.g., `3.4.4`)
- **Location**: Package metadata

### Service Version

- **Source**: `midil.version.__service_version__`
- **Format**: Semantic versioning (e.g., `0.1.0`)
- **Location**: Service project configuration

## Output Formats

### Detailed Format

The detailed format includes:

1. **Logo Display**: ASCII art logo with styling
2. **midil-kit Version**: Always displayed
3. **Service Version**: Only when in service directory
4. **Rich Formatting**: Colored and styled output

### Short Format

The short format provides:

1. **Package Name**: `midil-kit`
2. **Version Number**: `3.4.4`
3. **No Logo**: Clean, minimal output
4. **Single Line**: Suitable for scripts and automation

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Check Version
  run: |
    echo "midil-kit version: $(midil version --short)"
    echo "Service version: $(cd services/my-api && midil version --short)"
```

### Scripts and Automation

```bash
# Get version for logging
VERSION=$(midil version --short)
echo "Starting deployment with midil-kit $VERSION"

# Check if specific version is installed
if midil version --short | grep -q "3.4.4"; then
    echo "Correct version installed"
else
    echo "Version mismatch detected"
fi
```

### Development Workflow

```bash
# Check versions before development
midil version

# Verify service version
cd services/my-api
midil version --short
```

## Troubleshooting

### Version Not Displayed

1. **Check Installation**:
   ```bash
   pip show midil-kit
   ```

2. **Verify Entry Point**:
   ```bash
   which midil
   ```

3. **Test Import**:
   ```bash
   python -c "from midil.version import __version__; print(__version__)"
   ```

### Service Version Issues

1. **Not in Service Directory**:
   ```bash
   # Ensure you're in a service directory
   pwd
   ls -la
   ```

2. **Service Version Not Found**:
   ```bash
   # Check if service has proper structure
   ls -la services/my-service/
   ```

3. **Version Import Error**:
   ```bash
   # Test service version import
   python -c "from midil.version import __service_version__; print(__service_version__)"
   ```

## Advanced Usage

### Version Comparison

```bash
# Compare versions in script
CURRENT_VERSION=$(midil version --short | cut -d' ' -f2)
REQUIRED_VERSION="3.4.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$CURRENT_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo "Version is sufficient"
else
    echo "Version is too old"
fi
```

### Version Logging

```python
# Python script
import subprocess
import json

def get_version_info():
    result = subprocess.run(['midil', 'version', '--short'], 
                          capture_output=True, text=True)
    return result.stdout.strip()

version = get_version_info()
print(f"Running with {version}")
```

### Custom Version Display

```bash
# Create custom version script
#!/bin/bash
echo "=== MIDIL Environment ==="
midil version
echo "=== System Info ==="
python --version
pip --version
```

## Configuration

### Environment Variables

The version command respects the following environment variables:

```bash
# Override version display
export MIDIL_VERSION_FORMAT=short
midil version  # Will use short format
```

### Custom Version Sources

You can customize version sources by modifying:

1. **Package Version**: `midil/version.py`
2. **Service Version**: Service's `pyproject.toml`
3. **Display Format**: CLI command implementation

<!-- source: midil-kit-main/midil/cli/commands/version.py -->
<!-- source: midil-kit-main/midil/version.py -->
<!-- source: midil-kit-main/pyproject.toml -->
