---
slug: /cli/launchers
title: Service Launchers
description: Service launcher implementations for running midil-kit applications
---

# Service Launchers

The launcher system provides a flexible and extensible way to launch different types of services in midil-kit applications. Built on an abstract base class pattern, it supports various deployment scenarios and service types.

## Overview

Launchers handle the execution of services with:
- **Auto-discovery**: Automatic detection of service applications
- **Configuration Management**: Flexible configuration resolution
- **Process Management**: Proper process execution and monitoring
- **Error Handling**: Comprehensive error handling and reporting

## Base Launcher

### BaseLauncher Abstract Class

```python
from abc import ABC, abstractmethod

class BaseLauncher(ABC):
    @abstractmethod
    def run(self) -> None:
        """Execute the launcher and start the service."""
        pass
```

**Purpose**: Defines the contract for all launcher implementations.

**Usage**: Extend this class to create custom launchers for different service types.

## Uvicorn Launcher

### UvicornLauncher Class

The primary launcher for FastAPI applications using Uvicorn ASGI server.

```python
class UvicornLauncher(BaseLauncher):
    def __init__(
        self,
        app_module: str = "main:app",
        port: int = 8000,
        host: str = "0.0.0.0",
        reload: bool = True,
        extra_args: Optional[list[str]] = None,
        project_dir: Optional[Path] = None,
    ):
        # Initialize launcher configuration
        pass
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_module` | `str` | `"main:app"` | FastAPI app module path |
| `port` | `int` | `8000` | Server port |
| `host` | `str` | `"0.0.0.0"` | Server host |
| `reload` | `bool` | `True` | Enable auto-reload |
| `extra_args` | `list[str]` | `[]` | Additional uvicorn arguments |
| `project_dir` | `Path` | `Path.cwd()` | Project directory |

### Key Methods

#### discover_app()

```python
def discover_app(self) -> Path:
    """Discover the FastAPI app file based on the app_module."""
    module_file = self.app_module.split(":")[0]
    app_path = self.project_dir / f"{module_file}.py"
    if not app_path.exists():
        raise FileNotFoundError(
            f"Cannot find {module_file}.py in {self.project_dir}."
        )
    return app_path
```

**Purpose**: Locates the FastAPI application file.

**Error Handling**: Raises `FileNotFoundError` if the app file doesn't exist.

#### build_command()

```python
def build_command(self) -> list[str]:
    """Build the uvicorn command as a list of arguments."""
    cmd = [
        "uvicorn",
        self.app_module,
        f"--port={self.port}",
        f"--host={self.host}",
    ]
    if self.reload:
        cmd.append("--reload")
    cmd.extend(self.extra_args)
    return cmd
```

**Purpose**: Constructs the uvicorn command with all options.

**Output**: List of command arguments ready for subprocess execution.

#### run()

```python
def run(self) -> None:
    """Auto-discover FastAPI app and launch it with uvicorn."""
    command = self.build_command()
    subprocess.run(command, cwd=str(self.project_dir))
```

**Purpose**: Executes the launcher and starts the service.

**Process Management**: Runs uvicorn in the project directory.

## Usage Examples

### Basic Usage

```python
from midil.cli.core.launchers.uvicorn import UvicornLauncher

# Create launcher with defaults
launcher = UvicornLauncher()
launcher.run()
```

### Custom Configuration

```python
# Custom port and host
launcher = UvicornLauncher(
    port=3000,
    host="127.0.0.1",
    reload=False
)
launcher.run()
```

### Development Mode

```python
# Development configuration with reload
launcher = UvicornLauncher(
    app_module="src.main:app",
    port=8000,
    host="0.0.0.0",
    reload=True,
    extra_args=["--log-level", "debug"]
)
launcher.run()
```

### Production Mode

```python
# Production configuration
launcher = UvicornLauncher(
    app_module="main:app",
    port=80,
    host="0.0.0.0",
    reload=False,
    extra_args=["--workers", "4"]
)
launcher.run()
```

## Integration with CLI

### Launch Command Integration

```python
# In commands/launch.py
@click.command("launch")
@click.option("--port", type=int, help="Port to run the server on")
@click.option("--host", help="Host to run the server on")
@click.option("--reload", is_flag=True, help="Reload on code changes")
def launch_command(port, host, reload):
    launcher = UvicornLauncher(
        port=port or 8000,
        host=host or "0.0.0.0",
        reload=reload
    )
    launcher.run()
```

### Configuration Resolution

The launcher respects the CLI configuration priority:

1. **CLI Arguments** (highest priority)
2. **Environment Variables**
3. **Settings Configuration**
4. **Default Values** (lowest priority)

## Error Handling

### Common Errors

1. **File Not Found**
   ```python
   # When app file doesn't exist
   FileNotFoundError: Cannot find main.py in /path/to/project
   ```

2. **Module Import Error**
   ```python
   # When app module can't be imported
   ModuleNotFoundError: No module named 'main'
   ```

3. **Port Already in Use**
   ```python
   # When port is occupied
   OSError: [Errno 48] Address already in use
   ```

### Error Handling Strategies

```python
def run_with_error_handling(self) -> None:
    try:
        self.discover_app()
        command = self.build_command()
        subprocess.run(command, cwd=str(self.project_dir))
    except FileNotFoundError as e:
        console.print(f"❌ App file not found: {e}", style="red")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Launch failed: {e}", style="red")
        sys.exit(1)
```

## Extensibility

### Creating Custom Launchers

```python
class GunicornLauncher(BaseLauncher):
    def __init__(self, app_module: str, workers: int = 4):
        self.app_module = app_module
        self.workers = workers
    
    def run(self) -> None:
        command = [
            "gunicorn",
            self.app_module,
            f"--workers={self.workers}",
            "-k", "uvicorn.workers.UvicornWorker"
        ]
        subprocess.run(command)
```

### Docker Launcher

```python
class DockerLauncher(BaseLauncher):
    def __init__(self, image_name: str, port: int = 8000):
        self.image_name = image_name
        self.port = port
    
    def run(self) -> None:
        command = [
            "docker", "run",
            "-p", f"{self.port}:8000",
            self.image_name
        ]
        subprocess.run(command)
```

## Best Practices

### Configuration Management

- Use environment variables for deployment-specific settings
- Provide sensible defaults for development
- Validate configuration values before use
- Document all configuration options

### Error Handling

- Catch specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Exit with proper status codes

### Process Management

- Use subprocess.run() for process execution
- Set appropriate working directory
- Handle process signals properly
- Monitor process health

### Testing

```python
# Unit test example
def test_uvicorn_launcher():
    launcher = UvicornLauncher(port=8000, host="localhost")
    command = launcher.build_command()
    
    assert "uvicorn" in command
    assert "--port=8000" in command
    assert "--host=localhost" in command
```

## Troubleshooting

### Common Issues

1. **App Not Starting**
   - Check that `main.py` exists
   - Verify FastAPI app is properly defined
   - Ensure all dependencies are installed

2. **Port Conflicts**
   - Use `--port` option to specify different port
   - Check if port is already in use
   - Use `lsof -i :8000` to check port usage

3. **Module Import Errors**
   - Verify Python path includes project directory
   - Check that all imports are available
   - Ensure virtual environment is activated

### Debug Mode

```python
# Enable debug logging
launcher = UvicornLauncher(
    extra_args=["--log-level", "debug"]
)
launcher.run()
```

<!-- source: midil-kit-main/midil/cli/core/launchers/base.py -->
<!-- source: midil-kit-main/midil/cli/core/launchers/uvicorn.py -->
