---
slug: /auth/cognito
title: Cognito integration
description: AWS Cognito authentication and authorization integration for midil-kit
---

# Cognito Integration

The Cognito integration provides complete AWS Cognito support for both authentication (acquiring tokens) and authorization (validating tokens) in midil-kit applications.

## Purpose

This module implements:
- **OAuth2 Client Credentials Flow**: For service-to-service authentication
- **JWT Token Validation**: Using Cognito's JWKS (JSON Web Key Set) endpoint
- **Automatic Token Caching**: With expiration handling and refresh logic
- **Comprehensive Error Handling**: With Cognito-specific exception types

## Public API

The following classes and functions are exported from `midil.auth.cognito`:

```python
from midil.auth.cognito import (
    CognitoClientCredentialsAuthenticator,  # For acquiring tokens
    CognitoJWTAuthorizer,                   # For validating tokens
    CognitoAuthenticationError,             # Auth-specific exceptions
    CognitoAuthorizationError,              # AuthZ-specific exceptions
)
```

## CognitoClientCredentialsAuthenticator

Implements the OAuth2 client credentials flow for acquiring access tokens from Cognito.

### Signature

```python
class CognitoClientCredentialsAuthenticator(AuthNProvider):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scope: Optional[str] = None,
    ):
        # ...
```

### Behavior

- **Token Caching**: Automatically caches tokens until expiration
- **Concurrent Safety**: Uses asyncio locks to prevent race conditions
- **Automatic Refresh**: Fetches new tokens when cached ones expire
- **Basic Authentication**: Uses client credentials for token requests

### Example Usage

```python
from midil.auth.cognito import CognitoClientCredentialsAuthenticator

# Initialize authenticator
authenticator = CognitoClientCredentialsAuthenticator(
    client_id="your-app-client-id",
    client_secret="your-app-client-secret",
    token_url="https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/token",
    scope="read write"  # Optional
)

# Get authentication token
token = await authenticator.get_token()
print(f"Access token: {token.token}")
print(f"Expires at: {token.expires_at_iso}")

# Get headers for HTTP requests
headers = await authenticator.get_headers()
print(f"Authorization: {headers.authorization}")
```

## CognitoJWTAuthorizer

Validates and decodes JWT tokens issued by AWS Cognito using the JWKS endpoint.

### Signature

```python
class CognitoJWTAuthorizer(AuthZProvider):
    def __init__(
        self, 
        user_pool_id: str, 
        region: str, 
        audience: Optional[str] = None
    ) -> None:
        # ...
```

### JWKS Behavior

- **Automatic Key Fetching**: Retrieves signing keys from Cognito's JWKS endpoint
- **Key Caching**: Caches keys for 15 minutes with automatic refresh
- **Retry Logic**: Automatically retries key fetching on failures
- **Concurrent Access**: Thread-safe key retrieval with asyncio locks

### Example Usage

```python
from midil.auth.cognito import CognitoJWTAuthorizer, CognitoAuthorizationError

# Initialize authorizer
authorizer = CognitoJWTAuthorizer(
    user_pool_id="us-east-1_ABC123DEF",
    region="us-east-1",
    audience="your-client-id"  # Optional, for audience validation
)

# Validate a JWT token
try:
    claims = await authorizer.verify("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")
    print(f"User ID: {claims.sub}")
    print(f"Email: {claims.email}")
    print(f"Name: {claims.name}")
    print(f"Expires: {claims.expires_at()}")
except CognitoAuthorizationError as e:
    print(f"Token validation failed: {e}")
```

## Cognito-Specific Exceptions

### CognitoAuthenticationError

Raised when authentication with Cognito fails:

```python
from midil.auth.cognito import CognitoAuthenticationError

try:
    token = await authenticator.get_token()
except CognitoAuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Handle authentication failure
```

### CognitoAuthorizationError

Raised when token validation fails:

```python
from midil.auth.cognito import CognitoAuthorizationError

try:
    claims = await authorizer.verify(token)
except CognitoAuthorizationError as e:
    print(f"Authorization failed: {e}")
    # Handle authorization failure
```

## Configuration and Environment Mapping

### Required Environment Variables

```bash
# Cognito User Pool Configuration
COGNITO_USER_POOL_ID=us-east-1_ABC123DEF
COGNITO_CLIENT_ID=your-app-client-id
AWS_REGION=us-east-1

# Optional: Client Secret (required for client credentials flow)
COGNITO_CLIENT_SECRET=<REDACTED>
```

### Example .env Configuration

```bash
# .env file for development
COGNITO_USER_POOL_ID=us-east-1_ABC123DEF
COGNITO_CLIENT_ID=your-app-client-id
COGNITO_CLIENT_SECRET=your-client-secret-here
AWS_REGION=us-east-1

# Token endpoint (constructed from domain)
COGNITO_DOMAIN=your-domain.auth.us-east-1.amazoncognito.com
```

### Configuration in Code

```python
import os
from midil.auth.cognito import CognitoClientCredentialsAuthenticator

# Load from environment
authenticator = CognitoClientCredentialsAuthenticator(
    client_id=os.getenv("COGNITO_CLIENT_ID"),
    client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
    token_url=f"https://{os.getenv('COGNITO_DOMAIN')}/oauth2/token",
    scope=os.getenv("COGNITO_SCOPE", "read write")
)
```

## Troubleshooting

### Token Fetch Issues

**Problem**: `CognitoAuthenticationError` when fetching tokens

**Solutions**:
1. Verify client credentials in Cognito User Pool
2. Check network connectivity to Cognito
3. Ensure proper IAM permissions for the client
4. Validate token URL format

```python
# Debug token fetch
try:
    token = await authenticator.get_token()
except CognitoAuthenticationError as e:
    print(f"Token fetch failed: {e}")
    # Check authenticator configuration
    print(f"Client ID: {authenticator.client_id}")
    print(f"Token URL: {authenticator.token_url}")
```

### JWKS Key Fetching Issues

**Problem**: Signing key retrieval failures

**Solutions**:
1. Verify JWKS URL accessibility
2. Check AWS region configuration
3. Ensure proper network connectivity

```python
# Debug JWKS URL
authorizer = CognitoJWTAuthorizer("us-east-1_ABC123DEF", "us-east-1")
print(f"JWKS URL: {authorizer.jwks_url}")
# Should be: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_ABC123DEF/.well-known/jwks.json
```

### Audience Validation Issues

**Problem**: Token validation fails due to audience mismatch

**Solutions**:
1. Ensure audience matches your client ID
2. Check Cognito User Pool audience configuration
3. Verify token was issued for the correct audience

```python
# Debug audience validation
authorizer = CognitoJWTAuthorizer(
    user_pool_id="us-east-1_ABC123DEF",
    region="us-east-1",
    audience="your-expected-client-id"  # Must match token audience
)
```

### Clock Skew Issues

**Problem**: Token validation fails due to time differences

**Solutions**:
1. Synchronize system clock with NTP
2. Check timezone configuration
3. Verify JWT `iat` and `exp` claims

```python
import datetime
from datetime import timezone

# Check system time
now = datetime.datetime.now(timezone.utc)
print(f"System time (UTC): {now.isoformat()}")

# Check token expiration
if claims.expires_at():
    print(f"Token expires: {claims.expires_at().isoformat()}")
    print(f"Time until expiry: {claims.expires_at() - now}")
```

## Where to Look in Code

### Source Comments

Key implementation details can be found in:

- **Token Caching Logic**: `client_credentials_flow.py:31-49` <!-- source: midil-kit-main/midil/auth/cognito/client_credentials_flow.py:31-49 -->
- **JWKS Key Fetching**: `jwt_authorizer.py:64-87` <!-- source: midil-kit-main/midil/auth/cognito/jwt_authorizer.py:64-87 -->
- **JWT Validation Options**: `jwt_authorizer.py:101-113` <!-- source: midil-kit-main/midil/auth/cognito/jwt_authorizer.py:101-113 -->
- **Error Handling**: `jwt_authorizer.py:119-129` <!-- source: midil-kit-main/midil/auth/cognito/jwt_authorizer.py:119-129 -->

### Test Files

Comprehensive test coverage available in:
- `tests/auth/cognito/test_client_credentials_flow.py`
- `tests/auth/cognito/test_jwt_authorizer.py`
- `tests/auth/cognito/test_exceptions.py`

<!-- source: midil-kit-main/midil/auth/cognito/__init__.py -->
<!-- source: midil-kit-main/midil/auth/cognito/client_credentials_flow.py -->
<!-- source: midil-kit-main/midil/auth/cognito/jwt_authorizer.py -->
<!-- source: midil-kit-main/midil/auth/cognito/_exceptions.py -->
