from dataclasses import dataclass, field
from typing import Optional
from midil.event.consumers.core.types import FailurePolicy


@dataclass
class DispatcherConfig:
    """Configuration for the EventDispatcher."""

    concurrency_limit: int = 10
    default_failure_policy: FailurePolicy = FailurePolicy.ABORT
    default_timeout_seconds: int = 30


@dataclass
class PollingConfig:
    """Configuration for the PollingEventStrategy."""

    max_messages: int = 10
    wait_time: int = 20
    poll_interval: float = 1.0
    visibility_timeout: int = 60
    concurrency: int = 10


@dataclass
class StateStoreConfig:
    """Configuration for state stores."""

    redis_url: str = "redis://localhost:6379"
    ttl_seconds: Optional[int] = None


@dataclass
class ConsumerConfig:
    """Main configuration for the consumer system."""

    dispatcher: DispatcherConfig = field(default_factory=DispatcherConfig)
    polling: PollingConfig = field(default_factory=PollingConfig)
    state_store: StateStoreConfig = field(default_factory=StateStoreConfig)


# Default configuration
DEFAULT_CONFIG = ConsumerConfig()
