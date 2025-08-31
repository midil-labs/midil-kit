import httpx
import contextvars

from midil.http.overrides.async_client import MidilAsyncClient
from midil.http.overrides.retry.transport import RetryTransport

from typing import Any


_http_client_var: contextvars.ContextVar[
    httpx.AsyncClient | None
] = contextvars.ContextVar("_http_client_var", default=None)


def _get_http_client_context(timeout: int = 60, **kwargs: Any) -> httpx.AsyncClient:
    client = _http_client_var.get()
    if client is None:
        client = MidilAsyncClient(
            RetryTransport,
            timeout=timeout,
            **kwargs,
        )
        _http_client_var.set(client)
    return client


def get_http_async_client(timeout: int = 60, **kwargs: Any) -> httpx.AsyncClient:
    return _get_http_client_context(timeout, **kwargs)
