---
slug: /cli/scaffolds
title: Project Scaffolds
description: Project scaffolding system for generating midil-kit project templates
---

# Project Scaffolds

The scaffolding system provides a flexible and extensible way to generate new midil-kit projects using Cookiecutter templates. It supports multiple project types and can be easily extended for custom project structures.

## Overview

The scaffolding system is built on:
- **Abstract Base Classes**: For consistent scaffolder interfaces
- **Factory Pattern**: For creating appropriate scaffolders
- **Cookiecutter Integration**: For template-based project generation
- **Post-Generation Hooks**: For project customization

## Base Scaffolder

### ProjectScaffolder Abstract Class

```python
from abc import ABC, abstractmethod

class ProjectScaffolder(ABC):
    """Abstract base class for project scaffolding."""
    
    @abstractmethod
    def scaffold(self, name: str) -> None:
        """Scaffold a new project with the given name."""
        pass
```

**Purpose**: Defines the contract for all scaffolder implementations.

**Usage**: Extend this class to create custom scaffolders for different project types.

## Scaffolder Factory

### ProjectScaffolderFactory

Factory class for creating appropriate scaffolders based on project type:

```python
class ProjectScaffolderFactory:
    @staticmethod
    def create(project_type: str = "fastapi") -> ProjectScaffolder:
        template_base = Path(__file__).parent.parent / "templates"
        if project_type == "fastapi":
            template_path = template_base / "cookiecutter-midil-project"
            return FastAPIServiceScaffolder(template_path, no_user_input=_NO_USER_INPUT)
        elif project_type == "lambda":
            template_path = template_base / "cookiecutter-midil-lambda"
            return LambdaFunctionScaffolder(template_path, no_user_input=_NO_USER_INPUT)
        else:
            raise ValueError(f"Unknown project type: {project_type}")
```

### Supported Project Types

| Type | Description | Status |
|------|-------------|--------|
| `fastapi` | FastAPI web service | ✅ Implemented |
| `lambda` | AWS Lambda function | 🚧 Planned |

## FastAPI Service Scaffolder

### FastAPIServiceScaffolder

Concrete scaffolder for FastAPI projects using Cookiecutter:

```python
class FastAPIServiceScaffolder(ProjectScaffolder):
    def __init__(self, template_dir: Path, no_user_input: bool = False):
        self.template_dir = template_dir
        self.no_user_input = no_user_input
```

### Key Methods

#### _get_extra_context()

```python
def _get_extra_context(self, name: str) -> Dict[str, Any]:
    return {
        "project_name": name.replace("_", " ").replace("-", " ").title(),
        "project_slug": name.lower().replace(" ", "-").replace("_", "_"),
    }
```

**Purpose**: Generates template variables from project name.

**Transformations**:
- `my-api` → `project_name: "My Api"`, `project_slug: "my-api"`
- `user_service` → `project_name: "User Service"`, `project_slug: "user_service"`

#### _ensure_services_dir()

```python
def _ensure_services_dir(self) -> Path:
    services_dir = Path.cwd() / "services"
    services_dir.mkdir(exist_ok=True)
    return services_dir
```

**Purpose**: Creates the `services/` directory if it doesn't exist.

**Behavior**: Creates directory with `exist_ok=True` to avoid errors.

#### scaffold()

```python
def scaffold(self, name: str) -> None:
    template_path = self.template_dir
    extra_context = self._get_extra_context(name)
    services_dir = _ensure_services_dir()
    
    try:
        result = cookiecutter(
            str(template_path),
            output_dir=str(services_dir),
            extra_context=extra_context,
            no_input=self.no_user_input,
            skip_if_file_exists=True,
        )
        # Success handling
    except Exception as e:
        # Error handling
        pass
```

**Purpose**: Executes the scaffolding process using Cookiecutter.

**Parameters**:
- `output_dir`: Where to create the project
- `extra_context`: Template variables
- `no_input`: Skip user prompts
- `skip_if_file_exists`: Don't overwrite existing files

## Lambda Function Scaffolder

### LambdaFunctionScaffolder

Concrete scaffolder for AWS Lambda functions:

```python
class LambdaFunctionScaffolder(ProjectScaffolder):
    def __init__(self, template_dir: Path, no_user_input: bool = False):
        self.template_dir = template_dir
        self.no_user_input = no_user_input
    
    def scaffold(self, name: str) -> None:
        # TODO: Implement lambda project scaffolding
        raise NotImplementedError("Lambda project scaffolding is not implemented yet")
```

**Status**: Currently not implemented, planned for future release.

## Template System

### Cookiecutter Integration

The scaffolding system uses Cookiecutter for template-based project generation:

```python
from cookiecutter.main import cookiecutter

result = cookiecutter(
    template_path,
    output_dir=output_directory,
    extra_context=template_variables,
    no_input=skip_prompts,
    skip_if_file_exists=True,
)
```

### Template Variables

Templates receive the following variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `project_name` | Human-readable project name | "My API" |
| `project_slug` | URL-safe project identifier | "my-api" |
| `project_short_description` | Brief project description | "A project created with MIDIL CLI" |
| `author_name` | Author name | "Your Name" |
| `author_email` | Author email | "your.email@example.com" |
| `service_version` | Initial version | "0.1.0" |
| `python_version` | Python version | "3.12" |
| `include_docker` | Docker support flag | "n" |

## Usage Examples

### Basic Scaffolding

```python
from midil.cli.core.scaffolds import scaffold_project

# Scaffold a FastAPI project
scaffold_project("my-api", "fastapi")
```

### Custom Scaffolder

```python
from midil.cli.core.scaffolds.factory import ProjectScaffolderFactory

# Create scaffolder for specific type
scaffolder = ProjectScaffolderFactory.create("fastapi")
scaffolder.scaffold("my-service")
```

### CLI Integration

```python
# In commands/init.py
@click.command("init")
@click.argument("name", required=False, default="midil-project")
@click.option("--type", type=click.Choice(["fastapi", "lambda"]), default="fastapi")
def init_command(name, type):
    scaffold_project(name, type)
```

## Error Handling

### Common Errors

1. **Template Not Found**
   ```python
   FileNotFoundError: Template directory not found
   ```

2. **Permission Denied**
   ```python
   PermissionError: Cannot create directory
   ```

3. **Cookiecutter Error**
   ```python
   Exception: Cookiecutter execution failed
   ```

### Error Handling Strategies

```python
def scaffold_with_error_handling(self, name: str) -> None:
    try:
        # Scaffolding logic
        result = cookiecutter(...)
        console.print(f"✅ Project scaffolded at {result}", style="green")
    except FileNotFoundError as e:
        console.print(f"❌ Template not found: {e}", style="red")
        sys.exit(1)
    except PermissionError as e:
        console.print(f"❌ Permission denied: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Failed to create project: {e}", style="red")
        sys.exit(1)
```

## Extensibility

### Creating Custom Scaffolders

```python
class CustomScaffolder(ProjectScaffolder):
    def __init__(self, template_dir: Path, no_user_input: bool = False):
        self.template_dir = template_dir
        self.no_user_input = no_user_input
    
    def scaffold(self, name: str) -> None:
        # Implement custom scaffolding logic
        pass
```

### Adding New Project Types

1. **Create Template Directory**:
   ```
   cli/core/templates/cookiecutter-my-project/
   ├── cookiecutter.json
   └── {{cookiecutter.project_slug}}/
       └── ...
   ```

2. **Implement Scaffolder**:
   ```python
   class MyProjectScaffolder(ProjectScaffolder):
       def scaffold(self, name: str) -> None:
           # Implementation
           pass
   ```

3. **Update Factory**:
   ```python
   def create(project_type: str) -> ProjectScaffolder:
       if project_type == "my-project":
           return MyProjectScaffolder(template_path)
       # ... existing types
   ```

## Best Practices

### Template Design

- Use descriptive variable names
- Provide sensible defaults
- Include comprehensive documentation
- Test templates thoroughly

### Error Handling

- Validate inputs before processing
- Provide meaningful error messages
- Handle file system errors gracefully
- Log errors appropriately

### Testing

```python
# Unit test example
def test_fastapi_scaffolder():
    scaffolder = FastAPIServiceScaffolder(template_dir, no_user_input=True)
    
    # Test context generation
    context = scaffolder._get_extra_context("my-api")
    assert context["project_name"] == "My Api"
    assert context["project_slug"] == "my-api"
```

## Troubleshooting

### Common Issues

1. **Template Not Found**
   - Verify template directory exists
   - Check template path configuration
   - Ensure template has proper structure

2. **Permission Errors**
   - Check write permissions in target directory
   - Ensure services directory is accessible
   - Verify user has necessary privileges

3. **Cookiecutter Errors**
   - Install cookiecutter: `pip install cookiecutter`
   - Check template syntax
   - Verify template variables

### Debug Mode

```python
# Enable verbose output
scaffolder = FastAPIServiceScaffolder(template_dir, no_user_input=False)
scaffolder.scaffold("my-api")
```

<!-- source: midil-kit-main/midil/cli/core/scaffolds/base.py -->
<!-- source: midil-kit-main/midil/cli/core/scaffolds/factory.py -->
<!-- source: midil-kit-main/midil/cli/core/scaffolds/fastapi.py -->
<!-- source: midil-kit-main/midil/cli/core/scaffolds/lambda_function.py -->
