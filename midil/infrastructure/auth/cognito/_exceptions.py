from midil.infrastructure.auth.exceptions import AuthenticationError, AuthorizationError


class CognitoAuthenticationError(AuthenticationError):
    ...


class CognitoAuthorizationError(AuthorizationError):
    ...
