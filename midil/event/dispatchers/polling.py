from collections import defaultdict
from typing import Callable, Awaitable, Any, Dict, List, Union
import anyio
import inspect
from loguru import logger
from midil.event.dispatchers.abstract import AbstractEventDispatcher
from typing_extensions import TypeVar


FunctionalObserver = Callable[[str, Dict[str, Any]], Awaitable[Any]]
MethodObserver = Callable[[Any, str, Dict[str, Any]], Awaitable[Any]]

Observer = Union[FunctionalObserver, MethodObserver]


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


class PollingEventDispatcher(AbstractEventDispatcher):
    _observers: Dict[str, List[Observer]] = defaultdict(list)

    def on(self, event_type: str) -> Callable[[F], F]:
        """Register an event handler."""

        def decorator(func: F) -> F:
            self._observers.setdefault(event_type, []).append(func)
            logger.debug(f"Registered handler {func.__name__} for event: {event_type}")
            return func

        return decorator

    def register(self, event_type: str, observer: Observer) -> None:
        """Register an event handler."""
        self._observers[event_type].append(observer)

    async def _notify(self, event: str, body: dict[str, Any]) -> None:
        """Notify all registered observers for an event."""
        observers = self._observers.get(event, [])
        logger.debug(
            f"Processing event '{event}' with {len(observers)} registered observers"
        )

        if not observers:
            logger.warning(f"No handlers registered for event: {event}")
            logger.debug(f"Available event types: {list(self._observers.keys())}")
            return

        for observer in observers:
            if inspect.iscoroutinefunction(observer):
                if inspect.ismethod(observer):
                    handler = observer.__self__.__class__.__name__
                    logger.debug(f"Notifying {handler} for event: {event}")
                else:
                    logger.debug(f"Notifying {observer.__name__} for event: {event}")
                # Use anyio's compatibility layer for task creation
                async with anyio.create_task_group() as tg:
                    tg.start_soon(observer, event, body)


dispatcher = PollingEventDispatcher()
