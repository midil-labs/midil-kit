from midil.event.consumer.sqs import SQSConsumer, SQSConsumerConfig
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any
from midil.event.subscriber.base import FunctionSubscriber


# Create config explicitly (recommended for examples)
config = SQSConsumerConfig()
# type="sqs",
# endpoint="https://sqs.us-east-1.amazonaws.com/616782207790/booking-events-dev-v1",
# interval=1.0,
# )

# Alternative: Create config from environment variables
# Set these environment variables before running:
# export TYPE=sqs
# export ENDPOINT=https://sqs.us-east-1.amazonaws.com/616782207790/booking-events-dev-v1
# Then use: config = SQSConsumerConfig()
print(config.model_dump_json())
consumer = SQSConsumer(config)


def handle_event(event: Dict[str, Any]):
    print("Function subscriber", event)


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
