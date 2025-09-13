from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI

import uvicorn

from midil.event.config import EventConfig
from midil.event.event_bus import EventBus
from midil.event.subscriber.middlewares import (
    LoggingMiddleware,
    RetryMiddleware,
)
from midil.utils.retry import AsyncRetry
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


## subscribe to the event bus
retry = AsyncRetry()


@bus.subscriber(
    target="checkin",
    middlewares=[RetryMiddleware(retry), LoggingMiddleware()],
)
async def handle_checkin_event(event: Dict[str, Any]):
    print("Function subscriber : I got it", event)


# @bus.subscriber()  # subscribe to all consumers
# async def handle_all_events(event: Dict[str, Any]):
#     print("Function subscriber 2: I also got it ", event)


if __name__ == "__main__":
    uvicorn.run(
        "midil.event._examples.event_bus:app", host="0.0.0.0", port=8000, reload=True
    )
