# Midil Kit

A Python SDK for working with JSON:API specifications. This library provides a comprehensive set of tools for creating, validating, and manipulating JSON:API documents according to the [JSON:API specification](https://jsonapi.org/).

## Features

- **JSON:API Document Creation**: Easily create JSON:API compliant documents
- **Validation**: Built-in validation for JSON:API structures
- **Error Handling**: Comprehensive error document creation
- **Type Safety**: Full type hints and Pydantic models
- **Utility Functions**: Helper functions for common JSON:API operations

## Installation

### Using Poetry (Recommended)

```bash
poetry add midil-kit
```

### Using pip

```bash
pip install midil-kit
```

## Quick Start

```python
from jsonapi import (
    JSONAPIDocument,
    create_success_document,
    create_error_document,
    JSONAPIError
)

# Create a success document
data = {"id": "1", "type": "articles", "attributes": {"title": "JSON:API"}}
document = create_success_document(data)

# Create an error document
error = JSONAPIError(
    status="422",
    title="Validation Error",
    detail="The request was invalid"
)
error_document = create_error_document([error])

# Access document properties
print(document.jsonapi.version)  # "1.0"
print(document.data.attributes["title"])  # "JSON:API"
```

## Usage Examples

### Creating a Resource Document

```python
from jsonapi import JSONAPIDocument, ResourceObject

# Create a resource object
resource = ResourceObject(
    id="1",
    type="articles",
    attributes={"title": "JSON:API", "content": "A specification for APIs"}
)

# Create a document with the resource
document = JSONAPIDocument(data=resource)
```

### Working with Relationships

```python
from jsonapi import JSONAPIDocument, ResourceObject, Relationship

# Create related resources
author = ResourceObject(id="1", type="authors", attributes={"name": "John Doe"})
article = ResourceObject(
    id="1",
    type="articles",
    attributes={"title": "JSON:API"},
    relationships={
        "author": Relationship(data=author)
    }
)

document = JSONAPIDocument(data=article)
```

### Error Handling

```python
from jsonapi import create_error_document, JSONAPIError, ErrorSource

# Create detailed error
error = JSONAPIError(
    status="422",
    title="Validation Error",
    detail="The request was invalid",
    source=ErrorSource(pointer="/data/attributes/title")
)

error_document = create_error_document([error])
```

## API Reference

### Core Classes

- `JSONAPIDocument`: Main document class for JSON:API responses
- `ResourceObject`: Represents a JSON:API resource
- `JSONAPIError`: Represents an error in a JSON:API response
- `Relationship`: Represents relationships between resources

### Utility Functions

- `create_success_document()`: Create a success document with data
- `create_error_document()`: Create an error document
- `create_resource_identifier()`: Create a resource identifier object

## Development

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd midil-kit
```

2. Install dependencies:
```bash
poetry install
```

3. Install pre-commit hooks:
```bash
poetry run pre-commit install
```

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black .
poetry run isort .
```

### Type Checking

```bash
poetry run mypy .
```

### Changelog Management

The project includes automated changelog generation based on conventional commit messages.

**Preview changelog changes:**
```bash
make changelog-preview
```

**Update changelog with new commits:**
```bash
make changelog
```

**Create a new release:**
```bash
make create-release
```

**Bump version and prepare release:**
```bash
make release
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Commit Message Format

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. Please use the following format for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

**Scopes:**
- `jsonapi`: JSON:API core functionality
- `docs`: Documentation
- `ci`: Continuous integration
- `deps`: Dependencies

**Examples:**
```
feat(jsonapi): add support for sparse fieldsets
fix(jsonapi): resolve validation error in relationship serialization
docs: update README with usage examples
test: add tests for error document creation
chore: update dependencies
```

For breaking changes, start the commit body with `BREAKING CHANGE:`:
```
feat(jsonapi): remove deprecated ResourceObject constructor

BREAKING CHANGE: The ResourceObject constructor signature has changed
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0
- Initial release
- Basic JSON:API document creation and validation
- Error handling utilities
- Type-safe Pydantic models
