"""Core event processing subsystem.

This package provides a modular implementation of the event processing system
including types, exceptions, policies, dispatcher, processor, and state store.

Import submodules directly, e.g.:
    from midil.event.consumers.types import HandlerContext
    from midil.event.consumers.dispatcher import EventDispatcher
    from midil.event.consumers.state_store import StateStore
"""

# Core types and interfaces
from midil.event.consumers.core.types import (
    HandlerContext,
    HandlerCallable,
    Event,
    HandlerName,
    FailurePolicy,
    HandlerStatus,
    Depends,
)

# Core components
from midil.event.consumers.core.router import EventRouter
from midil.event.consumers.core.dispatcher import EventDispatcher
from midil.event.consumers.core.state_store import (
    StateStore,
    InMemoryStateStore,
    RedisStateStore,
)

# Queue implementations
from midil.event.consumers.queues import EventQueue, SQSEventQueue

# Strategy implementations
from midil.event.consumers.strategies import BaseEventStrategy, PollingEventStrategy

# Configuration and factory
from midil.event.consumers.config import (
    ConsumerConfig,
    DispatcherConfig,
    PollingConfig,
    StateStoreConfig,
    DEFAULT_CONFIG,
)
from midil.event.consumers.factory import (
    create_router,
    create_state_store,
    create_dispatcher,
    create_sqs_queue,
    create_polling_strategy,
    create_consumer_system,
)

# Exceptions
from .core.exceptions import (
    EventProcessingError,
    DependencyGraphError,
    CycleDetectedError,
    DependencyRegistrationError,
)

# Utilities
from midil.event.consumers.core.graph import GraphValidator

__all__ = [
    # Types
    "HandlerContext",
    "HandlerCallable",
    "Event",
    "HandlerName",
    "FailurePolicy",
    "HandlerStatus",
    "Depends",
    # Core components
    "EventRouter",
    "EventDispatcher",
    "StateStore",
    "InMemoryStateStore",
    "RedisStateStore",
    # Queues
    "EventQueue",
    "SQSEventQueue",
    # Strategies
    "BaseEventStrategy",
    "PollingEventStrategy",
    # Configuration
    "ConsumerConfig",
    "DispatcherConfig",
    "PollingConfig",
    "StateStoreConfig",
    "DEFAULT_CONFIG",
    # Factory functions
    "create_router",
    "create_state_store",
    "create_dispatcher",
    "create_sqs_queue",
    "create_polling_strategy",
    "create_consumer_system",
    # Exceptions
    "EventProcessingError",
    "DependencyGraphError",
    "CycleDetectedError",
    "DependencyRegistrationError",
    # Utilities
    "GraphValidator",
]
