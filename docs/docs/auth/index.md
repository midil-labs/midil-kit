---
slug: /auth
title: Authentication (auth)
description: Complete authentication and authorization module for midil-kit with Cognito integration
---

# Authentication (auth)

The `auth` module provides a comprehensive authentication and authorization system for midil-kit applications, with built-in support for AWS Cognito integration and extensible interfaces for custom authentication providers.

## Overview

The authentication module is designed around two core concepts:
- **Authentication (AuthN)**: Verifying user identity and acquiring access tokens
- **Authorization (AuthZ)**: Validating tokens and extracting user claims

The module provides both concrete implementations (Cognito) and abstract interfaces for building custom authentication solutions.

## File Tree

```
auth/
├── __init__.py                 # Main exports
├── config.py                   # Configuration models
├── exceptions.py               # Base exception classes
├── cognito/                    # AWS Cognito integration
│   ├── __init__.py
│   ├── client_credentials_flow.py  # OAuth2 client credentials flow
│   ├── jwt_authorizer.py           # JWT token validation
│   └── _exceptions.py              # Cognito-specific exceptions
└── interfaces/                 # Abstract interfaces
    ├── __init__.py
    ├── authenticator.py        # AuthN provider interface
    ├── authorizer.py           # AuthZ provider interface
    └── models.py               # Data models
```

## Quick Start

### Installation

The auth module is part of midil-kit. Install dependencies:

```bash
pip install midil-kit
# or with poetry
poetry add midil-kit
```

### Running Tests

```bash
# Run all auth tests
pytest tests/auth/

# Run specific test files
pytest tests/auth/cognito/test_client_credentials_flow.py
pytest tests/auth/cognito/test_jwt_authorizer.py
pytest tests/auth/interfaces/test_authenticator.py
```

## How-to Examples

### Validate a JWT Token

```python
from midil.auth.cognito import CognitoJWTAuthorizer

# Initialize the authorizer
authorizer = CognitoJWTAuthorizer(
    user_pool_id="us-east-1_ABC123DEF",
    region="us-east-1",
    audience="your-client-id"  # Optional
)

# Validate a token
try:
    claims = await authorizer.verify("your-jwt-token")
    print(f"User: {claims.sub}, Email: {claims.email}")
except CognitoAuthorizationError as e:
    print(f"Token validation failed: {e}")
```

### Get Outbound Authentication Token

```python
from midil.auth.cognito import CognitoClientCredentialsAuthenticator

# Initialize the authenticator
authenticator = CognitoClientCredentialsAuthenticator(
    client_id="your-client-id",
    client_secret="your-client-secret",
    token_url="https://your-domain.auth.region.amazoncognito.com/oauth2/token",
    scope="read write"  # Optional
)

# Get authentication headers for outbound requests
headers = await authenticator.get_headers()
# Use headers.authorization in your HTTP requests
```

## Contents

### [Cognito Integration](./cognito.md)
Complete AWS Cognito integration including:
- OAuth2 client credentials flow for service-to-service authentication
- JWT token validation with JWKS support
- Automatic token caching and refresh
- Comprehensive error handling

### [Auth Interfaces](./interfaces.md)
Abstract interfaces for building custom authentication:
- `AuthNProvider` for authentication implementations
- `AuthZProvider` for authorization implementations
- Data models for tokens and claims
- Extensible design patterns

### [Configuration](./config.md)
Configuration management with Pydantic models:
- Environment variable mapping
- Type validation and defaults
- Secret management integration

### [Exception Handling](./exceptions.md)
Comprehensive exception hierarchy:
- Base authentication and authorization errors
- Provider-specific exception classes
- HTTP status code mapping guidance

## Configuration Summary

The auth module uses Pydantic models for configuration. Map these fields to environment variables:

| Field | Environment Variable | Description | Required |
|-------|---------------------|-------------|----------|
| `user_pool_id` | `COGNITO_USER_POOL_ID` | Cognito User Pool ID | Yes |
| `client_id` | `COGNITO_CLIENT_ID` | Cognito App Client ID | Yes |
| `client_secret` | `COGNITO_CLIENT_SECRET` | App Client Secret | No* |
| `region` | `AWS_REGION` | AWS region | Yes |

*Required for client credentials flow

### Example Environment Configuration

```bash
# .env file
COGNITO_USER_POOL_ID=us-east-1_ABC123DEF
COGNITO_CLIENT_ID=your-client-id
COGNITO_CLIENT_SECRET=<REDACTED>
AWS_REGION=us-east-1
```

## Troubleshooting

### 1. Token Fetch Failures
- **Issue**: `CognitoAuthenticationError` when fetching tokens
- **Solutions**:
  - Verify client credentials are correct
  - Check network connectivity to Cognito
  - Ensure client has proper permissions in Cognito User Pool
  - Verify token URL format: `https://{domain}.auth.{region}.amazoncognito.com/oauth2/token`

### 2. JWT Validation Errors
- **Issue**: `CognitoAuthorizationError` during token validation
- **Solutions**:
  - Check token hasn't expired
  - Verify audience matches your client ID
  - Ensure issuer matches your Cognito User Pool
  - Check system clock synchronization (JWT uses UTC timestamps)

### 3. JWKS Key Fetching Issues
- **Issue**: Signing key retrieval failures
- **Solutions**:
  - Verify JWKS URL is accessible: `https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json`
  - Check network connectivity
  - Review AWS region configuration

## Security Notes

- **Token Storage**: Never store tokens in plain text. Use secure storage mechanisms.
- **Client Secrets**: Store client secrets in environment variables or secret managers (AWS Secrets Manager, Azure Key Vault).
- **HTTPS Only**: Always use HTTPS for token endpoints and JWKS URLs.
- **Token Expiration**: Implement proper token refresh logic to avoid expired token usage.
- **Audience Validation**: Always validate token audience to prevent token misuse.

## Maintainers

*Maintainer information to be added by repository owners*

## Missing/Ambiguous Info

The following information requires confirmation from repository maintainers:

1. **Exact CLI Commands**: No CLI commands found for auth module testing
2. **Example Token Formats**: Specific JWT token examples not found in codebase
3. **Secret Management**: Integration details with specific secret managers not documented
4. **Maintainer Contact**: GitHub handles or contact information not found
5. **Migration Guide**: No migration documentation found for version upgrades
6. **Performance Metrics**: No performance benchmarks or optimization guidelines found

<!-- source: midil-kit-main/midil/auth/__init__.py -->
<!-- source: midil-kit-main/midil/auth/config.py -->
<!-- source: midil-kit-main/midil/auth/exceptions.py -->
