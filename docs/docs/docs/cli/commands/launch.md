---
slug: /cli/commands/launch
title: Launch Command
description: Launch midil-kit services with intelligent configuration and auto-discovery
---

# Launch Command

The `launch` command intelligently discovers and launches midil-kit services using Uvicorn, with automatic configuration resolution and beautiful console output.

## Usage

```bash
midil launch [--port PORT] [--host HOST] [--reload]
```

### Options

- `--port PORT`: Server port *(inherits from settings if not specified)*
- `--host HOST`: Server host *(inherits from settings if not specified)*
- `--reload`: Enable auto-reload on code changes

## Examples

### Basic Launch

```bash
# Launch with default settings
midil launch

# Launch with custom port
midil launch --port 3000

# Launch with reload enabled
midil launch --reload

# Launch with custom host and port
midil launch --host 127.0.0.1 --port 8080 --reload
```

## Configuration Priority

The launch command resolves configuration in the following order:

1. **CLI Arguments** (highest priority)
2. **Environment Variables**
3. **Settings Configuration**
4. **Default Values** (lowest priority)

### Default Values

- **Port**: `8000`
- **Host**: `0.0.0.0`
- **Reload**: `False`

## Auto-Discovery

The launch command automatically discovers FastAPI applications:

### Application Discovery

1. **Default Module**: Looks for `main:app` in the current directory
2. **File Check**: Verifies `main.py` exists
3. **Module Resolution**: Resolves the FastAPI app instance

### Supported Patterns

```python
# main.py - Standard pattern
from fastapi import FastAPI
app = FastAPI()

# Alternative patterns
from fastapi import FastAPI
application = FastAPI()  # Will work with main:application
```

## Rich Console Output

The launch command provides beautiful console output:

```
⚡ Ingenuity ⚡
by midil.io

🛸 Launching my-api (v0.1.0)
   using midil-kit (v3.4.4)
   on http://0.0.0.0:8000

✨ Sit back, relax, and watch the magic happen!
```

## Service Information Display

The command displays:
- **Service Name**: Extracted from project directory
- **Service Version**: From `__service_version__`
- **midil-kit Version**: From `__version__`
- **Server URL**: Complete URL with host and port

## Uvicorn Integration

The launch command is built on top of Uvicorn with:

### Command Building

```python
# Generated uvicorn command
uvicorn main:app --port=8000 --host=0.0.0.0 --reload
```

### Supported Uvicorn Options

- `--port`: Server port
- `--host`: Server host
- `--reload`: Auto-reload on code changes
- `--workers`: Number of worker processes *(inferred)*
- `--log-level`: Logging level *(inferred)*

## Error Handling

### Common Errors

1. **File Not Found**
   ```
   Cannot find main.py in /path/to/project
   ```
   **Solution**: Ensure you're in a valid project directory with `main.py`

2. **Module Import Error**
   ```
   ModuleNotFoundError: No module named 'main'
   ```
   **Solution**: Check that `main.py` is properly formatted and dependencies are installed

3. **Port Already in Use**
   ```
   [Errno 48] Address already in use
   ```
   **Solution**: Use a different port with `--port` option

### Debugging

Enable verbose output for debugging:

```bash
# Check what command will be executed
midil launch --port 8000 --verbose
```

## Integration Examples

### Development Workflow

```bash
# 1. Navigate to project
cd services/my-api

# 2. Install dependencies
poetry install

# 3. Launch with reload for development
midil launch --reload

# 4. Access the service
curl http://localhost:8000
```

### Production Deployment

```bash
# Launch without reload for production
midil launch --host 0.0.0.0 --port 8000

# With environment variables
export API_HOST=0.0.0.0
export API_PORT=8000
midil launch
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["midil", "launch", "--host", "0.0.0.0", "--port", "8000"]
```

## Advanced Usage

### Custom Application Module

```bash
# Launch with custom app module
midil launch --app-module "src.main:app"
```

### Environment-Specific Configuration

```bash
# Development
midil launch --reload --port 3000

# Staging
midil launch --host 0.0.0.0 --port 8000

# Production
midil launch --host 0.0.0.0 --port 80
```

### Process Management

```bash
# Run in background
nohup midil launch --port 8000 > app.log 2>&1 &

# With process manager
pm2 start "midil launch --port 8000" --name my-api
```

## Troubleshooting

### Service Won't Start

1. **Check Dependencies**:
   ```bash
   pip list | grep fastapi
   pip list | grep uvicorn
   ```

2. **Verify Application**:
   ```bash
   python -c "from main import app; print('App loaded successfully')"
   ```

3. **Check Port Availability**:
   ```bash
   lsof -i :8000
   ```

### Performance Issues

1. **Disable Reload in Production**:
   ```bash
   midil launch --port 8000  # No --reload flag
   ```

2. **Use Multiple Workers**:
   ```bash
   # Use gunicorn with uvicorn workers
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

<!-- source: midil-kit-main/midil/cli/commands/launch.py -->
<!-- source: midil-kit-main/midil/cli/core/launchers/uvicorn.py -->
<!-- source: midil-kit-main/midil/cli/core/launchers/base.py -->
