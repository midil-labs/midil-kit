class BaseAuthError(Exception):
    ...


class AuthenticationError(BaseAuthError):
    ...


class AuthorizationError(BaseAuthError):
    ...
