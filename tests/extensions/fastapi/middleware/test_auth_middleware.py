"""
Tests for midil.extensions.fastapi.middleware.auth_middleware
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from starlette.requests import Request
from starlette.responses import Response
from starlette.applications import Starlette


from midil.extensions.fastapi.middleware.auth_middleware import (
    AuthContext,
    CognitoAuthMiddleware,
)
from midil.infrastructure.auth.interfaces.models import AuthZTokenClaims


class TestAuthContext:
    """Tests for AuthContext class."""

    def test_auth_context_init(self, mock_cognito_claims):
        """Test AuthContext initialization."""
        claims = AuthZTokenClaims(token="Bearer test-token", **mock_cognito_claims)
        raw_headers = {
            "authorization": "Bearer token",
            "content-type": "application/json",
        }

        context = AuthContext(claims=claims, _raw_headers=raw_headers)

        assert context.claims == claims
        assert context._raw_headers == raw_headers

    def test_auth_context_to_dict(self, mock_cognito_claims):
        """Test AuthContext to_dict method."""
        claims = AuthZTokenClaims(token="Bearer test-token", **mock_cognito_claims)
        raw_headers = {"authorization": "Bearer token"}

        context = AuthContext(claims=claims, _raw_headers=raw_headers)
        result = context.to_dict()

        assert "claims" in result
        assert "raw_headers" in result
        assert result["raw_headers"] == raw_headers
        assert isinstance(result["claims"], dict)


class TestCognitoAuthMiddleware:
    """Tests for CognitoAuthMiddleware class."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.headers = {"authorization": "Bearer test-token"}
        request.state = Mock()
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create a mock call_next function."""

        async def call_next(request):
            return Response("OK")

        return call_next

    @pytest.fixture
    def auth_middleware(self):
        """Create CognitoAuthMiddleware instance."""
        app = Starlette()
        return CognitoAuthMiddleware(app)

    @pytest.fixture
    def mock_authorizer(self, mock_cognito_claims):
        """Create a mock authorizer."""
        authorizer = AsyncMock()
        claims = AuthZTokenClaims(token="Bearer test-token", **mock_cognito_claims)
        authorizer.verify.return_value = claims
        return authorizer

    @pytest.mark.anyio
    @patch.dict(
        "os.environ",
        {"COGNITO_USER_POOL_ID": "test-pool-id", "AWS_REGION": "us-east-1"},
    )
    @patch("midil.extensions.fastapi.middleware.auth_middleware.CognitoJWTAuthorizer")
    async def test_dispatch_success(
        self,
        mock_authorizer_class,
        auth_middleware,
        mock_request,
        mock_call_next,
        mock_authorizer,
        mock_cognito_claims,
    ):
        """Test successful authentication in middleware dispatch."""
        # Setup mocks
        mock_authorizer_class.return_value = mock_authorizer
        claims = AuthZTokenClaims(token="Bearer test-token", **mock_cognito_claims)
        mock_authorizer.verify.return_value = claims

        # Execute
        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        # Verify
        assert response.status_code == 200
        mock_authorizer.verify.assert_called_once_with("Bearer test-token")

        # Check that auth context was set on request state
        assert hasattr(mock_request.state, "auth")
        auth_context = mock_request.state.auth
        assert isinstance(auth_context, AuthContext)
        assert auth_context.claims == claims
        assert auth_context._raw_headers == dict(mock_request.headers)

    @patch.dict(
        "os.environ",
        {"COGNITO_USER_POOL_ID": "test-pool-id", "AWS_REGION": "us-east-1"},
    )
    @pytest.mark.anyio
    @patch("midil.extensions.fastapi.middleware.auth_middleware.CognitoJWTAuthorizer")
    async def test_dispatch_authorization_error(
        self, mock_authorizer_class, auth_middleware, mock_request, mock_call_next
    ):
        """Test middleware behavior when authorization fails."""
        # Setup mock to raise exception
        mock_authorizer = AsyncMock()
        mock_authorizer.verify.side_effect = Exception("Invalid token")
        mock_authorizer_class.return_value = mock_authorizer

        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Invalid token"):
            await auth_middleware.dispatch(mock_request, mock_call_next)

        mock_authorizer.verify.assert_called_once_with("Bearer test-token")

    @pytest.mark.anyio
    @patch.dict("os.environ", {"COGNITO_USER_POOL_ID": "", "AWS_REGION": ""})
    @patch("midil.extensions.fastapi.middleware.auth_middleware.CognitoJWTAuthorizer")
    async def test_dispatch_empty_environment(
        self,
        mock_authorizer_class,
        auth_middleware,
        mock_request,
        mock_call_next,
        mock_authorizer,
        mock_cognito_claims,
    ):
        """Test middleware with empty environment variables."""
        # Setup mocks
        mock_authorizer_class.return_value = mock_authorizer
        claims = AuthZTokenClaims(token="Bearer test-token", **mock_cognito_claims)
        mock_authorizer.verify.return_value = claims

        # Execute
        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        # Verify
        assert response.status_code == 200
        mock_authorizer_class.assert_called_once_with(user_pool_id="", region="")

    def test_missing_authorization_header(self, auth_middleware, mock_call_next):
        """Test middleware behavior when authorization header is missing."""
        request = Mock(spec=Request)
        request.headers = {}  # No authorization header
        request.state = Mock()

        # This should raise KeyError when trying to access the authorization header
        with pytest.raises(KeyError):
            # Use asyncio.run to run the async function
            import asyncio

            asyncio.run(auth_middleware.dispatch(request, mock_call_next))
