from midil.event.consumer.sqs import SQSConsumer, SQSConsumerEventConfig
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any
from midil.event.subscriber.base import FunctionSubscriber
from loguru import logger
from midil.settings import EventSettings


# Load config from environment variables or .env file (recommended for production):
# Set these environment variables before running:
#   export TYPE=sqs
#   export QUEUE_URL=https://sqs.us-east-1.amazonaws.com/616782207790/booking-events-dev-v1
#   export DLQ_URL=...
#   export VISIBILITY_TIMEOUT=30
#   export MAX_NUMBER_OF_MESSAGES=10
#   export WAIT_TIME_SECONDS=20
#   export POLL_INTERVAL=0.1
#   export MAX_CONCURRENT_MESSAGES=10
# Then use: consumer_config = EventSettings().event.consumer


# Alternative: Create config explicitly (recommended for development)
# sqs_config = SQSConsumerEventConfig(
#     queue_url="https://sqs.us-east-1.amazonaws.com/616782207790/booking-events-dev-v1",
#     dlq_url=None,
#     visibility_timeout=30,
#     max_number_of_messages=10,
#     wait_time_seconds=20,
#     poll_interval=0.1,
#     max_concurrent_messages=10,
# )


event_settings = EventSettings()
consumer_config = event_settings.event.consumer

# Ensure the config is of the correct type (SQSConsumerEventConfig)
if not isinstance(consumer_config, SQSConsumerEventConfig):
    raise TypeError(
        "event_settings.event.consumer must be an instance of SQSConsumerEventConfig"
    )

consumer = SQSConsumer(consumer_config)


def handle_event(event: Dict[str, Any]):
    logger.info(f"Event {event} handled successfully")


consumer.subscribe(FunctionSubscriber(handle_event))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await consumer.start()
    yield
    await consumer.stop()


app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(
        "midil.event._examples.standalone_consumer:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
