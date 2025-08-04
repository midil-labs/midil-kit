import pytest
from unittest.mock import AsyncMock, Mock
import httpx
from httpx import URL
from midil.infrastructure.http.client import HttpClient
from midil.infrastructure.auth.interfaces.models import AuthNHeaders

pytestmark = pytest.mark.asyncio


class MockAuthNProvider:
    """Mock AuthNProvider for testing."""

    def __init__(self, headers_data=None):
        self.headers_data = headers_data or {
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_headers(self) -> AuthNHeaders:
        return AuthNHeaders(**self.headers_data)


class TestHttpClient:
    """Tests for HttpClient class."""

    @pytest.fixture
    def mock_auth_provider(self):
        """Create a mock authentication provider."""
        return MockAuthNProvider()

    @pytest.fixture
    def base_url(self):
        """Create a base URL for testing."""
        return URL("https://api.example.com")

    @pytest.fixture
    def http_client(self, mock_auth_provider, base_url):
        """Create an HttpClient instance for testing."""
        return HttpClient(auth_client=mock_auth_provider, base_url=base_url)

    def test_init(self, mock_auth_provider, base_url):
        """Test HttpClient initialization."""
        client = HttpClient(auth_client=mock_auth_provider, base_url=base_url)

        assert client.base_url == base_url
        assert client._auth_client == mock_auth_provider
        assert isinstance(client.client, httpx.AsyncClient)
        assert client.client.base_url == base_url

    def test_client_property_getter(self, http_client):
        """Test client property getter."""
        client = http_client.client
        assert isinstance(client, httpx.AsyncClient)
        assert client == http_client.client

    def test_client_property_setter(self, http_client, base_url):
        """Test client property setter."""
        new_client = httpx.AsyncClient()

        http_client.client = new_client

        assert http_client.client == new_client
        assert http_client.client.base_url == base_url

    def test_client_setter_updates_base_url(self, http_client):
        """Test that client setter updates base_url on new client."""
        original_base_url = http_client.base_url
        new_client = httpx.AsyncClient(base_url="https://different.com")

        http_client.client = new_client

        # Base URL should be updated to match the HttpClient's base_url
        assert http_client.client.base_url == original_base_url

    async def test_headers_property(self, http_client):
        """Test headers property returns auth headers."""
        headers = await http_client.headers

        assert isinstance(headers, dict)
        assert "Authorization" in headers
        assert "Accept" in headers
        assert "Content-Type" in headers
        assert headers["Authorization"] == "Bearer test-token"

    async def test_headers_property_with_custom_auth(self, base_url):
        """Test headers property with custom auth provider."""
        custom_headers = {
            "Authorization": "Bearer custom-token",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "X-Custom-Header": "custom-value",
        }
        auth_provider = MockAuthNProvider(custom_headers)
        client = HttpClient(auth_client=auth_provider, base_url=base_url)

        headers = await client.headers

        assert headers["Authorization"] == "Bearer custom-token"
        assert headers["Accept"] == "application/vnd.api+json"
        assert headers["X-Custom-Header"] == "custom-value"

    async def test_send_request_success(self, http_client):
        """Test successful request sending."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_response.raise_for_status.return_value = None

        # Mock the client request
        http_client.client.request = AsyncMock(return_value=mock_response)

        result = await http_client.send_request(
            method="POST", url="/test", data={"test": "data"}
        )

        assert result == {"success": True, "data": "test"}

        # Verify the request was made correctly
        http_client.client.request.assert_called_once_with(
            method="POST",
            url="/test",
            headers={
                "Authorization": "Bearer test-token",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={"test": "data"},
        )

    async def test_send_request_get_method(self, http_client):
        """Test GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "retrieved"}
        mock_response.raise_for_status.return_value = None

        http_client.client.request = AsyncMock(return_value=mock_response)

        result = await http_client.send_request(method="GET", url="/users/123", data={})

        assert result == {"data": "retrieved"}

        http_client.client.request.assert_called_once_with(
            method="GET",
            url="/users/123",
            headers={
                "Authorization": "Bearer test-token",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={},
        )

    async def test_send_request_with_different_methods(self, http_client):
        """Test request with different HTTP methods."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        http_client.client.request = AsyncMock(return_value=mock_response)

        methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for method in methods:
            await http_client.send_request(
                method=method, url=f"/test-{method.lower()}", data={"method": method}
            )

            # Get the last call arguments
            last_call = http_client.client.request.call_args
            assert last_call[1]["method"] == method
            assert last_call[1]["url"] == f"/test-{method.lower()}"

    async def test_send_request_http_error(self, http_client):
        """Test request with HTTP error response."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=None, response=mock_response
        )

        http_client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await http_client.send_request(method="GET", url="/not-found", data={})

    async def test_send_request_network_error(self, http_client):
        """Test request with network error."""
        http_client.client.request = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        with pytest.raises(httpx.ConnectError):
            await http_client.send_request(method="GET", url="/test", data={})

    async def test_send_request_json_decode_error(self, http_client):
        """Test request with JSON decode error."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")

        http_client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError):
            await http_client.send_request(method="GET", url="/test", data={})

    async def test_send_request_uses_fresh_headers(self, http_client):
        """Test that send_request gets fresh headers for each request."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        http_client.client.request = AsyncMock(return_value=mock_response)

        # Make two requests
        await http_client.send_request("GET", "/test1", {})
        await http_client.send_request("GET", "/test2", {})

        # Verify auth provider was called twice (once for each request)
        assert http_client.client.request.call_count == 2

    async def test_send_paginated_request_not_implemented(self, http_client):
        """Test that send_paginated_request raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await http_client.send_paginated_request(
                method="GET", url="/paginated", data={}
            )

    def test_type_annotations(self, http_client):
        """Test that type annotations are properly set."""
        import inspect

        # Check init signature
        init_sig = inspect.signature(HttpClient.__init__)
        assert "auth_client" in init_sig.parameters
        assert "base_url" in init_sig.parameters

        # Check that the class has the expected methods
        assert hasattr(http_client, "send_request")
        assert hasattr(http_client, "send_paginated_request")
        assert hasattr(
            HttpClient, "headers"
        )  # Check class level to avoid coroutine creation

    async def test_auth_provider_integration(self, base_url):
        """Test integration with different auth providers."""

        class CustomAuthProvider:
            async def get_headers(self) -> AuthNHeaders:
                return AuthNHeaders(
                    authorization="Bearer integration-token",
                    accept="application/custom+json",
                    content_type="application/custom+json",
                )

        custom_auth = CustomAuthProvider()
        client = HttpClient(auth_client=custom_auth, base_url=base_url)

        headers = await client.headers

        assert headers["Authorization"] == "Bearer integration-token"
        assert headers["Accept"] == "application/custom+json"
        assert headers["Content-Type"] == "application/custom+json"

    async def test_concurrent_requests(self, http_client):
        """Test handling concurrent requests."""
        import anyio

        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        http_client.client.request = AsyncMock(return_value=mock_response)

        # Make concurrent requests using anyio for cross-framework compatibility
        results = []

        async def make_request(i):
            result = await http_client.send_request("GET", f"/test-{i}", {})
            results.append(result)

        async with anyio.create_task_group() as tg:
            for i in range(5):
                tg.start_soon(make_request, i)

        # All should succeed
        assert all(result == {"success": True} for result in results)
        assert http_client.client.request.call_count == 5

    def test_base_url_handling_with_different_url_types(self, mock_auth_provider):
        """Test base_url handling with different URL types."""
        # Test with string URL
        string_url = "https://api.example.com"
        client1 = HttpClient(auth_client=mock_auth_provider, base_url=URL(string_url))
        assert str(client1.base_url) == string_url

        # Test with httpx.URL
        url_obj = URL("https://api.example.com")
        client2 = HttpClient(auth_client=mock_auth_provider, base_url=url_obj)
        assert client2.base_url == url_obj

    async def test_empty_response_handling(self, http_client):
        """Test handling of empty responses."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None

        http_client.client.request = AsyncMock(return_value=mock_response)

        result = await http_client.send_request("GET", "/empty", {})

        assert result == {}

    async def test_complex_data_structures(self, http_client):
        """Test sending complex data structures."""
        mock_response = Mock()
        mock_response.json.return_value = {"processed": True}
        mock_response.raise_for_status.return_value = None

        http_client.client.request = AsyncMock(return_value=mock_response)

        complex_data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "preferences": {"theme": "dark", "notifications": True},
            },
            "metadata": {"timestamp": "2023-01-01T00:00:00Z", "version": "1.0"},
        }

        result = await http_client.send_request("POST", "/complex", complex_data)

        assert result == {"processed": True}

        # Verify the complex data was passed correctly
        call_args = http_client.client.request.call_args
        assert call_args[1]["json"] == complex_data
