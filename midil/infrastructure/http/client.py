from typing import Any, Dict, TYPE_CHECKING
from httpx import AsyncClient

from midil.infrastructure.http.overrides.async_http import (
    get_http_async_client,
    _http_client_var,
)

if TYPE_CHECKING:
    from httpx import URL
    from midil.infrastructure.auth.interfaces.authenticator import AuthNProvider


class HttpClient:
    def __init__(self, auth_client: "AuthNProvider", base_url: "URL") -> None:
        self.base_url = base_url
        self._auth_client = auth_client

    @property
    def client(self) -> AsyncClient:
        client = get_http_async_client()
        client.base_url = self.base_url
        return client

    @client.setter
    def client(self, value: AsyncClient) -> None:
        value.base_url = self.base_url
        _http_client_var.set(value)

    @property
    async def headers(self) -> Dict[str, Any]:
        auth_headers = await self._auth_client.get_headers()
        return auth_headers.model_dump(by_alias=True)

    async def send_request(self, method: str, url: str, data: Dict[str, Any]) -> Any:
        headers = await self.headers
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def send_paginated_request(
        self, method: str, url: str, data: Dict[str, Any]
    ) -> Any:
        raise NotImplementedError("Paginated requests are not implemented")
