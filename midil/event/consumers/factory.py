"""Factory functions for creating consumer components."""

from typing import Optional

from .config import ConsumerConfig, DEFAULT_CONFIG
from .core.router import EventRouter
from .core.dispatcher import EventDispatcher
from .core.state_store import StateStore, InMemoryStateStore, RedisStateStore
from .queues import EventQueue, SQSEventQueue
from .strategies.polling import PollingEventStrategy


def create_router() -> EventRouter:
    """Create a new EventRouter instance."""
    return EventRouter()


def create_state_store(
    store_type: str = "memory",
    redis_url: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
) -> StateStore:
    """
    Create a state store instance.

    Args:
        store_type: Either "memory" or "redis"
        redis_url: Redis connection URL (required for redis type)
        ttl_seconds: TTL for message keys (redis only)

    Returns:
        Configured StateStore instance
    """
    if store_type == "memory":
        return InMemoryStateStore()
    elif store_type == "redis":
        if not redis_url:
            raise ValueError("redis_url is required for redis state store")
        return RedisStateStore(redis_url=redis_url, ttl_seconds=ttl_seconds)
    else:
        raise ValueError(f"Unknown state store type: {store_type}")


def create_dispatcher(
    router: EventRouter,
    state_store: StateStore,
    config: Optional[ConsumerConfig] = None,
) -> EventDispatcher:
    """
    Create an EventDispatcher instance.

    Args:
        router: EventRouter instance
        state_store: StateStore instance
        config: Configuration (uses default if not provided)

    Returns:
        Configured EventDispatcher instance
    """
    if config is None:
        config = DEFAULT_CONFIG

    return EventDispatcher(
        router=router,
        state_store=state_store,
        concurrency_limit=config.dispatcher.concurrency_limit,
        default_failure_policy=config.dispatcher.default_failure_policy,
    )


def create_sqs_queue(
    queue_url: str,
    region_name: Optional[str] = None,
) -> SQSEventQueue:
    """
    Create an SQS queue instance.

    Args:
        queue_url: SQS queue URL
        region_name: AWS region name

    Returns:
        Configured SQSEventQueue instance
    """
    return SQSEventQueue(queue_url=queue_url, region_name=region_name)


def create_polling_strategy(
    queue: EventQueue,
    router: EventRouter,
    state_store: StateStore,
    config: Optional[ConsumerConfig] = None,
) -> PollingEventStrategy:
    """
    Create a polling strategy instance.

    Args:
        queue: EventQueue instance
        router: EventRouter instance
        state_store: StateStore instance
        config: Configuration (uses default if not provided)

    Returns:
        Configured PollingEventStrategy instance
    """
    if config is None:
        config = DEFAULT_CONFIG

    return PollingEventStrategy(
        queue=queue,
        router=router,
        state_store=state_store,
        max_messages=config.polling.max_messages,
        wait_time=config.polling.wait_time,
        poll_interval=config.polling.poll_interval,
        visibility_timeout=config.polling.visibility_timeout,
        concurrency=config.polling.concurrency,
    )


def create_consumer_system(
    queue: EventQueue,
    config: Optional[ConsumerConfig] = None,
) -> tuple[EventRouter, EventDispatcher, PollingEventStrategy]:
    """
    Create a complete consumer system with all components.

    Args:
        queue: EventQueue instance
        config: Configuration (uses default if not provided)

    Returns:
        Tuple of (router, dispatcher, polling_strategy)
    """
    if config is None:
        config = DEFAULT_CONFIG

    router = create_router()
    state_store = create_state_store(
        store_type="memory"
        if config.state_store.redis_url == "redis://localhost:6379"
        else "redis",
        redis_url=config.state_store.redis_url,
        ttl_seconds=config.state_store.ttl_seconds,
    )
    dispatcher = create_dispatcher(router, state_store, config)
    polling_strategy = create_polling_strategy(queue, router, state_store, config)

    return router, dispatcher, polling_strategy
