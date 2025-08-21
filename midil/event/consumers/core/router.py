from collections import defaultdict
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, Optional, Any

from midil.event.consumers.core.exceptions import DependencyRegistrationError
from midil.event.consumers.core.graph import GraphValidator
from midil.utils.retry import ExponentialRetryPolicy, RetryPolicy
from midil.utils.backoff import BackoffStrategy, ExponentialBackoff
from midil.event.consumers.core.types import (
    FailurePolicy,
    HandlerCallable,
    HandlerContext,
    HandlerName,
)
from midil.event.consumers.core.exceptions import DependencyGraphError
from loguru import logger
import inspect


class DependencySpec:
    def __init__(self, func: Callable[..., Awaitable[Any]] | Callable[..., Any]):
        self.func = func
        self.name = func.__name__
        self.deps: List[Callable[..., Awaitable[Any]] | Callable[..., Any]] = []
        self.is_async = inspect.iscoroutinefunction(func)


@dataclass
class HandlerSpec:
    """Complete specification for a handler"""

    name: HandlerName
    handler: HandlerCallable
    depends_on: List[HandlerName] = field(default_factory=list)
    timeout_seconds: int = 30
    retry_policy: RetryPolicy = field(default_factory=lambda: ExponentialRetryPolicy())
    backoff: BackoffStrategy = field(default_factory=lambda: ExponentialBackoff())
    failure_policy: FailurePolicy = FailurePolicy.ABORT
    metadata: Dict[str, object] = field(default_factory=dict)


class EventRouter:
    """
    Facade for routing event handlers with dependency management.
    only handles registration logic.
    """

    def __init__(self):
        self._handlers: Dict[str, Dict[HandlerName, HandlerSpec]] = defaultdict(dict)
        self._handler_counter = 0

    def route(
        self,
        event_type: str,
        handler: HandlerCallable,
        *,
        name: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        timeout_seconds: int = 30,
        retry_policy: Optional[RetryPolicy] = None,
        backoff: Optional[BackoffStrategy] = None,
        failure_policy: Optional[FailurePolicy] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Callable[[HandlerContext], Awaitable[Any]]:
        """
        Register/Route a handler for an event type

        Args:
            event_type: Type of event this handler processes
            handler: Async function to handle the event
            name: Optional handler name (auto-generated if not provided)
            depends_on: List of handler names this handler depends on
            timeout_seconds: Handler execution timeout
            retry_policy: Retry strategy for failed handlers
            backoff: Backoff strategy between retries
            failure_policy: How to handle handler failures
            metadata: Additional handler metadata

        Returns:
            The original handler function (for use as decorator)

        Raises:
            DependencyGraphError: If the dependency graph becomes invalid
        """
        # Generate name if not provided
        if name is None:
            name = self._generate_handler_name(handler)

        # Use defaults if not provided
        retry_policy = retry_policy or ExponentialRetryPolicy()
        backoff = backoff or ExponentialBackoff()
        failure_policy = failure_policy or FailurePolicy.ABORT
        depends_on = depends_on or []
        metadata = metadata or {}

        # Create handler specification
        spec = HandlerSpec(
            name=name,
            handler=handler,
            depends_on=depends_on,
            timeout_seconds=timeout_seconds,
            retry_policy=retry_policy,
            backoff=backoff,
            failure_policy=failure_policy,
            metadata=metadata,
        )

        # Check for duplicate names
        if name in self._handlers[event_type]:
            raise DependencyRegistrationError(
                f"Handler name '{name}' already routed for event type '{event_type}'"
            )

        # Route the handler
        self._handlers[event_type][name] = spec

        # Validate the updated graph
        try:
            GraphValidator.validate(self._handlers[event_type])
        except DependencyGraphError:
            # Remove the handler if validation fails
            del self._handlers[event_type][name]
            raise

        logger.info(f"Routed handler '{name}' for event type '{event_type}'")
        return handler

    def on(
        self,
        event_type: str,
        *,
        name: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        timeout_seconds: int = 30,
        retry_policy: Optional[RetryPolicy] = None,
        backoff: Optional[BackoffStrategy] = None,
        failure_policy: Optional[FailurePolicy] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Decorator version of route"""

        def decorator(handler):
            return self.route(
                event_type=event_type,
                handler=handler,
                name=name,
                depends_on=depends_on,
                timeout_seconds=timeout_seconds,
                retry_policy=retry_policy,
                backoff=backoff,
                failure_policy=failure_policy,
                metadata=metadata,
            )

        return decorator

    def handlers_for(self, event_type: str) -> Dict[HandlerName, HandlerSpec]:
        """Get all handlers routed for an event type"""
        return self._handlers.get(event_type, {}).copy()

    def _generate_handler_name(
        self, handler: Callable[..., Awaitable[Any]] | Callable[..., Any]
    ) -> str:
        """Generate a deterministic name for a handler"""
        try:
            # Try to use module.qualname for deterministic naming
            return f"{handler.__module__}.{handler.__qualname__}"
        except AttributeError:
            # Fallback to counter-based naming
            self._handler_counter += 1
            return f"handler_{self._handler_counter}"


__all__ = ["HandlerSpec", "EventRouter"]
