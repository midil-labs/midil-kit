from __future__ import annotations

import asyncio
import functools
from typing import (
    Awaitable,
    Callable,
    ParamSpec,
    TypeVar,
    Union,
    cast,
)

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

P = ParamSpec("P")
R = TypeVar("R")


SyncCallable = Callable[P, R]
AsyncCallable = Callable[P, Awaitable[R]]
AnyCallable = Union[SyncCallable[P, R], AsyncCallable[P, R]]


def with_async_exponential_backoff(
    max_attempts: int = 3,
    multiplier: float = 1,
    min_wait: int = 1,
    max_wait: int = 10,
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
