---
sidebar_position: 2
title: Getting Started
description: Installation, setup, and first steps with Midil Kit
---

# Getting Started

This guide will help you get up and running with Midil Kit quickly. We'll cover installation, basic setup, and walk through a simple example.

## Prerequisites

- **Python 3.12+** (Python 3.13 is also supported)
- **Poetry** (recommended) or **pip** for dependency management
- Basic knowledge of **async/await** in Python
- Familiarity with **FastAPI** (optional, for web framework integration)

## Installation

### Using Poetry (Recommended)

```bash
poetry add midil-kit
```

### Using pip

```bash
pip install midil-kit
```

### Optional Dependencies

Midil Kit supports optional feature sets through extras:

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

## Basic Setup

### 1. Environment Configuration

Create a `.env` file in your project root:

```env
# AWS Configuration (if using AWS services)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Cognito Configuration (if using Cognito)
COGNITO_USER_POOL_ID=us-east-1_abcd1234
COGNITO_CLIENT_ID=your-client-id
COGNITO_CLIENT_SECRET=your-client-secret
COGNITO_DOMAIN=your-domain.auth.us-east-1.amazoncognito.com
```

### 2. Basic Project Structure

```
your-project/
├── main.py
├── .env
├── requirements.txt  # or pyproject.toml
└── src/
    ├── auth/
    ├── events/
    └── api/
```

## Quick Start Example

Let's build a simple authenticated API client using Midil Kit:

### Step 1: Authentication Setup

```python title="src/auth/setup.py"
from midil.auth.cognito import (
    CognitoClientCredentialsAuthenticator,
    CognitoJWTAuthorizer
)

# For outbound requests (your service calling other APIs)
auth_client = CognitoClientCredentialsAuthenticator(
    client_id="your-client-id",
    client_secret="your-client-secret",
    cognito_domain="your-domain.auth.us-east-1.amazoncognito.com"
)

# For inbound requests (validating tokens in your API)
jwt_authorizer = CognitoJWTAuthorizer(
    user_pool_id="us-east-1_abcd1234",
    region="us-east-1"
)
```

### Step 2: HTTP Client with Authentication

```python title="src/api/client.py"
from midil.http_client import HttpClient
from httpx import URL
import asyncio

async def main():
    # Create authenticated HTTP client
    http_client = HttpClient(
        auth_client=auth_client,  # from previous step
        base_url=URL("https://api.example.com")
    )

    # Make authenticated requests
    try:
        # GET request
        users_response = await http_client.send_request(
            method="GET",
            url="/users",
            params={"limit": 10}
        )
        print(f"Users: {users_response.json()}")

        # POST request
        create_response = await http_client.send_request(
            method="POST",
            url="/users",
            data={
                "name": "John Doe",
                "email": "john@example.com"
            }
        )
        print(f"Created user: {create_response.json()}")

    finally:
        await http_client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Event System Setup

```python title="src/events/setup.py"
from midil.event import EventBus, SQSProducer, SQSConsumer
from midil.event.context import event_context

# Set up event bus
event_bus = EventBus()

# Set up SQS producer
producer = SQSProducer(
    queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
    region_name="us-east-1"
)

# Register event handlers
@event_bus.subscriber("user.created")
async def handle_user_created(event_data: dict):
    async with event_context(event_type="user.created", data=event_data):
        print(f"Processing user creation: {event_data}")
        # Send welcome email, create profile, etc.

@event_bus.subscriber("user.updated")
async def handle_user_updated(event_data: dict):
    async with event_context(event_type="user.updated", data=event_data):
        print(f"Processing user update: {event_data}")
        # Update cache, sync with external systems, etc.

# Produce events
async def create_user_event(user_data: dict):
    await producer.publish("user.created", user_data)
```

### Step 4: FastAPI Integration

```python title="main.py"
from fastapi import FastAPI, Depends, HTTPException
from midil.midilapi.middleware.auth_middleware import CognitoAuthMiddleware
from midil.midilapi.dependencies.jsonapi import parse_sort, parse_include
from midil.jsonapi import Document, ResourceObject
from pydantic import BaseModel

app = FastAPI(title="My API with Midil Kit")

# Add authentication middleware
app.add_middleware(
    CognitoAuthMiddleware,
    user_pool_id="us-east-1_abcd1234",
    region="us-east-1"
)

class UserCreate(BaseModel):
    name: str
    email: str

# Dependency to get authenticated user
def get_current_user(request):
    if not hasattr(request.state, 'auth'):
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.auth

@app.get("/users")
async def list_users(
    sort=Depends(parse_sort),
    include=Depends(parse_include),
    current_user=Depends(get_current_user)
):
    """List users with JSON:API query parameters"""
    # Fetch users from database
    users_data = [
        {"id": "1", "name": "Alice", "email": "alice@example.com"},
        {"id": "2", "name": "Bob", "email": "bob@example.com"},
    ]

    # Create JSON:API document
    resources = [
        ResourceObject(
            id=user["id"],
            type="users",
            attributes={
                "name": user["name"],
                "email": user["email"]
            }
        )
        for user in users_data
    ]

    document = Document(data=resources)
    return document

@app.post("/users")
async def create_user(
    user_data: UserCreate,
    current_user=Depends(get_current_user)
):
    """Create a new user"""
    # Create user in database
    new_user_id = "123"  # Generated ID

    # Emit event
    await event_bus.publish("user.created", {
        "user_id": new_user_id,
        "name": user_data.name,
        "email": user_data.email,
        "created_by": current_user.claims.sub
    })

    # Return JSON:API response
    resource = ResourceObject(
        id=new_user_id,
        type="users",
        attributes=user_data.dict()
    )

    return Document(data=resource)

@app.get("/me")
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current authenticated user info"""
    return {
        "user_id": current_user.claims.sub,
        "email": current_user.claims.email,
        "groups": current_user.claims.get("cognito:groups", [])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Running Your Application

### 1. Start the FastAPI server

```bash
python main.py
```

or with uvicorn directly:

```bash
uvicorn main:app --reload
```

### 2. Test the API

```bash
# Get an access token (if using Cognito)
TOKEN=$(curl -X POST https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET" \
  | jq -r '.access_token')

# Make authenticated requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/users
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/me
```

## Configuration Options

### Environment Variables

Midil Kit supports configuration through environment variables:

```python title="config.py"
from midil.settings import MidilSettings

# Load settings from environment
settings = MidilSettings()

print(f"AWS Region: {settings.aws_region}")
print(f"Cognito User Pool: {settings.cognito_user_pool_id}")
```

### Custom Configuration

```python title="custom_config.py"
from midil.auth.cognito import CognitoClientCredentialsAuthenticator
from midil.http_client.overrides.retry.strategies import DefaultRetryStrategy
from midil.http_client import HttpClient
from httpx import URL

# Custom retry configuration
custom_retry_strategy = DefaultRetryStrategy(
    max_attempts=5,
    backoff_factor=2.0,
    max_backoff=30.0
)

# HTTP client with custom retry
http_client = HttpClient(
    auth_client=auth_client,
    base_url=URL("https://api.example.com"),
    retry_strategy=custom_retry_strategy
)
```

## Next Steps

Now that you have Midil Kit set up, explore the detailed documentation for each module:

- [**Authentication Module**](./auth/overview) - Learn about authentication patterns and providers
- [**Event System**](./event/overview) - Understand event-driven architecture with Midil Kit
- [**HTTP Client**](./http/overview) - Master HTTP client capabilities and retry strategies
- [**JSON:API**](./jsonapi/overview) - Build JSON:API compliant APIs
- [**FastAPI Extensions**](./extensions/overview) - Integrate with FastAPI applications

## Common Patterns

### Error Handling

```python
from midil.auth.exceptions import AuthenticationError
from midil.http_client.overrides.retry.strategies import RetryExhaustedException

try:
    response = await http_client.send_request("GET", "/protected-resource")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RetryExhaustedException as e:
    print(f"Request failed after retries: {e}")
```

### Dependency Injection

```python
from typing import Protocol

class UserService(Protocol):
    async def create_user(self, user_data: dict) -> dict: ...

class DatabaseUserService:
    async def create_user(self, user_data: dict) -> dict:
        # Implementation
        pass

# Use dependency injection in FastAPI
app.dependency_overrides[UserService] = DatabaseUserService
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you've installed the correct extras for the features you're using
2. **Authentication Failures**: Verify your Cognito configuration and credentials
3. **Async Context Issues**: Ensure you're using `async`/`await` properly throughout your application

### Getting Help

- Check the [API Reference](./auth/overview) for detailed documentation
- Look at [Examples](./auth/examples) for common use cases
- Open an [issue on GitHub](https://github.com/midil-labs/midil-kit/issues) for bugs or feature requests

Ready to dive deeper? Let's explore the [Authentication Module](./auth/overview) next!
