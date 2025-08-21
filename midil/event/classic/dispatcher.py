from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List

from .types import Event, Handler

logger = logging.getLogger(__name__)


@dataclass
class HandlerSpec:
    handler: Handler
    timeout_seconds: int = 30


class EventDispatcher:
    """Register and dispatch events to handlers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[HandlerSpec]] = {}

    def register(
        self, event_type: str, handler: Handler, timeout_seconds: int = 30
    ) -> Handler:
        spec = HandlerSpec(handler=handler, timeout_seconds=timeout_seconds)
        self._handlers.setdefault(event_type, []).append(spec)
        logger.debug("Registered handler for %s: %s", event_type, handler)
        return handler

    def on(self, event_type: str, timeout_seconds: int = 30):
        def decorator(fn: Handler) -> Handler:
            return self.register(event_type, fn, timeout_seconds)

        return decorator

    def handlers_for(self, event_type: str) -> List[HandlerSpec]:
        return self._handlers.get(event_type, [])

    async def dispatch_single(self, spec: HandlerSpec, event: Event) -> None:
        """Run a single handler with timeout enforcement."""
        try:
            try:
                async with asyncio.timeout(spec.timeout_seconds):
                    await spec.handler(event)
            except AttributeError:
                await asyncio.wait_for(
                    spec.handler(event), timeout=spec.timeout_seconds
                )
        except asyncio.TimeoutError:
            raise
        except Exception:
            raise


__all__ = [
    "HandlerSpec",
    "EventDispatcher",
]
