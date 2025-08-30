from midil.event.producer.sqs import SQSProducer, SQSProducerConfig
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from pydantic import BaseModel, Field


# Create config explicitly (recommended for examples)
config = SQSProducerConfig()
print(config.model_dump_json())
producer = SQSProducer(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # If your producer needs to start/stop, do it here
    yield
    producer.close()


app = FastAPI(lifespan=lifespan)


class Event(BaseModel):
    message: str = Field(..., description="Message to publish")


@app.post("/produce")
async def produce_event(event: Event):
    await producer.publish(event.model_dump())
    return {"status": "event published"}


if __name__ == "__main__":
    uvicorn.run(
        "midil.event._examples.standalone_producer:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
