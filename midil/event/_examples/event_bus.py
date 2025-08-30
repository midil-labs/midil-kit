from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI

import uvicorn

from midil.event.event_bus import EventBus, EventConfig
from midil.event.consumer.sqs import SQSConsumerConfig
from midil.event.subscriber.middlewares import (
    LoggingMiddleware,
    GroupMiddleware,
    RetryMiddleware,
)
from midil.event.retry import AsyncExponentialBackoff


consumer_config = SQSConsumerConfig()

config = EventConfig(consumer=consumer_config)

print(f"config.model_dump_json(): {config.model_dump_json()}")

bus = EventBus(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bus.start()
    yield
    await bus.stop()


app = FastAPI(lifespan=lifespan)


@bus.subscriber(
    middlewares=[
        RetryMiddleware(AsyncExponentialBackoff()),
        GroupMiddleware([LoggingMiddleware()]),
    ]
)
async def handle_event(event: Dict[str, Any]):
    print("Function subscriber : I got it")


@bus.subscriber()
async def handle_event_2(event: Dict[str, Any]):
    print("Function subscriber 2: I also got it ")


if __name__ == "__main__":
    uvicorn.run(
        "midil.event._examples.event_bus:app", host="0.0.0.0", port=8000, reload=True
    )
