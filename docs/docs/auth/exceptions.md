---
slug: /auth/exceptions
title: Auth exceptions
description: Exception hierarchy and error handling for the midil-kit authentication module
---

# Auth Exceptions

The auth module provides a comprehensive exception hierarchy for handling authentication and authorization errors with clear error types and HTTP status code mapping.

## Exception Hierarchy

The exception hierarchy follows a clear inheritance pattern:

```
BaseAuthError
├── AuthenticationError
│   └── CognitoAuthenticationError
└── AuthorizationError
    └── CognitoAuthorizationError
```

### BaseAuthError

The root exception class for all authentication and authorization errors.

```python
class BaseAuthError(Exception):
    """Base exception for all authentication and authorization errors."""
    pass
```

**Usage**:
```python
from midil.auth.exceptions import BaseAuthError 

try:
    # Some auth operation
    pass
except BaseAuthError as e:
    print(f"Authentication/Authorization error: {e}")
```

### AuthenticationError

Raised when authentication (verifying identity) fails.

```python
class AuthenticationError(BaseAuthError):
    """Exception raised when authentication fails."""
    pass
```

**Common Scenarios**:
- Invalid credentials
- Token acquisition failures
- Network errors during authentication
- Client configuration errors

**Usage**:
```python
from midil.auth.exceptions import AuthenticationError

try:
    token = await authenticator.get_token()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Handle authentication failure
```

### AuthorizationError

Raised when authorization (validating permissions) fails.

```python
class AuthorizationError(BaseAuthError):
    """Exception raised when authorization fails."""
    pass
```

**Common Scenarios**:
- Invalid or expired tokens
- Insufficient permissions
- Token validation failures
- JWT signature verification errors

**Usage**:
```python
from midil.auth.exceptions import AuthorizationError

try:
    claims = await authorizer.verify(token)
except AuthorizationError as e:
    print(f"Authorization failed: {e}")
    # Handle authorization failure
```

## Provider-Specific Exceptions

### CognitoAuthenticationError

Cognito-specific authentication errors.

```python
from midil.auth.cognito._exceptions import CognitoAuthenticationError

class CognitoAuthenticationError(AuthenticationError):
    """Exception raised when authentication with Cognito fails."""
    pass
```

**Common Scenarios**:
- Invalid client credentials
- Cognito service unavailable
- Network connectivity issues
- Invalid token endpoint

### CognitoAuthorizationError

Cognito-specific authorization errors.

```python
from midil.auth.cognito._exceptions import CognitoAuthorizationError

class CognitoAuthorizationError(AuthorizationError):
    """Exception raised when authorization with Cognito fails."""
    pass
```

**Common Scenarios**:
- Invalid JWT signature
- Expired tokens
- Invalid audience
- JWKS key fetch failures

## HTTP Status Code Mapping

### Suggested HTTP Status Mapping

| Exception Type | HTTP Status | Description |
|----------------|-------------|-------------|
| `AuthenticationError` | `401 Unauthorized` | Authentication failed |
| `AuthorizationError` | `403 Forbidden` | Authorization failed |
| `CognitoAuthenticationError` | `401 Unauthorized` | Cognito auth failed |
| `CognitoAuthorizationError` | `403 Forbidden` | Cognito authz failed |

### FastAPI Exception Handler Examples

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from midil.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CognitoAuthenticationError,
    CognitoAuthorizationError
)

app = FastAPI()

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={
            "error": "authentication_failed",
            "message": str(exc),
            "type": "AuthenticationError"
        }
    )

@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(
        status_code=403,
        content={
            "error": "authorization_failed",
            "message": str(exc),
            "type": "AuthorizationError"
        }
    )

@app.exception_handler(CognitoAuthenticationError)
async def cognito_auth_exception_handler(request: Request, exc: CognitoAuthenticationError):
    return JSONResponse(
        status_code=401,
        content={
            "error": "cognito_authentication_failed",
            "message": str(exc),
            "type": "CognitoAuthenticationError"
        }
    )

@app.exception_handler(CognitoAuthorizationError)
async def cognito_authz_exception_handler(request: Request, exc: CognitoAuthorizationError):
    return JSONResponse(
        status_code=403,
        content={
            "error": "cognito_authorization_failed",
            "message": str(exc),
            "type": "CognitoAuthorizationError"
        }
    )
```

### Django Exception Handling

```python
from django.http import JsonResponse
from midil.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CognitoAuthenticationError,
    CognitoAuthorizationError
)

def handle_auth_exceptions(get_response):
    def middleware(request):
        try:
            response = get_response(request)
            return response
        except AuthenticationError as e:
            return JsonResponse(
                {"error": "authentication_failed", "message": str(e)},
                status=401
            )
        except AuthorizationError as e:
            return JsonResponse(
                {"error": "authorization_failed", "message": str(e)},
                status=403
            )
        except CognitoAuthenticationError as e:
            return JsonResponse(
                {"error": "cognito_authentication_failed", "message": str(e)},
                status=401
            )
        except CognitoAuthorizationError as e:
            return JsonResponse(
                {"error": "cognito_authorization_failed", "message": str(e)},
                status=403
            )
    
    return middleware
```

## Mapping Provider-Specific Errors

### Cognito Error Mapping

```python
from midil.auth.cognito._exceptions import (
    CognitoAuthenticationError,
    CognitoAuthorizationError
)
from midil.auth.exceptions import AuthenticationError, AuthorizationError

def map_cognito_errors(func):
    """Decorator to map Cognito-specific errors to generic auth errors."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CognitoAuthenticationError as e:
            # Map to generic authentication error
            raise AuthenticationError(f"Cognito authentication failed: {e}") from e
        except CognitoAuthorizationError as e:
            # Map to generic authorization error
            raise AuthorizationError(f"Cognito authorization failed: {e}") from e
    
    return wrapper

# Usage
@map_cognito_errors
async def authenticate_user(token: str):
    # This will map Cognito errors to generic auth errors
    return await cognito_authorizer.verify(token)
```

### Custom Error Mapping

```python
from midil.auth.exceptions import AuthenticationError, AuthorizationError

class ErrorMapper:
    @staticmethod
    def map_http_error_to_auth_error(status_code: int, message: str):
        """Map HTTP status codes to appropriate auth exceptions."""
        if status_code == 401:
            return AuthenticationError(f"HTTP 401: {message}")
        elif status_code == 403:
            return AuthorizationError(f"HTTP 403: {message}")
        else:
            return AuthenticationError(f"HTTP {status_code}: {message}")
    
    @staticmethod
    def map_jwt_error_to_auth_error(jwt_error: Exception):
        """Map JWT library errors to auth exceptions."""
        if "expired" in str(jwt_error).lower():
            return AuthorizationError("Token has expired")
        elif "signature" in str(jwt_error).lower():
            return AuthorizationError("Invalid token signature")
        else:
            return AuthorizationError(f"JWT validation failed: {jwt_error}")
```

## Error Handling Best Practices

### Structured Error Responses

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AuthErrorResponse:
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

def create_error_response(exception: BaseAuthError) -> AuthErrorResponse:
    """Create a structured error response from an auth exception."""
    return AuthErrorResponse(
        error_code=exception.__class__.__name__,
        message=str(exception),
        timestamp=datetime.utcnow().isoformat()
    )
```

### Logging Integration

```python
import logging
from midil.auth.exceptions import BaseAuthError

logger = logging.getLogger(__name__)

def handle_auth_error(exception: BaseAuthError, context: Dict[str, Any] = None):
    """Handle auth errors with proper logging."""
    logger.error(
        f"Auth error: {exception}",
        extra={
            "error_type": exception.__class__.__name__,
            "context": context or {}
        }
    )
    
    # Log additional context for debugging
    if isinstance(exception, CognitoAuthenticationError):
        logger.debug("Cognito authentication error details", extra={"context": context})
    elif isinstance(exception, CognitoAuthorizationError):
        logger.debug("Cognito authorization error details", extra={"context": context})
```

### Retry Logic with Exceptions

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from midil.auth.exceptions import AuthenticationError, AuthorizationError

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(AuthenticationError)
)
async def authenticate_with_retry(authenticator, credentials):
    """Authenticate with retry logic for transient errors."""
    try:
        return await authenticator.get_token()
    except AuthenticationError as e:
        # Only retry on transient authentication errors
        if "network" in str(e).lower() or "timeout" in str(e).lower():
            raise  # Retry
        else:
            raise  # Don't retry on permanent errors
```

## Testing Exception Handling

### Unit Tests for Exceptions

```python
import pytest
from midil.auth.exceptions import (
    BaseAuthError,
    AuthenticationError,
    AuthorizationError
)

def test_exception_hierarchy():
    """Test that exception hierarchy is correct."""
    assert issubclass(AuthenticationError, BaseAuthError)
    assert issubclass(AuthorizationError, BaseAuthError)
    assert not issubclass(AuthenticationError, AuthorizationError)

def test_exception_instantiation():
    """Test that exceptions can be instantiated."""
    auth_error = AuthenticationError("Auth failed")
    authz_error = AuthorizationError("Authz failed")
    
    assert str(auth_error) == "Auth failed"
    assert str(authz_error) == "Authz failed"

def test_exception_chaining():
    """Test exception chaining."""
    original_error = ValueError("Original error")
    
    try:
        raise original_error
    except ValueError as e:
        auth_error = AuthenticationError("Auth failed") from e
        assert auth_error.__cause__ == original_error
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_cognito_error_mapping():
    """Test that Cognito errors are properly mapped."""
    from midil.auth.cognito import CognitoClientCredentialsAuthenticator
    from midil.auth.cognito._exceptions import CognitoAuthenticationError
    
    authenticator = CognitoClientCredentialsAuthenticator(
        client_id="invalid-id",
        client_secret="invalid-secret",
        token_url="https://invalid-url.com/token"
    )
    
    with pytest.raises(CognitoAuthenticationError):
        await authenticator.get_token()
```

<!-- source: midil-kit-main/midil/auth/exceptions.py -->
<!-- source: midil-kit-main/midil/auth/cognito/_exceptions.py -->
<!-- source: midil-kit-main/tests/auth/test_exceptions.py -->
