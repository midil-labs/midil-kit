class BaseAuthError(Exception):
    """Base exception for all authentication and authorization errors."""

    ...


class AuthenticationError(BaseAuthError):
    """Exception raised when authentication fails."""

    ...


class AuthorizationError(BaseAuthError):
    """Exception raised when authorization fails."""

    ...
