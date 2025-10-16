---
slug: /auth/interfaces
title: Auth interfaces
description: Abstract interfaces for authentication and authorization in midil-kit
---

# Auth Interfaces

The interfaces module provides abstract base classes and data models for building custom authentication and authorization solutions in midil-kit applications.

## Purpose

This module defines the core contracts for:
- **Authentication Providers**: For acquiring and managing access tokens
- **Authorization Providers**: For validating and decoding tokens
- **Data Models**: Standardized token and claim representations
- **Extensibility**: Clean abstractions for custom implementations

## File Tree

```
interfaces/
├── __init__.py          # Main exports
├── authenticator.py     # AuthN provider interface
├── authorizer.py        # AuthZ provider interface
└── models.py            # Data models and mixins
```

## AuthNProvider and AuthZProvider

### AuthNProvider Interface

Abstract base class for authentication clients that acquire and manage access tokens.

```python
from abc import ABC, abstractmethod
from midil.auth.interfaces.models import AuthNToken, AuthNHeaders

class AuthNProvider(ABC):
    """Abstract base class for authentication clients that acquire and manage access tokens."""
    
    @abstractmethod
    async def get_token(self) -> AuthNToken:
        """Acquire a new access token from the authentication provider."""
        pass

    @abstractmethod
    async def get_headers(self) -> AuthNHeaders:
        """Return authentication headers suitable for making authorized HTTP requests."""
        pass
```

### AuthZProvider Interface

Abstract base class for authorization providers that validate and decode tokens.

```python
from abc import ABC, abstractmethod
from midil.auth.interfaces.models import AuthZTokenClaims

class AuthZProvider(ABC):
    """Abstract base class for authentication authorizers that validate and decode tokens."""
    
    @abstractmethod
    async def verify(self, token: str) -> AuthZTokenClaims:
        """Validate and decode a token, returning the claims."""
        pass
```

### Usage Examples

#### Custom Authentication Provider

```python
from midil.auth.interfaces import AuthNProvider
from midil.auth.interfaces.models import AuthNToken, AuthNHeaders

class CustomAuthProvider(AuthNProvider):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    async def get_token(self) -> AuthNToken:
        # Implement your custom token acquisition logic
        response = await self._make_request("/auth/token")
        return AuthNToken(
            token=response["access_token"],
            expires_at_iso=response["expires_at"]
        )
    
    async def get_headers(self) -> AuthNHeaders:
        token = await self.get_token()
        return AuthNHeaders(
            authorization=f"Bearer {token.token}",
            content_type="application/json"
        )
```

#### Custom Authorization Provider

```python
from midil.auth.interfaces import AuthZProvider
from midil.auth.interfaces.models import AuthZTokenClaims

class CustomAuthZProvider(AuthZProvider):
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    async def verify(self, token: str) -> AuthZTokenClaims:
        # Implement your custom token validation logic
        decoded = self._decode_token(token)
        return AuthZTokenClaims(
            token=token,
            sub=decoded["sub"],
            exp=decoded["exp"]
        )
```

## Models

### AuthNToken

Represents an authentication token with expiration handling.

```python
class AuthNToken(ExpirableTokenMixin):
    expires_at_iso: Optional[str] = None
    
    def expires_at(self) -> Optional[datetime]:
        return isoparse(self.expires_at_iso) if self.expires_at_iso else None
```

**Usage Example**:
```python
from midil.auth.interfaces.models import AuthNToken
from datetime import datetime, timezone, timedelta

# Create a token with expiration
token = AuthNToken(
    token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    expires_at_iso=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
)

# Check if token is expired
if token.expired:
    print("Token has expired")
else:
    print(f"Token expires at: {token.expires_at()}")
```

### AuthNHeaders

Standardized authentication headers for HTTP requests.

```python
class AuthNHeaders(BaseModel):
    authorization: str = Field(..., alias="Authorization")
    accept: str = Field(default="application/json", alias="Accept")
    content_type: str = Field(default="application/json", alias="Content-Type")
```

**Usage Example**:
```python
from midil.auth.interfaces.models import AuthNHeaders

# Create headers for API request
headers = AuthNHeaders(
    authorization="Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    content_type="application/json"
)

# Use in HTTP request
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://api.example.com/data",
        headers=headers.dict(by_alias=True)
    )
```

### AuthZTokenClaims

Base model for token claims with expiration handling.

```python
class AuthZTokenClaims(ExpirableTokenMixin):
    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp (epoch)
    
    def expires_at(self) -> datetime:
        return datetime.fromtimestamp(self.exp, tz=timezone.utc)
```

**Usage Example**:
```python
from midil.auth.interfaces.models import AuthZTokenClaims
from datetime import datetime, timezone

# Create claims from decoded JWT
claims = AuthZTokenClaims(
    token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    sub="user123",
    exp=int(datetime.now(timezone.utc).timestamp()) + 3600
)

# Access user information
print(f"User ID: {claims.sub}")
print(f"Expires at: {claims.expires_at()}")
print(f"Is expired: {claims.expired}")
```

### ExpirableTokenMixin

Mixin providing expiration logic for tokens.

```python
class ExpirableTokenMixin(BaseModel):
    _time_buffer: timedelta = PrivateAttr(default_factory=lambda: timedelta(minutes=5))
    token: str
    refresh_token: Optional[str] = None
    
    def expires_at(self) -> Optional[datetime]:
        raise NotImplementedError("Subclasses must implement expires_at()")
    
    @property
    def expired(self) -> bool:
        # Returns True if token is expired (with 5-minute buffer)
        pass
    
    @property
    def should_refresh(self) -> bool:
        # Returns True if token should be refreshed
        pass
```

## Testing Tips for Interfaces

### Mock Implementations

Create mock implementations for testing:

```python
from unittest.mock import AsyncMock
from midil.auth.interfaces import AuthNProvider, AuthZProvider
from midil.auth.interfaces.models import AuthNToken, AuthZTokenClaims

class MockAuthNProvider(AuthNProvider):
    def __init__(self, token_value: str = "mock-token"):
        self.token_value = token_value
    
    async def get_token(self) -> AuthNToken:
        return AuthNToken(token=self.token_value)
    
    async def get_headers(self) -> AuthNHeaders:
        return AuthNHeaders(authorization=f"Bearer {self.token_value}")

class MockAuthZProvider(AuthZProvider):
    def __init__(self, should_validate: bool = True):
        self.should_validate = should_validate
    
    async def verify(self, token: str) -> AuthZTokenClaims:
        if not self.should_validate:
            raise ValueError("Invalid token")
        
        return AuthZTokenClaims(
            token=token,
            sub="test-user",
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600
        )
```

### Testing Custom Implementations

```python
import pytest
from midil.auth.interfaces import AuthNProvider, AuthZProvider

@pytest.mark.asyncio
async def test_custom_auth_provider():
    provider = CustomAuthProvider("api-key", "https://api.example.com")
    
    # Test token acquisition
    token = await provider.get_token()
    assert isinstance(token, AuthNToken)
    assert token.token is not None
    
    # Test header generation
    headers = await provider.get_headers()
    assert headers.authorization.startswith("Bearer ")

@pytest.mark.asyncio
async def test_custom_authz_provider():
    provider = CustomAuthZProvider("secret-key")
    
    # Test valid token
    claims = await provider.verify("valid-token")
    assert isinstance(claims, AuthZTokenClaims)
    assert claims.sub == "test-user"
    
    # Test invalid token
    with pytest.raises(ValueError):
        await provider.verify("invalid-token")
```

## Where to Look in Code

### Source Comments

Key implementation details can be found in:

- **AuthNProvider Interface**: `authenticator.py:5-42` <!-- source: midil-kit-main/midil/auth/interfaces/authenticator.py:5-42 -->
- **AuthZProvider Interface**: `authorizer.py:5-21` <!-- source: midil-kit-main/midil/auth/interfaces/authorizer.py:5-21 -->
- **ExpirableTokenMixin**: `models.py:7-25` <!-- source: midil-kit-main/midil/auth/interfaces/models.py:7-25 -->
- **AuthNToken Implementation**: `models.py:27-32` <!-- source: midil-kit-main/midil/auth/interfaces/models.py:27-32 -->
- **AuthZTokenClaims Implementation**: `models.py:45-51` <!-- source: midil-kit-main/midil/auth/interfaces/models.py:45-51 -->

### Test Files

Comprehensive test coverage available in:
- `tests/auth/interfaces/test_authenticator.py`
- `tests/auth/interfaces/test_authorizer.py`
- `tests/auth/interfaces/test_models.py`

## Missing Info

The following information requires clarification:

1. **Custom Provider Examples**: No concrete examples of custom implementations found in codebase
2. **Interface Versioning**: No versioning strategy documented for interface changes
3. **Performance Guidelines**: No performance recommendations for custom implementations
4. **Error Handling Patterns**: No standardized error handling patterns for custom providers
5. **Configuration Integration**: No guidance on integrating custom providers with configuration system

<!-- source: midil-kit-main/midil/auth/interfaces/__init__.py -->
<!-- source: midil-kit-main/midil/auth/interfaces/authenticator.py -->
<!-- source: midil-kit-main/midil/auth/interfaces/authorizer.py -->
<!-- source: midil-kit-main/midil/auth/interfaces/models.py -->
