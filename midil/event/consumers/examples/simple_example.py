"""Simplified example demonstrating the improved consumer organization."""

import asyncio
from typing import Dict, Any

from midil.event.consumers import (
    HandlerContext,
    create_consumer_system,
    create_sqs_queue,
    ConsumerConfig,
    PollingConfig,
)


async def main():
    """Example of using the improved consumer system."""

    # Configure the system
    config = ConsumerConfig(
        polling=PollingConfig(
            max_messages=5,
            concurrency=3,
            poll_interval=0.5,
        )
    )

    # Create SQS queue (replace with your queue URL)
    queue = create_sqs_queue(
        queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
        region_name="us-east-1",
    )

    # Create the complete consumer system
    router, dispatcher, polling_strategy = create_consumer_system(queue, config)

    # Register handlers
    @router.on("order:created", name="validate_order")
    async def validate_order(ctx: HandlerContext) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"valid": True, "order_id": ctx.event.get("order_id")}

    @router.on("order:created", name="process_payment", depends_on=["validate_order"])
    async def process_payment(ctx: HandlerContext) -> Dict[str, Any]:
        validate_result = ctx.deps_results.get("validate_order")
        if not validate_result or not validate_result["valid"]:
            raise Exception("Order validation failed")

        await asyncio.sleep(0.2)
        return {"payment_processed": True, "amount": ctx.event.get("amount")}

    @router.on(
        "order:created", name="send_notification", depends_on=["process_payment"]
    )
    async def send_notification(ctx: HandlerContext) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"notification_sent": True, "user_id": ctx.event.get("user_id")}

    # Start the polling strategy
    polling_strategy.start()

    try:
        # Keep running for a while
        await asyncio.sleep(30)
    finally:
        # Clean shutdown
        await polling_strategy.stop()


if __name__ == "__main__":
    asyncio.run(main())
