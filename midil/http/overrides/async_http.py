import httpx
import contextvars

from midil.http.overrides.async_client import MidilAsyncClient
from midil.http.overrides.retry.transport import RetryTransport

_http_client_var: contextvars.ContextVar[
    httpx.AsyncClient | None
] = contextvars.ContextVar("_http_client_var", default=None)

timeout = 60  # TODO: Make this configurable


def _get_http_client_context() -> httpx.AsyncClient:
    client = _http_client_var.get()
    if client is None:
        client = MidilAsyncClient(
            RetryTransport,
            timeout=timeout,
        )
        _http_client_var.set(client)
    return client


# Lazy getter method — safe for importing and use across code
def get_http_async_client() -> httpx.AsyncClient:
    return _get_http_client_context()
