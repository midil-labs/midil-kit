from httpx import AsyncClient
from typing import Any, Dict, TYPE_CHECKING


if TYPE_CHECKING:
    from httpx import URL
    from midil.infrastructure.auth.interfaces.authenticator import AuthNProvider


class HttpClient:
    def __init__(self, auth_client: "AuthNProvider", base_url: "URL") -> None:
        self.base_url = base_url
        self._client = AsyncClient(base_url=self.base_url)
        self._auth_client = auth_client

    @property
    def client(self) -> AsyncClient:
        return self._client

    @client.setter
    def client(self, value: AsyncClient) -> None:
        value.base_url = self.base_url
        self._client = value

    @property
    async def headers(self) -> Dict[str, Any]:
        auth_headers = await self._auth_client.get_headers()
        headers: Dict[str, Any] = auth_headers.model_dump(by_alias=True)
        return headers

    async def send_request(self, method: str, url: str, data: Dict[str, Any]) -> Any:
        headers = await self.headers
        response = await self._client.request(
            method=method, url=url, headers=headers, json=data
        )
        response.raise_for_status()
        return response.json()
