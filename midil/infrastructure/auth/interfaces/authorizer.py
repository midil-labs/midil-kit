from abc import ABC, abstractmethod
from datetime import datetime, timezone
from midil.infrastructure.auth.interfaces.models import ExpirableTokenMixin


class AuthZTokenClaims(ExpirableTokenMixin):
    sub: str
    exp: int  # epoch

    def expires_at(self) -> datetime:
        return datetime.fromtimestamp(self.exp, tz=timezone.utc)


class AuthZProvider(ABC):
    """
    Abstract base class for authentication authorizers that validate and decode tokens.

    Usecase: For decoding and verifying incoming tokens.

    Implementations of this class should provide methods to:
    - Validate and decode a token from an authentication provider (e.g., OAuth2, Cognito, etc.).
    - Return the claims (payload) of a valid token.

    Your services doing inbound auth (like API gateways or middlewares) use TokenVerifier.
    """

    @abstractmethod
    async def verify(self, token: str) -> AuthZTokenClaims:
        pass
