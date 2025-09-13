from abc import ABC, abstractmethod
from typing import Annotated, Union, Optional, Sequence, Mapping
from midil.jsonapi.config import AllowExtraFieldsModel
from typing import Dict, Any, List, Set
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
from loguru import logger

from typing import Awaitable
from midil.event.subscriber.base import EventSubscriber
from midil.event.exceptions import RetryableEventError

from threading import Lock
from midil.utils.time import utcnow


class Message(AllowExtraFieldsModel):
    id: Union[str, int] = Field(
        ...,
        description="Unique identifier for the message or its position, You can rely on the message Id for idempotent",
    )
    body: Sequence[Any] | Mapping[Any, Any] | str = Field(
        ..., description="The actual message payload"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=utcnow, description="When the message was published or received"
    )
    ack_handle: Optional[str] = Field(
        default=None,
        description="Token or handle required to ack/nack/delete this message",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional message properties or headers"
    )


class BaseConsumerConfig(BaseModel):
    """
    Configuration model for event consumers.

    This model is intended to be subclassed for specific consumer implementations.
    The 'type' field is used as a discriminator for selecting the appropriate
    consumer configuration at runtime.
    """

    type: Annotated[
        str,
        Field(
            description="Type of the consumer configuration",
            pattern=r"^[a-zA-Z0-9_-]+$",
        ),
    ]


class EventConsumer(ABC):
    """
    Abstract base class for event consumers.

    Event consumers are responsible for subscribing to event sources, registering
    handlers, and managing the lifecycle of event consumption. Subclasses should
    implement the methods to provide concrete integration with event backends such
    as message queues, brokers, or other event delivery mechanisms.

    Attributes:
        _config (EventConsumerConfig): The configuration object for the consumer.
    """

    def __init__(self, config: BaseConsumerConfig):
        self._subscribers: Set[EventSubscriber] = set()
        self._config: BaseConsumerConfig = config
        self._subscription_lock = Lock()

    def subscribe(self, subscriber: EventSubscriber) -> None:
        """
        Register a handler (subscriber) to receive all events.

        Args:
            subscriber (EventSubscriber): A subscriber that will be invoked
                when an event is received. The subscriber receives the event payload as a dictionary.
        """
        with self._subscription_lock:
            self._subscribers.add(subscriber)

    def unsubscribe(self, subscriber: EventSubscriber) -> None:
        """
        Remove a handler (subscriber).

        Args:
            subscriber (EventSubscriber): The subscriber to remove.
        """
        with self._subscription_lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

    async def dispatch(self, event: Message) -> None:
        """
        Dispatch events to all registered subscribers.
        """
        if not self._subscribers:
            logger.warning("No subscribers registered, skipping event...")
            return

        # async with event_context(self._config.type, id=str(event.id)) as ctx:
        tasks: List[Awaitable[Any]] = [
            subscriber(event) for subscriber in self._subscribers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        if any(isinstance(r, RetryableEventError) for r in results):
            requeue = True
            logger.error(
                f"Some subscribers failed for event {event.id}, requeue={requeue}"
            )
            return await self.nack(event, requeue=requeue)

        return await self.ack(event)

    @abstractmethod
    async def start(self) -> None:
        """
        Begin consuming events from the event source.

        This method should be implemented to start the event loop or background
        process that listens for incoming events and dispatches them to the
        registered subscribers.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop consuming events and perform any necessary cleanup.

        This method should be implemented to halt event processing, release
        resources, and ensure that no further events are delivered to subscribers.
        """
        ...

    @abstractmethod
    async def ack(self, message: Message) -> None:
        """
        Acknowledge the receipt of an event.

        This method should be implemented to acknowledge the receipt of an event,
        such as confirming that the event has been processed successfully.

        Args:
            message: The message to ack.
        """
        pass

    @abstractmethod
    async def nack(self, message: Message, requeue: bool = False) -> None:
        """
        Negative acknowledge the receipt of an event.

        This method should be implemented to negatively acknowledge the receipt of an event,
        such as indicating that the event was not processed successfully. If requeue is True,
        the message will be requeued for re-processing.

        Args:
            message: The message to nack.
            requeue: Whether to requeue the message.
        """
        pass
