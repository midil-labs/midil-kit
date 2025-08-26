from midil.event.consumer.core.router import EventRouter
from midil.event.consumer.core.types import Event, HandlerContext
from midil.event.consumer.core.state_store import InMemoryStateStore
from midil.event.consumer.core.dispatcher import EventDispatcher

import asyncio
from typing import Dict, Any


def create_example_system():
    """Example of how to set up and use the event processing system"""

    # Create registry
    router = EventRouter()

    # Register handlers using decorator
    @router.on("checkout:complete", name="validate", timeout_seconds=10)
    async def validate(ctx: HandlerContext) -> Dict[str, Any]:
        # Simulate validation
        await asyncio.sleep(0.1)
        return {"ok": True, "user_id": ctx.event.get("user_id"), "validate": True}

    @router.on(
        "checkout:complete", name="charge", depends_on=["validate"], timeout_seconds=30
    )
    async def charge(ctx: HandlerContext) -> Dict[str, Any]:
        validate_result = ctx.deps_results.get("validate")
        # assert validate_result is None
        if not validate_result or not validate_result["ok"]:
            raise Exception("Validation failed")

        # Simulate charging
        await asyncio.sleep(0.2)
        return {"charged": True, "amount": ctx.event.get("amount", 0)}

    @router.on(
        "checkout:complete", name="notify", depends_on=["charge"], timeout_seconds=5
    )
    async def notify(ctx: HandlerContext) -> Dict[str, Any]:
        _ = ctx.deps_results.get("charge")
        # Simulate notification
        await asyncio.sleep(0.1)
        return {"notified": True, "user_id": ctx.event.get("user_id")}

    # Create processor
    state_store = InMemoryStateStore()
    dispatcher = EventDispatcher(router, state_store)

    return router, dispatcher


# Example test function
async def test_example():
    """Test the example system"""
    registry, dispatcher = create_example_system()

    # Test event
    event = Event(
        type="checkout:complete", data={"user_id": "user123", "amount": 99.99}
    )

    # Process the event
    success = await dispatcher.dispatch("msg123", event, "receipt123")
    print(f"Processing success: {success}")


if __name__ == "__main__":
    # Run example
    asyncio.run(test_example())
