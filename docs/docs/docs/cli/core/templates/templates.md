---
slug: /cli/templates
title: Project Templates
description: Cookiecutter templates and project structures for midil-kit scaffolding
---

# Project Templates

The template system provides Cookiecutter-based project templates for scaffolding midil-kit applications. Templates include FastAPI services, Lambda functions, and extensible project structures.

## Overview

Templates are organized using Cookiecutter's directory structure:
- **Template Configuration**: `cookiecutter.json` with variables
- **Template Files**: Jinja2-templated project files
- **Custom Extensions**: Jinja2 extensions for advanced templating
- **Post-Generation Hooks**: Python hooks for project customization

## Template Structure

```
cli/core/templates/
└── cookiecutter-midil-project/
    ├── cookiecutter.json              # Template configuration <!-- source: midil-kit-main/midil/cli/core/templates/cookiecutter-midil-project/cookiecutter.json -->
    ├── extensions.py                  # Custom Jinja2 extensions <!-- source: midil-kit-main/midil/cli/core/templates/cookiecutter-midil-project/extensions.py -->
    ├── hooks/                         # Post-generation hooks
    │   └── post_gen_project.py        # Project customization <!-- source: midil-kit-main/midil/cli/core/templates/cookiecutter-midil-project/hooks/post_gen_project.py -->
    └── {{cookiecutter.project_slug}}/ # Template directory
        ├── {% if cookiecutter.include_docker == 'y' %}Dockerfile{% endif %}
        ├── main.py
        ├── poetry.toml
        ├── pyproject.toml
        └── README.md
```

## Template Configuration

### cookiecutter.json

Template configuration with variables and extensions:

```json
{
    "project_name": "My MIDIL Project",
    "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '-').replace('_', '-') }}",
    "project_short_description": "A project created with MIDIL CLI",
    "author_name": "Your Name",
    "author_email": "your.email@example.com",
    "service_version": "0.1.0",
    "python_version": "3.12",
    "include_docker": "n",
    "_extensions": [
        "extensions.VersionExtension"
    ]
}
```

### Template Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `project_name` | Human-readable project name | "My MIDIL Project" | "User Management API" |
| `project_slug` | URL-safe identifier | Auto-generated | "user-management-api" |
| `project_short_description` | Brief description | "A project created with MIDIL CLI" | "User management service" |
| `author_name` | Author name | "Your Name" | "John Doe" |
| `author_email` | Author email | "your.email@example.com" | "john@example.com" |
| `service_version` | Initial version | "0.1.0" | "0.1.0" |
| `python_version` | Python version | "3.12" | "3.12" |
| `include_docker` | Docker support | "n" | "y" or "n" |

## Custom Extensions

### VersionExtension

Jinja2 extension for embedding midil-kit version in templates:

```python
from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.parser import Parser
from midil.version import __version__

class VersionExtension(Extension):
    tags = {"version"}
    
    def parse(self, parser: Parser) -> nodes.Node | list[nodes.Node]:
        return nodes.Const(__version__, lineno=next(parser.stream).lineno)
```

**Usage in Templates**:
```python
# In template files
__version__ = "{% version %}"
```

## Post-Generation Hooks

### ProjectHook Abstract Class

Base class for post-generation hooks:

```python
from abc import ABC, abstractmethod

class ProjectHook(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass
```

### ListProcessingHook

Base hook for processing lists of items:

```python
class ListProcessingHook(ProjectHook, ABC):
    def __init__(self, items: Optional[Iterable[str]] = None):
        self.items = list(items or [])
    
    @abstractmethod
    def process_item(self, item: str) -> None:
        pass
    
    def execute(self) -> None:
        for item in self.items:
            self.process_item(item)
```

### Concrete Hooks

#### ConditionalFileRemover

Removes files based on user configuration:

```python
class ConditionalFileRemover(ListProcessingHook):
    def __init__(self, docker_flag: str, files: Optional[Iterable[str]] = None):
        default_files = ["Dockerfile", "docker-compose.yml"]
        super().__init__(files or default_files)
        self.docker_flag = docker_flag
    
    def execute(self) -> None:
        if self.docker_flag != "y":
            super().execute()
    
    def process_item(self, item: str) -> None:
        path = Path(item)
        if path.exists():
            path.unlink()
```

#### DirectoryCreator

Creates additional directories:

```python
class DirectoryCreator(ListProcessingHook):
    def __init__(self, directories: Optional[Iterable[str]] = None):
        super().__init__(directories or ["tests"])
    
    def process_item(self, item: str) -> None:
        Path(item).mkdir(parents=True, exist_ok=True)
```

#### FileCreator

Creates Python package files:

```python
class FileCreator(ListProcessingHook):
    def __init__(self, files: Optional[Iterable[str]] = None):
        super().__init__(files or ["tests/__init__.py"])
    
    def process_item(self, item: str) -> None:
        Path(item).touch()
```

### PostGenProjectManager

Coordinates execution of post-generation hooks:

```python
class PostGenProjectManager:
    def __init__(self, hooks: Iterable[ProjectHook]):
        self.hooks = list(hooks)
    
    def run(self) -> None:
        for hook in self.hooks:
            hook.execute()
```

## Generated Project Structure

### FastAPI Project

When scaffolding a FastAPI project, the template generates:

```
services/
└── my-api/
    ├── main.py              # FastAPI application
    ├── pyproject.toml       # Poetry configuration
    ├── poetry.toml          # Poetry lock file
    ├── README.md            # Project documentation
    └── Dockerfile           # Optional Docker support
```

### Template Files

#### main.py

```python
from fastapi import FastAPI

app = FastAPI(
    title="{{ cookiecutter.project_name }}",
    description="{{ cookiecutter.project_short_description }}",
    version="{{ cookiecutter.service_version }}"
)

@app.get("/")
async def root():
    return {"message": "Hello from {{ cookiecutter.project_name }}"}
```

#### pyproject.toml

```toml
[tool.poetry]
name = "{{ cookiecutter.project_slug }}"
version = "{{ cookiecutter.service_version }}"
description = "{{ cookiecutter.project_short_description }}"
authors = ["{{ cookiecutter.author_name }} <{{ cookiecutter.author_email }}>"]
readme = "README.md"
packages = [{include = "{{ cookiecutter.project_slug }}", from = "."}]

[tool.poetry.dependencies]
python = "^{{ cookiecutter.python_version }}"
fastapi = "^0.100.0"
uvicorn = "^0.20.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
```

#### README.md

```markdown
# {{ cookiecutter.project_name }}

{{ cookiecutter.project_short_description }}

## Getting Started

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run the service:
   ```bash
   midil launch --reload
   ```

3. Access the API:
   ```bash
   curl http://localhost:8000
   ```
```

## Template Customization

### Adding New Variables

1. **Update cookiecutter.json**:
   ```json
   {
       "new_variable": "default_value",
       "conditional_variable": "y"
   }
   ```

2. **Use in Templates**:
   ```python
   # In template files
   new_setting = "{{ cookiecutter.new_variable }}"
   ```

### Conditional Templates

Use Jinja2 conditionals for optional files:

```python
# In template files
{% if cookiecutter.include_docker == 'y' %}
# Dockerfile content
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
{% endif %}
```

### Custom Extensions

Create new Jinja2 extensions:

```python
class CustomExtension(Extension):
    tags = {"custom"}
    
    def parse(self, parser: Parser) -> nodes.Node:
        # Custom parsing logic
        pass
```

## Usage Examples

### Basic Template Usage

```python
from cookiecutter.main import cookiecutter

# Use template with default values
cookiecutter("path/to/template")

# Use template with custom values
cookiecutter(
    "path/to/template",
    extra_context={
        "project_name": "My Custom API",
        "include_docker": "y"
    }
)
```

### CLI Integration

```python
# In scaffolder
def scaffold(self, name: str) -> None:
    extra_context = self._get_extra_context(name)
    result = cookiecutter(
        str(self.template_dir),
        output_dir=str(services_dir),
        extra_context=extra_context,
        no_input=self.no_user_input,
        skip_if_file_exists=True,
    )
```

## Best Practices

### Template Design

- Use descriptive variable names
- Provide sensible defaults
- Include comprehensive documentation
- Test templates thoroughly

### Variable Naming

- Use snake_case for variable names
- Prefix private variables with underscore
- Use descriptive names that explain purpose

### File Organization

- Group related files together
- Use consistent naming conventions
- Include necessary configuration files
- Provide clear documentation

### Error Handling

- Validate template syntax
- Handle missing variables gracefully
- Provide meaningful error messages
- Test edge cases

## Troubleshooting

### Common Issues

1. **Template Syntax Errors**
   - Check Jinja2 syntax
   - Validate variable references
   - Test template rendering

2. **Missing Variables**
   - Ensure all variables are defined
   - Check variable names for typos
   - Provide default values

3. **File Generation Errors**
   - Check file permissions
   - Verify directory structure
   - Test post-generation hooks

### Debug Mode

```python
# Enable verbose output
cookiecutter(
    template_path,
    extra_context=context,
    no_input=False,  # Allow user input
    verbose=True     # Enable verbose output
)
```

<!-- source: midil-kit-main/midil/cli/core/templates/cookiecutter-midil-project/cookiecutter.json -->
<!-- source: midil-kit-main/midil/cli/core/templates/cookiecutter-midil-project/extensions.py -->
<!-- source: midil-kit-main/midil/cli/core/templates/cookiecutter-midil-project/hooks/post_gen_project.py -->
