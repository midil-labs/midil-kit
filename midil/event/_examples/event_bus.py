from typing import Dict, Any, Callable, Awaitable, Coroutine, cast
from contextlib import asynccontextmanager

from fastapi import FastAPI

import uvicorn

from midil.event.config import EventConfig
from midil.event.event_bus import EventBus
from midil.event.subscriber.middlewares import (
    LoggingMiddleware,
    GroupMiddleware,
    RetryMiddleware,
)
from midil.utils.retry import exponential_backoff_async
from midil.settings import get_consumer_event_settings


booking_settings = get_consumer_event_settings("booking")
checkin_settings = get_consumer_event_settings("checkin")
config = EventConfig(
    consumers={
        "booking": booking_settings,
        "checkin": checkin_settings,
    }
)
bus = EventBus(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # start the event bus
    await bus.start()
    yield
    # stop the event bus
    await bus.stop()


app = FastAPI(lifespan=lifespan)

# Retry Middleware expects a callable, so we create a convenience function
# to wrap the exponential_backoff_async which is a decorator with the retry logic.
# You can also just implmement your own _RetryCallable if you want.


async def exponential_backoff_async_wrapper(
    func: Callable[..., Awaitable[Any]], *args, **kwargs
) -> Any:
    func = cast(Callable[..., Coroutine[Any, Any, Any]], func)
    wrapped = exponential_backoff_async()
    retry_func: Callable[..., Coroutine[Any, Any, Any]] = wrapped(func)
    return await retry_func(*args, **kwargs)


## subscribe to the event bus
@bus.subscriber(
    target="checkin",
    middlewares=[
        RetryMiddleware(exponential_backoff_async_wrapper),
        GroupMiddleware([LoggingMiddleware()]),
    ],
)
async def handle_checkin_event(event: Dict[str, Any]):
    print("Function subscriber : I got it")


@bus.subscriber()  # subscribe to all consumers
async def handle_all_events(event: Dict[str, Any]):
    print("Function subscriber 2: I also got it ")


if __name__ == "__main__":
    uvicorn.run(
        "midil.event._examples.event_bus:app", host="0.0.0.0", port=8000, reload=True
    )
