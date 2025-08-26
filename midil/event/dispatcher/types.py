from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Awaitable, Callable, Dict, Optional, Protocol, TypedDict


Event = TypedDict("Event", {"type": str, "data": Any})
HandlerName = str


class Depends:
    def __init__(self, dependency: Callable[..., Awaitable[Any]] | Callable[..., Any]):
        self.dependency = dependency


class FailurePolicy(StrEnum):
    """Handler failure policies"""

    ABORT = "abort"
    CONTINUE = "continue"
    COMPENSATE = "compensate"


class HandlerStatus(StrEnum):
    """Runtime handler execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class HandlerCallable(Protocol):
    def __call__(
        self, ctx: "HandlerContext", *args: Any, **kwargs: Any
    ) -> Awaitable[Any]:
        ...


@dataclass
class HandlerContext:
    """Immutable context passed to handlers during execution"""

    event: Event
    deps_results: Dict[HandlerName, Any]
    attempt: int
    message_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HandlerState:
    """Runtime state tracking for individual handlers"""

    status: HandlerStatus = HandlerStatus.PENDING
    attempts: int = 0
    result: Optional[Any] = None
    last_error: Optional[Exception] = None


@dataclass
class MessageState:
    """Overall state for processing a single message"""

    message_id: str
    handler_states: Dict[HandlerName, HandlerState] = field(default_factory=dict)
    results: Dict[HandlerName, Any] = field(default_factory=dict)
    overall_status: str = "processing"


class LiveEventTimestamp(StrEnum):
    """Enum for timestamp keys"""

    AddedToQueue = "Added To Queue"
    StartedProcessing = "Started Processing"
    FinishedProcessingSuccessfully = "Finished Processing Successfully"
    FinishedProcessingWithError = "Finished Processing With Error"


class QueueLike(Protocol):
    """Structural protocol for queues that support visibility changes."""

    async def change_message_visibility(
        self, receipt_handle: str, visibility_seconds: int
    ) -> None:
        ...
