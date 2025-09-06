# Midil Kit

A comprehensive Python SDK for backend systems development at [midil.io](https://midil.io). This library provides a rich set of tools for building modern, scalable backend applications with support for authentication, event handling, HTTP clients, and JSON:API compliance.

## ✨ Features

### 🔐 Authentication & Authorization
- **JWT Authorization**: Comprehensive JWT token verification and validation
- **AWS Cognito Integration**: Ready-to-use Cognito client credentials flow and JWT authorizer
- **Pluggable Auth Providers**: Abstract interfaces for custom authentication implementations
- **FastAPI Middleware**: Built-in authentication middleware for FastAPI applications

### 📡 Event System
- **Event Dispatching**: Abstract event dispatcher with polling and AWS integrations
- **SQS Consumer**: AWS SQS message consumption with automatic retry and context handling
- **Event Scheduling**: AWS EventBridge integration and periodic task scheduling
- **Event Context**: Distributed tracing and context management for events

### 🌐 HTTP Client
- **Enhanced HTTP Client**: HTTPX-based client with authentication integration
- **Retry Logic**: Configurable retry strategies with exponential backoff and jitter
- **Transport Layer**: Custom transport with comprehensive error handling
- **Auth Integration**: Seamless integration with authentication providers

### 📋 JSON:API Compliance
- **Document Creation**: Full JSON:API compliant document creation and validation
- **Resource Management**: Type-safe resource objects with relationships
- **Query Parameters**: Parsing and validation of JSON:API query parameters (sort, include, pagination)
- **Error Handling**: Standardized JSON:API error document creation

### 🚀 Framework Extensions
- **FastAPI Integration**: Authentication middleware and JSON:API dependencies
- **Type Safety**: Full type hints throughout with Pydantic models
- **Async Support**: Native async/await support across all components

## 📦 Installation

### Using Poetry (Recommended)

```bash
poetry add midil-kit
```

### Using pip

```bash
pip install midil-kit
```

### Optional Dependencies

The library supports optional feature sets through extras:

```bash
# Web framework extensions (FastAPI)
poetry add midil-kit[fastapi]

# Authentication providers (JWT, Cognito)
poetry add midil-kit[auth]

# AWS event services (SQS, EventBridge)
poetry add midil-kit[event]

# AWS infrastructure (auth + event)
poetry add midil-kit[aws]

# All optional dependencies
poetry add midil-kit[all]
```

## 🚀 Quick Start

### Authentication with Cognito

```python
from midil.auth.cognito import CognitoClientCredentialsAuthenticator, CognitoJWTAuthorizer

# Authentication client for outbound requests
auth_client = CognitoClientCredentialsAuthenticator(
    client_id="your-client-id",
    client_secret="your-client-secret",
    cognito_domain="your-domain.auth.region.amazoncognito.com"
)

# Get access token
token = await auth_client.get_token()
headers = await auth_client.get_headers()

# JWT authorizer for inbound requests
authorizer = CognitoJWTAuthorizer(
    user_pool_id="your-user-pool-id",
    region="us-east-1"
)

# Verify incoming token
claims = await authorizer.verify("jwt-token")
```

### Event System

```python
from midil.event.dispatchers.polling import PollingEventDispatcher
from midil.event.consumer.sqs import run_sqs_consumer
from midil.event.context import event_context

# Event dispatcher
dispatcher = PollingEventDispatcher()

# Register event handlers
@dispatcher.on("user.created")
async def handle_user_created(event: str, body: dict):
    print(f"User created: {body['user_id']}")

# Start event processing
await dispatcher.start_event_processor()

# Send events
await dispatcher.notify("user.created", {"user_id": "123"})

# SQS consumer
await run_sqs_consumer(
    queue_url="https://sqs.region.amazonaws.com/account/queue-name",
    region_name="us-east-1"
)
```

### HTTP Client with Authentication

```python
from midil.http import HttpClient
from midil.auth.cognito import CognitoClientCredentialsAuthenticator
from httpx import URL

# Create authenticated HTTP client
auth_client = CognitoClientCredentialsAuthenticator(...)
http_client = HttpClient(
    auth_client=auth_client,
    base_url=URL("https://api.example.com")
)

# Make authenticated requests
response = await http_client.send_request(
    method="POST",
    url="/users",
    data={"name": "John Doe"}
)
```

### JSON:API Documents

```python
from midil.jsonapi import Document, ResourceObject, ErrorObject

# Create a resource document
resource = ResourceObject(
    id="1",
    type="articles",
    attributes={"title": "JSON:API with Midil Kit", "content": "..."}
)

document = Document(data=resource)

# Create error documents
error = ErrorObject(
    status="422",
    title="Validation Error",
    detail="Title is required"
)

error_document = Document(errors=[error])
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from midil.midilapi.fastapi.middleware.auth_middleware import CognitoAuthMiddleware
from midil.midilapi.fastapi.dependencies.jsonapi import parse_sort, parse_include

app = FastAPI()

# Add authentication middleware
app.add_middleware(CognitoAuthMiddleware)

# JSON:API query parameter parsing
@app.get("/articles")
async def list_articles(
    sort=Depends(parse_sort),
    include=Depends(parse_include)
):
    return {"data": [], "meta": {"sort": sort, "include": include}}

# Access authenticated user
def get_auth(request):
    return request.state.auth

@app.get("/me")
async def get_current_user(auth=Depends(get_auth)):
    return {"user_id": auth.claims.sub}
```

## 📚 API Reference

### Authentication Module (`midil.auth`)

#### Core Interfaces
- `AuthNProvider`: Abstract authentication provider for outbound requests
- `AuthZProvider`: Abstract authorization provider for inbound token verification
- `AuthNToken`: Token model with expiration handling
- `AuthZTokenClaims`: Token claims model

#### Cognito Implementation
- `CognitoClientCredentialsAuthenticator`: OAuth2 client credentials flow
- `CognitoJWTAuthorizer`: JWT token verification for Cognito

### Event Module (`midil.event`)

#### Dispatchers
- `AbstractEventDispatcher`: Base event dispatcher with memory queue
- `PollingEventDispatcher`: In-memory event dispatcher with observer pattern

#### Consumers
- `SQSEventConsumer`: AWS SQS message consumer with retry logic

#### Schedulers
- `AWSEventBridgeClient`: EventBridge integration for scheduled events
- `PeriodicTask`: Periodic task execution with customizable strategies

#### Context Management
- `EventContext`: Event tracing and context management
- `event_context()`: Async context manager for event scoping

### HTTP Module (`midil.http`)

#### Client
- `HttpClient`: Enhanced HTTP client with auth integration
- `MidilAsyncClient`: Custom HTTPX client with retry transport

#### Retry System
- `RetryTransport`: Configurable retry transport layer
- `DefaultRetryStrategy`: Standard retry strategy implementation
- `ExponentialBackoffWithJitter`: Backoff strategy with jitter

### JSON:API Module (`midil.jsonapi`)

#### Document Models
- `Document`: Main document container
- `ResourceObject`: Resource representation with attributes and relationships
- `ErrorObject`: Error representation
- `QueryParams`: Query parameter parsing and validation

#### Utilities
- `Sort`, `Include`, `PaginationParams`: Query parameter models

### Extensions Module (`midil.midilapi`)

#### FastAPI Integration
- `BaseAuthMiddleware`: Base authentication middleware
- `CognitoAuthMiddleware`: Cognito-specific middleware
- `AuthContext`: Request authentication context
- `parse_sort()`, `parse_include()`: JSON:API query parameter dependencies

## 🛠️ Development

### Prerequisites

- Python 3.12+
- Poetry for dependency management

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd midil-kit
```

2. Install dependencies:
```bash
make install
```

3. Install pre-commit hooks:
```bash
make pre-commit-install
```

### Development Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Lint code
make lint

# Format code
make format

# Type checking
make type-check

# Run all checks
make check

# Clean build artifacts
make clean

# Build package
make build
```

### Changelog Management

The project uses [towncrier](https://towncrier.readthedocs.io/) for changelog management:

```bash
# Create a changelog entry
make changelog-draft

# Preview changelog changes
make changelog-preview

# Update changelog
make changelog

# Prepare a new release
make release
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=midil --cov-report=html

# Run specific test file
poetry run pytest tests/auth/test_cognito.py
```

### Code Quality

The project enforces code quality through:

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **Pre-commit hooks**: Automated quality checks

## 🏗️ Architecture

### Modular Design

Midil Kit follows a modular architecture:

```
midil/
├── auth/           # Authentication & authorization
├── event/          # Event system & messaging
├── http/           # HTTP client & retry logic
├── jsonapi/        # JSON:API compliance
└── extensions/     # Framework integrations
    └── fastapi/    # FastAPI-specific extensions
```

### Design Principles

- **Type Safety**: Comprehensive type hints using Pydantic models
- **Async First**: Native async/await support throughout
- **Pluggable**: Abstract interfaces for custom implementations
- **Framework Agnostic**: Core functionality independent of web frameworks
- **AWS Native**: First-class support for AWS services

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`make check`)
6. Create a changelog entry (`make changelog-draft`)
7. Commit your changes (`git commit -m 'feat: add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Commit Message Format

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

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
- `auth`: Authentication & authorization
- `event`: Event system
- `http`: HTTP client
- `jsonapi`: JSON:API functionality
- `extensions`: Framework extensions
- `docs`: Documentation
- `ci`: Continuous integration

**Examples:**
```
feat(auth): add support for refresh tokens
fix(event): resolve memory leak in event dispatcher
docs: update installation instructions
test(jsonapi): add tests for error document creation
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

### Recent Releases

- **v3.0.0** - Breaking changes with improved naming conventions and PATCH/POST resource compliance
- **v2.1.0** - Infrastructure packages, FastAPI extensions, and improved interfaces
- **v2.0.0** - Major architectural improvements with auth, http, and event modules

## 🆘 Support

- 📧 Email: [michael.armah@midil.io](mailto:michael.armah@midil.io)
- 🌐 Website: [midil.io](https://midil.io)
- 📚 Documentation: [Coming Soon]

---

Built with ❤️ by the [Midil.io](https://midil.io) team for the Python backend development community.
