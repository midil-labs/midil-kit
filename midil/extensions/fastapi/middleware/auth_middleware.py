from typing import Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from midil.infrastructure.auth.interfaces.authorizer import (
    AuthZTokenClaims,
)
from midil.infrastructure.auth.cognito.jwt_authorizer import CognitoJWTAuthorizer
import os


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


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract auth headers from request and store them in the request state.

    Usage:

        def get_auth(request: Request) -> AuthContext:
            return request.state.auth

        @app.get("/me")
        def me(auth: AuthContext = Depends(get_auth)):
            return auth.to_dict()

        # as middleware
        app.add_middleware(AuthMiddleware)

    Example:

        curl -H "x-user-sub: 123" -H "x-user-email: test@test.com" -H "x-user-name: John Doe" http://localhost:8000/me

    """

    async def dispatch(self, request: Request, call_next):
        token = request.headers["authorization"]

        authorizer = CognitoJWTAuthorizer(
            user_pool_id=os.getenv("COGNITO_USER_POOL_ID", ""),
            region=os.getenv("AWS_REGION", ""),
        )
        claims = await authorizer.verify(token)

        request.state.auth = AuthContext(
            claims=claims,
            _raw_headers=dict(request.headers),
        )
        response = await call_next(request)
        return response
