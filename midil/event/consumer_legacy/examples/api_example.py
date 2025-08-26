import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel


from midil.event.consumer import (
    create_consumer,
    create_sqs_queue,
    ConsumerConfig,
    DispatcherConfig,
    PollingConfig,
)
from midil.event.consumer.core.types import Event, HandlerContext

# --- Configuration ---
config = ConsumerConfig(
    dispatcher=DispatcherConfig(
        concurrency_limit=5,
        default_timeout_seconds=30,
    ),
    polling=PollingConfig(
        max_messages=10,
        wait_time=20,
        poll_interval=1.0,
        visibility_timeout=60,
        concurrency=5,
    ),
)

# --- Setup global components using factory functions ---
SQS_REGION = "us-east-1"
SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/616782207790/booking-events-dev-v1"

# Create the complete consumer system
queue = create_sqs_queue(queue_url=SQS_QUEUE_URL, region_name=SQS_REGION)
router, dispatcher, polling_strategy = create_consumer(queue, config)


# --- Register Handlers ---
@router.on("checkout:complete", name="validate", timeout_seconds=10)
async def validate(ctx: HandlerContext) -> Dict[str, Any]:
    await asyncio.sleep(0.1)
    return {"ok": True, "user_id": ctx.event.get("user_id")}


@router.on(
    "checkout:complete", name="charge", depends_on=["validate"], timeout_seconds=30
)
async def charge(ctx: HandlerContext) -> Dict[str, Any]:
    validate_result = ctx.deps_results.get("validate")
    if not validate_result or not validate_result["ok"]:
        raise Exception("Validation failed")
    await asyncio.sleep(0.2)
    return {"charged": True, "amount": ctx.event.get("amount", 0)}


@router.on("checkout:complete", name="notify", depends_on=["charge"], timeout_seconds=5)
async def notify(ctx: HandlerContext) -> Dict[str, Any]:
    await asyncio.sleep(0.1)
    return {"notified": True, "user_id": ctx.event.get("user_id")}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager using the new factory-based setup."""
    try:
        # Start the polling strategy
        polling_strategy.start()
        yield
    finally:
        # Clean shutdown
        await polling_strategy.stop()


# --- FastAPI setup ---
app = FastAPI(title="Event Processing Example", lifespan=lifespan)


class EventPayload(BaseModel):
    type: str
    data: Dict[str, Any]


@app.post("/events")
async def handle_event(payload: EventPayload):
    """
    Receive an event and trigger processing.
    """
    message_id = f"msg-{payload.data.get('user_id')}"
    receipt_handle = f"receipt-{payload.data.get('user_id')}"

    success = await dispatcher.dispatch(
        message_id, Event(type=payload.type, data=payload.data), receipt_handle
    )
    return {"success": success}


# --- Optional: a test endpoint to see registered handlers ---
@app.get("/handlers")
def list_handlers():
    """List all registered handlers by event type."""
    return {
        event_type: [
            {
                "name": spec.name,
                "depends_on": spec.depends_on,
                "timeout_seconds": spec.timeout_seconds,
                "failure_policy": spec.failure_policy.value,
            }
            for spec in specs.values()
        ]
        for event_type, specs in router._handlers.items()
    }


@app.get("/config")
def get_config():
    """Get current configuration settings."""
    return {
        "dispatcher": {
            "concurrency_limit": config.dispatcher.concurrency_limit,
            "default_failure_policy": config.dispatcher.default_failure_policy.value,
            "default_timeout_seconds": config.dispatcher.default_timeout_seconds,
        },
        "polling": {
            "max_messages": config.polling.max_messages,
            "wait_time": config.polling.wait_time,
            "poll_interval": config.polling.poll_interval,
            "visibility_timeout": config.polling.visibility_timeout,
            "concurrency": config.polling.concurrency,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "midil.event.consumer.examples.api_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
