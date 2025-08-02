import asyncio
from asyncio import ensure_future
from functools import wraps
from traceback import format_exception
from typing import Callable, Coroutine, Any

from loguru import logger
from starlette.concurrency import run_in_threadpool

import redis.asyncio as redis

NoArgsNoReturnFuncT = Callable[[], None]
NoArgsNoReturnAsyncFuncT = Callable[[], Coroutine[Any, Any, None]]
NoArgsNoReturnDecorator = Callable[
    [NoArgsNoReturnFuncT | NoArgsNoReturnAsyncFuncT], NoArgsNoReturnAsyncFuncT
]


def repeat_every(
    seconds: float,
    wait_first: bool = False,
    raise_exceptions: bool = False,
    max_repetitions: int | None = None,
) -> NoArgsNoReturnDecorator:
    """
    This function returns a decorator that modifies a function so it is periodically re-executed after its first call.
    The function it decorates should accept no arguments and return nothing (a nullary function). If necessary, this can be accomplished
    by using `functools.partial` or otherwise wrapping the target function prior to decoration.
    Parameters
    ----------
    seconds: float
        The number of seconds to wait between repeated calls
    wait_first: bool (default False)
        If True, the function will wait for a single period before the first call
    raise_exceptions: bool (default False)
        If True, errors raised by the decorated function will be raised to the event loop's exception handler.
        Note that if an error is raised, the repeated execution will stop.
        Otherwise, exceptions are just logged and the execution continues to repeat.
        See https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.set_exception_handler for more info.
    max_repetitions: Optional[int] (default None)
        The maximum number of times to call the repeated function. If `None`, the function is repeated forever.
    """

    def decorator(
        func: NoArgsNoReturnAsyncFuncT | NoArgsNoReturnFuncT,
    ) -> NoArgsNoReturnAsyncFuncT:
        """
        Converts the decorated function into a repeated, periodically-called version of itself.
        """
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def wrapped() -> None:
            repetitions = 0

            async def loop() -> None:
                nonlocal repetitions

                if wait_first:
                    await asyncio.sleep(seconds)
                while max_repetitions is None or repetitions < max_repetitions:
                    # count the repetition even if an exception is raised
                    repetitions += 1
                    try:
                        if is_coroutine:
                            await func()  # type: ignore
                        else:
                            await run_in_threadpool(func)
                    except Exception as exc:
                        formatted_exception = "".join(
                            format_exception(type(exc), exc, exc.__traceback__)
                        )
                        logger.error(formatted_exception)
                        if raise_exceptions:
                            raise exc
                    await asyncio.sleep(seconds)

            ensure_future(loop())

        return wrapped

    return decorator


redis_client = redis.Redis.from_url("redis://localhost:6379", decode_responses=True)


def repeat_every_distributed(
    *,
    seconds: float,
    lock_key: str,
    wait_first: bool = False,
    raise_exceptions: bool = False,
    max_repetitions: int | None = None,
    lock_ttl: int | None = None,  # Optional override for Redis lock TTL
) -> NoArgsNoReturnDecorator:
    """Optimized version of repeat_every that uses Redis locks to prevent multiple instances of the same task from running concurrently.
    Suitable for distributed systems."""

    def decorator(
        func: NoArgsNoReturnAsyncFuncT | NoArgsNoReturnFuncT,
    ) -> NoArgsNoReturnAsyncFuncT:
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def wrapped() -> None:
            repetitions = 0

            async def loop() -> None:
                nonlocal repetitions
                if wait_first:
                    await asyncio.sleep(seconds)

                while max_repetitions is None or repetitions < max_repetitions:
                    repetitions += 1
                    try:
                        # Attempt to acquire Redis lock
                        acquired = await redis_client.set(
                            name=lock_key,
                            value="1",
                            nx=True,  # only set if not exists
                            ex=lock_ttl or int(seconds),  # auto-expire
                        )

                        if acquired:
                            logger.info(f"Acquired lock `{lock_key}`, running task.")
                            if is_coroutine:
                                await func()  # type: ignore
                            else:
                                await run_in_threadpool(func)
                        else:
                            logger.debug(
                                f"Lock `{lock_key}` already held by another instance."
                            )
                    except Exception as exc:
                        formatted_exception = "".join(
                            format_exception(type(exc), exc, exc.__traceback__)
                        )
                        logger.error(formatted_exception)
                        if raise_exceptions:
                            raise exc
                    await asyncio.sleep(seconds)

            asyncio.ensure_future(loop())

        return wrapped

    return decorator
