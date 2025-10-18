---
slug: /auth/config
title: Auth configuration
description: Configuration management for the midil-kit authentication module
---

# Auth Configuration

The auth module uses Pydantic models for type-safe configuration management with environment variable integration and validation.

## Pydantic Model Fields

### CognitoAuthConfig

The main configuration model for Cognito authentication:

```python
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, SecretStr

class CognitoAuthConfig(BaseModel):
    type: Literal["cognito"] = "cognito"
    user_pool_id: str = Field(..., description="Cognito User Pool ID")
    client_id: str = Field(..., description="Cognito App Client ID")
    client_secret: Optional[SecretStr] = Field(
        None, description="Cognito App Client Secret (optional)"
    )
    region: str = Field(..., description="AWS region for Cognito")

AuthConfig = Annotated[Union[CognitoAuthConfig], Field(discriminator="type")]
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `Literal["cognito"]` | Yes | Discriminator for auth type (defaults to "cognito") |
| `user_pool_id` | `str` | Yes | AWS Cognito User Pool identifier |
| `client_id` | `str` | Yes | Cognito App Client identifier |
| `client_secret` | `Optional[SecretStr]` | No | App Client secret (required for client credentials flow) |
| `region` | `str` | Yes | AWS region where Cognito is deployed |

## Environment Variable Mapping

### Recommended Environment Variables

```bash
# Required variables
COGNITO_USER_POOL_ID=us-east-1_ABC123DEF
COGNITO_CLIENT_ID=your-app-client-id
AWS_REGION=us-east-1

# Optional variables
COGNITO_CLIENT_SECRET=your-client-secret-here
```

### Environment Variable Loading

```python
import os
from midil.auth.config import CognitoAuthConfig

# Load configuration from environment
config = CognitoAuthConfig(
    user_pool_id=os.getenv("COGNITO_USER_POOL_ID"),
    client_id=os.getenv("COGNITO_CLIENT_ID"),
    client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
    region=os.getenv("AWS_REGION", "us-east-1")
)
```

### Using with Pydantic Settings

For automatic environment variable loading, integrate with Pydantic Settings:

```python
from pydantic import BaseSettings
from midil.auth.config import CognitoAuthConfig

class Settings(BaseSettings):
    cognito: CognitoAuthConfig
    
    class Config:
        env_nested_delimiter = "__"

# Load from environment with nested structure
settings = Settings()
cognito_config = settings.cognito
```

## Example .env Configuration

### Development Environment

```bash
# .env.development
COGNITO_USER_POOL_ID=us-east-1_ABC123DEF
COGNITO_CLIENT_ID=dev-app-client-id
COGNITO_CLIENT_SECRET=dev-client-secret-here
AWS_REGION=us-east-1
```

### Production Environment

```bash
# .env.production
COGNITO_USER_POOL_ID=us-east-1_PROD123ABC
COGNITO_CLIENT_ID=prod-app-client-id
COGNITO_CLIENT_SECRET=<REDACTED>
AWS_REGION=us-east-1
```

### Testing Environment

```bash
# .env.testing
COGNITO_USER_POOL_ID=us-east-1_TEST123DEF
COGNITO_CLIENT_ID=test-app-client-id
COGNITO_CLIENT_SECRET=test-client-secret
AWS_REGION=us-east-1
```

## Configuration Validation

### Type Validation

Pydantic automatically validates field types:

```python
from midil.auth.config import CognitoAuthConfig
from pydantic import ValidationError

try:
    config = CognitoAuthConfig(
        user_pool_id="us-east-1_ABC123DEF",
        client_id="valid-client-id",
        region="us-east-1"
    )
    print("Configuration is valid")
except ValidationError as e:
    print(f"Configuration validation failed: {e}")
```

### Required Field Validation

```python
# This will raise ValidationError
try:
    config = CognitoAuthConfig(
        client_id="valid-client-id"
        # Missing required fields: user_pool_id, region
    )
except ValidationError as e:
    print(f"Missing required fields: {e}")
```

### Secret String Handling

The `client_secret` field uses `SecretStr` for secure handling:

```python
from midil.auth.config import CognitoAuthConfig

config = CognitoAuthConfig(
    user_pool_id="us-east-1_ABC123DEF",
    client_id="valid-client-id",
    client_secret="secret-value",
    region="us-east-1"
)

# Access secret value
secret_value = config.client_secret.get_secret_value()
print(f"Secret: {secret_value}")

# Secret is not displayed in string representation
print(f"Config: {config}")  # client_secret will be hidden
```

## Deployment Notes

### Secret Management

For production deployments, use secure secret management:

#### AWS Secrets Manager

```python
import boto3
from midil.auth.config import CognitoAuthConfig

def load_config_from_secrets_manager(secret_name: str) -> CognitoAuthConfig:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    secret_data = json.loads(response['SecretString'])
    
    return CognitoAuthConfig(**secret_data)
```

#### Azure Key Vault

```python
from azure.keyvault.secrets import SecretClient
from midil.auth.config import CognitoAuthConfig

def load_config_from_key_vault(vault_url: str) -> CognitoAuthConfig:
    client = SecretClient(vault_url=vault_url, credential=credential)
    
    return CognitoAuthConfig(
        user_pool_id=client.get_secret("cognito-user-pool-id").value,
        client_id=client.get_secret("cognito-client-id").value,
        client_secret=client.get_secret("cognito-client-secret").value,
        region=client.get_secret("aws-region").value
    )
```

#### Environment-Specific Configuration

```python
import os
from midil.auth.config import CognitoAuthConfig

def get_auth_config() -> CognitoAuthConfig:
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Load from secret manager
        return load_config_from_secrets_manager("prod/cognito-config")
    elif environment == "staging":
        # Load from environment variables
        return CognitoAuthConfig(
            user_pool_id=os.getenv("COGNITO_USER_POOL_ID"),
            client_id=os.getenv("COGNITO_CLIENT_ID"),
            client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
            region=os.getenv("AWS_REGION")
        )
    else:
        # Development - load from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        return CognitoAuthConfig(
            user_pool_id=os.getenv("COGNITO_USER_POOL_ID"),
            client_id=os.getenv("COGNITO_CLIENT_ID"),
            client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
            region=os.getenv("AWS_REGION")
        )
```

### Configuration Caching

For high-performance applications, consider caching configuration:

```python
from functools import lru_cache
from midil.auth.config import CognitoAuthConfig

@lru_cache(maxsize=1)
def get_cached_auth_config() -> CognitoAuthConfig:
    """Cache configuration to avoid repeated loading."""
    return get_auth_config()

# Use cached configuration
config = get_cached_auth_config()
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from midil.auth.config import CognitoAuthConfig

app = FastAPI()

def get_auth_config() -> CognitoAuthConfig:
    return CognitoAuthConfig(
        user_pool_id=os.getenv("COGNITO_USER_POOL_ID"),
        client_id=os.getenv("COGNITO_CLIENT_ID"),
        client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
        region=os.getenv("AWS_REGION")
    )

@app.get("/")
async def root(auth_config: CognitoAuthConfig = Depends(get_auth_config)):
    return {"user_pool_id": auth_config.user_pool_id}
```

### Django Integration

```python
# settings.py
from midil.auth.config import CognitoAuthConfig

COGNITO_CONFIG = CognitoAuthConfig(
    user_pool_id=os.getenv("COGNITO_USER_POOL_ID"),
    client_id=os.getenv("COGNITO_CLIENT_ID"),
    client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
    region=os.getenv("AWS_REGION")
)
```

<!-- source: midil-kit-main/midil/auth/config.py -->
