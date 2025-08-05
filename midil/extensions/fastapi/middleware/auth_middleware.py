from typing import Dict, Any, Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from midil.auth.interfaces.authorizer import AuthZProvider
from midil.auth.interfaces.models import AuthZTokenClaims
from midil.auth.cognito.jwt_authorizer import CognitoJWTAuthorizer
import os

from starlette.responses import Response


class AuthContext:
    def __init__(
        self,
        claims: AuthZTokenClaims,
        _raw_headers: Dict[str, Any],
    ) -> None:
        self.claims = claims
        self._raw_headers = _raw_headers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claims": self.claims.model_dump(),
            "raw_headers": self._raw_headers,
        }


class BaseAuthMiddleware(BaseHTTPMiddleware):
    """
    Base middleware for extracting authentication headers from the request and storing
    authentication context in the request state.

    Subclass this middleware and implement the `authorizer` method to provide a concrete
    AuthZProvider (e.g., CognitoJWTAuthorizer).

    Usage Example:

        def get_auth(request: Request) -> AuthContext:
            return request.state.auth

        @app.get("/me")
        def me(auth: AuthContext = Depends(get_auth)):
            return auth.to_dict()

        # Add as middleware
        app.add_middleware(CognitoAuthMiddleware)

    After authentication, the request's state will have an `auth` attribute containing
    an AuthContext instance with the decoded claims and raw headers.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if "authorization" not in request.headers:
            return Response(
                content="Authorization header is missing",
                status_code=401,
            )
        token = request.headers["authorization"]

        authorizer = await self.authorizer(request)
        claims = await authorizer.verify(token)

        request.state.auth = AuthContext(
            claims=claims,
            _raw_headers=dict(request.headers),
        )
        response = await call_next(request)
        return response

    async def authorizer(self, request: Request) -> AuthZProvider:
        """
        Authorizer is a class that verifies and decodes a JWT token.
        """
        raise NotImplementedError("Authorizer not implemented")


class CognitoAuthMiddleware(BaseAuthMiddleware):
    """
    Middleware to extract cognitoauth headers from request and store them in the request state.

    Usage:

        def get_auth(request: Request) -> AuthContext:
            return request.state.auth

        @app.get("/me")
        def me(auth: AuthContext = Depends(get_auth)):
            return auth.to_dict()

        # as middleware
        app.add_middleware(CognitoAuthMiddleware)

    """

    async def authorizer(self, request: Request) -> AuthZProvider:
        return CognitoJWTAuthorizer(
            user_pool_id=os.getenv("COGNITO_USER_POOL_ID", ""),
            region=os.getenv("AWS_REGION", ""),
        )
