from __future__ import annotations

from functools import wraps
from typing import (
    Any,
    Callable,
    ParamSpec,
    TypeVar,
    Coroutine,
    AsyncGenerator,
)

from tenacity import (
    retry,
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

P = ParamSpec("P")
R = TypeVar("R")

SyncCallable = Callable[P, R]
CoroutineCallable = Callable[P, Coroutine[Any, Any, R]]

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_MULTIPLIER = 1
_DEFAULT_MIN_WAIT = 1
_DEFAULT_MAX_WAIT = 10


def exponential_backoff(
    max_attempts: int | None = _DEFAULT_MAX_ATTEMPTS,
    multiplier: float = _DEFAULT_MULTIPLIER,
    min_wait: int = _DEFAULT_MIN_WAIT,
    max_wait: int = _DEFAULT_MAX_WAIT,
    retry_on_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[SyncCallable[P, R]], SyncCallable[P, R]]:
    """
    Retry logic with exponential backoff for sync callables.
    - Sync callables are retried in-place.
    - Uses Tenacity's @retry decorator internally.
    """

    def decorator(func: SyncCallable[P, R]) -> SyncCallable[P, R]:
        stop_strategy = (
            stop_after_attempt(max_attempts)
            if max_attempts is not None
            else stop_after_attempt(_DEFAULT_MAX_ATTEMPTS)
        )
        retry_decorator = retry(
            stop=stop_strategy,
            wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(*retry_on_exceptions),
            reraise=True,
        )

        @retry_decorator
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def exponential_backoff_async(
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    multiplier: float = _DEFAULT_MULTIPLIER,
    min_wait: int = _DEFAULT_MIN_WAIT,
    max_wait: int = _DEFAULT_MAX_WAIT,
    retry_on_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[CoroutineCallable[P, R]], CoroutineCallable[P, R]]:
    """
    Retry logic with exponential backoff for async callables.
    Always returns a coroutine function (not just an Awaitable).
    """

    def decorator(func: CoroutineCallable[P, R]) -> CoroutineCallable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=multiplier, min=min_wait, max=max_wait
                ),
                retry=retry_if_exception_type(*retry_on_exceptions),
                reraise=True,
            ):
                with attempt:
                    return await func(*args, **kwargs)

            raise RuntimeError(
                "Unreachable: async_exponential_backoff exhausted attempts without returning."
            )

        return wrapper

    return decorator


def exponential_backoff_asyncgen[
    T
](
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    multiplier: float = _DEFAULT_MULTIPLIER,
    min_wait: int = _DEFAULT_MIN_WAIT,
    max_wait: int = _DEFAULT_MAX_WAIT,
    retry_on_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[..., Callable[..., AsyncGenerator[T, None]]]:
    """
    Retry logic with exponential backoff for async generators.
    Retries each `__anext__` call, not the entire generator.
    """

    def decorator(
        func: Callable[..., AsyncGenerator[T, None]]
    ) -> Callable[..., AsyncGenerator[T, None]]:
        async def wrapper(*args, **kwargs) -> AsyncGenerator[T, None]:
            gen = func(*args, **kwargs)

            async for item in _wrap_asyncgen_with_retry(gen):
                yield item

        async def _wrap_asyncgen_with_retry(
            gen: AsyncGenerator[T, None]
        ) -> AsyncGenerator[T, None]:
            retry_decorator = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=multiplier, min=min_wait, max=max_wait
                ),
                retry=retry_if_exception_type(*retry_on_exceptions),
                reraise=True,
            )

            @retry_decorator
            async def _next() -> T:
                return await gen.__anext__()

            while True:
                try:
                    yield await _next()
                except StopAsyncIteration:
                    break

        return wrapper

    return decorator
