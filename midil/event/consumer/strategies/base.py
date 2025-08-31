from abc import ABC, abstractmethod
from typing import Annotated, Union, Optional, Sequence, Mapping
from midil.jsonapi.config import AllowExtraFieldsModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any, List, Set
from datetime import datetime
from pydantic import Field
import asyncio
from loguru import logger

from typing import Awaitable
from midil.event.subscriber.base import EventSubscriber
from midil.event.exceptions import CriticalSubscriberError


class Message(AllowExtraFieldsModel):
    id: Union[str, int] = Field(
        ...,
        description="Unique identifier for the message or its position, You can rely on the message Id for idepotency",
    )
    body: Sequence[Any] | Mapping[Any, Any] | str = Field(
        ..., description="The actual message payload"
    )
    timestamp: Optional[datetime] = Field(
        None, description="When the message was published or received"
    )
    ack_handle: Optional[str] = Field(
        None, description="Token or handle required to ack/nack/delete this message"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional message properties or headers"
    )


class EventConsumerConfig(BaseSettings):
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        env_prefix="MIDIL__EVENT__CONSUMER__",
        env_nested_delimiter="__",
    )


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

    def __init__(self, config: EventConsumerConfig):
        self._subscribers: Set[EventSubscriber] = set()
        self._config: EventConsumerConfig = config

    def subscribe(self, subscriber: EventSubscriber) -> None:
        """
        Register a handler (subscriber) to receive all events.

        Args:
            subscriber (EventSubscriber): A subscriber that will be invoked
                when an event is received. The subscriber receives the event payload as a dictionary.
        """
        self._subscribers.add(subscriber)

    async def unsubscribe(self, subscriber: EventSubscriber) -> None:
        """
        Remove a handler (subscriber).

        Args:
            subscriber (EventSubscriber): The subscriber to remove.
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    async def dispatch(self, event: Message) -> None:
        """
        Dispatch events to all registered subscribers.
        """
        if not self._subscribers:
            logger.warning("No subscribers registered, skipping event...")
            return

        tasks: List[Awaitable[Any]] = [
            subscriber(event) for subscriber in self._subscribers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        if any(isinstance(r, CriticalSubscriberError) for r in results):
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
