import contextvars
from contextlib import asynccontextmanager
from uuid import uuid4
from typing import Optional, AsyncGenerator


class EventContext:
    def __init__(
        self, id: str, event_type: str, parent: Optional["EventContext"] = None
    ) -> None:
        self.id = id
        self.event_type = event_type
        self.parent = parent


_current_event_context: contextvars.ContextVar[EventContext] = contextvars.ContextVar(
    "event"
)


def get_current_event() -> EventContext:
    return _current_event_context.get()


@asynccontextmanager
async def event_context(
    event_type: str, parent_override: Optional[EventContext] = None
) -> AsyncGenerator[EventContext, None]:
    new_context = EventContext(
        id=uuid4().hex,
        event_type=event_type,
        parent=parent_override
        or (_current_event_context.get(None) if _current_event_context else None),
    )
    token = _current_event_context.set(new_context)
    try:
        yield new_context
    finally:
        _current_event_context.reset(token)
