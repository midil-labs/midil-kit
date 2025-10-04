# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v3.4.4 (2025-10-04)

### Improvement

- Allow passing host to midil launch


## v3.4.3 (2025-09-28)

### Improvement

- Fixed Logging configuration


## v3.4.2 (2025-09-28)

### Improvement

- Lazily import settings module in event_bus to avoid circular import


## v3.4.1 (2025-09-28)

### Improvement

- Improve CLI configuration
- Make settings access camel case


## v3.4.0 (2025-09-06)

### Improvement

- Enhanced the Event Bus to allow configuration of multiple consumers and producers, providing greater flexibility in event-driven workflows.


## Breaking Changes

- The event bus now requires producers and consumers to be specified as mappings (dictionaries). Providing a single producer or consumer directly will result in an exception.


## v3.3.0 (2025-09-06)

### Features

- Introduced a flexible settings configuration system that allows you to manage application settings directly through environment variables, making configuration and deployment more streamlined and environment-agnostic.

## Breaking Changes

- Remodeled Event Module


## v3.2.0 (2025-08-07)

### Features

- Added `MidilAPI`, a FastAPI-based wrapper that helps ensure your APIs follow Midil's design standards.

## Bug Fixes

- Resolved serialization errors in JSONAPI:Spec models

## Breaking Changes

- Renamed JSONAPI:Spec models to enforce semantic meaning
- Renamed `extensions` folder to midilapi after adapting FastAPI class partially for compliance


## v3.1.0 (2025-08-07)

### Features

- Introduced a command-line interface (CLI) for streamlined project scaffolding and management

### Improvements

- Renamed `CognitoClientCredentialsAuthClient` to `CognitoClientCredentialsAuthenticator`

## Bug Fixes

- Fixed parameter name mismatch in Async HTTP transport
- Fix Invalid Header Padding Error in Auth Middleware


## v3.0.0 (2025-08-05)

### Improvements

- Added `PatchResource` and `PostResource` to enforce complaince for Patch requests and Post requests specifications respectively

## Breaking Changes

- Renamed JSONAPI:Specs Objects to enforce consistency with naming conventions adopted in jsonapi.org
- Remove Support For `JSONAPIQueryParmas`
- Implementations of `BaseAuthMiddleware` raise HTTPException instead of returning a Response.


## v2.0.1 (2025-08-05)

### Bug Fixes

- Fixed missing authorization header issue in auth middleware


## v2.0.0 (2025-08-04)

### Features

- Add infrastructure packages (auth, http, event)
- Add extensions package with support for FastAPI

### Improvements

- Simplified JSONAPI Interface


## v1.0.4 (2025-07-13)

### Improvements

- Improved time complexity when accessing Query parameter fields
- Delegated Changelog management to towncrier


## v1.0.3 (2025-07-13)

### Bug Fixes

- Fixed bugs in Query Parameters parsing

### Improvements

- Improved makefile with build and push commands for PyPI deployment


## v1.0.2 (2025-07-13)

### Bug Fixes

- Fix Bugs in Body Parameters


## v1.0.1 (2025-07-13)

### Features

- Added CI scripts for releasing to PyPI (ci)
- Initialize project setup (jsonapi)
