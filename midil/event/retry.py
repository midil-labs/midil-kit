from __future__ import annotations

import asyncio
import functools
from functools import wraps
from typing import (
    Awaitable,
    Callable,
    ParamSpec,
    TypeVar,
    Union,
    cast,
    Any,
)

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    AsyncRetrying,
)

P = ParamSpec("P")
R = TypeVar("R")


SyncCallable = Callable[P, R]
AsyncCallable = Callable[P, Awaitable[R]]
AnyCallable = Union[SyncCallable[P, R], AsyncCallable[P, R]]


_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_MULTIPLIER = 1
_DEFAULT_MIN_WAIT = 1
_DEFAULT_MAX_WAIT = 10


def async_exponential_backoff(
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    multiplier: float = _DEFAULT_MULTIPLIER,
    min_wait: int = _DEFAULT_MIN_WAIT,
    max_wait: int = _DEFAULT_MAX_WAIT,
    retry_on_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[AnyCallable[P, R]], AsyncCallable[P, R]]:
    """
    Retry logic with exponential backoff for async dispatch.
    - Async callables are awaited directly.
    - Sync callables are run inside the event loop executor.
    """

    def decorator(func: AnyCallable[P, R]) -> AsyncCallable[P, R]:
        is_coroutine = asyncio.iscoroutinefunction(func)

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(*retry_on_exceptions),
            reraise=True,
        )
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if is_coroutine:
                return await cast(AsyncCallable[P, R], func)(*args, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                bound_func = functools.partial(
                    cast(SyncCallable[P, R], func), *args, **kwargs
                )
                return await loop.run_in_executor(None, bound_func)

        return wrapper

    return decorator


class AsyncExponentialBackoff:
    def __init__(
        self,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        multiplier: int = _DEFAULT_MULTIPLIER,
        min_wait: int = _DEFAULT_MIN_WAIT,
        max_wait: int = _DEFAULT_MAX_WAIT,
    ):
        self.max_attempts = max_attempts
        self.multiplier = multiplier
        self.min_wait = min_wait
        self.max_wait = max_wait

    async def run(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(
                multiplier=self.multiplier, min=self.min_wait, max=self.max_wait
            ),
            reraise=True,
        ):
            with attempt:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    partial_func = functools.partial(func, *args, **kwargs)
                    return await loop.run_in_executor(None, partial_func)
