from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

# Core event types used across the event system
Event = Dict[str, Any]
Handler = Callable[[Event], Awaitable[None]]

__all__ = [
    "Event",
    "Handler",
]
