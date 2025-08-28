from midil.event.event_bus import EventBus, EventBusConfig
from midil.event.consumer.sqs import SQSConsumerConfig
from typing import Dict, Any
from midil.event.subscriber.base import FunctionSubscriber
import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager


config = EventBusConfig(
    consumer=SQSConsumerConfig(
        type="sqs",
        endpoint="https://sqs.us-east-1.amazonaws.com/616782207790/booking-events-dev-v1",
        interval=1.0,
        dlq_uri=None,
    ),
)

bus = EventBus(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bus.start()
    yield
    await bus.stop()


app = FastAPI(lifespan=lifespan)


async def handle_event(event: Dict[str, Any]):
    print("Function subscriber", event)


func_subscriber = FunctionSubscriber(handle_event)
bus.subscribe(func_subscriber)


if __name__ == "__main__":
    uvicorn.run(
        "midil.event._examples.event_bus:app", host="0.0.0.0", port=8000, reload=True
    )
