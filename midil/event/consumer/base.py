from abc import ABC, abstractmethod
from typing import Annotated
from midil.jsonapi.config import ForbidExtraFieldsModel, AllowExtraFieldsModel
from typing import Callable, Dict, Any, List
from collections import defaultdict
from datetime import datetime
from midil.utils.time import utcnow
from pydantic import Field
import asyncio
from loguru import logger

from typing import Awaitable
from midil.event.consumer.exceptions import (
    ConsumerStartError,
    ConsumerStopError,
    RetryableSubscriberError,
)
from midil.event.retry import with_async_exponential_backoff


EventContext = Dict[str, Any]


class Message(AllowExtraFieldsModel):
    id: str
    type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=utcnow)


Subscriber = Callable[[Message], Awaitable[None] | None]


class EventConsumerConfig(ForbidExtraFieldsModel):
    """
    Configuration model for event consumers.

    This model is intended to be subclassed for specific consumer implementations.
    The 'type' field is used as a discriminator for selecting the appropriate
    consumer configuration at runtime.
    """

    type: Annotated[
        str,
        Field(discriminator="type"),
    ]
    connection_string: str = Field(
        default="localhost", description="Connection string for the event source."
    )
    max_retries: int = Field(
        default=3, ge=0, description="Maximum number of retries for a message."
    )
    interval: float = Field(
        default=1.0, description="Interval between polls if no messages"
    )


class EventConsumer(ABC):
    """
    Abstract base class for event consumers.

    Event consumers are responsible for subscribing to event sources, registering
    handlers for specific event types, and managing the lifecycle of event
    consumption. Subclasses should implement the methods to provide concrete
    integration with event backends such as message queues, brokers, or other
    event delivery mechanisms.

    Attributes:
        _config (EventConsumerConfig): The configuration object for the consumer.
    """

    def __init__(self, config: EventConsumerConfig):
        self._config = config
        self._running: bool = False
        self._loop_task: asyncio.Task[Any] | None = None
        self._subscribers: Dict[str, List[Subscriber]] = defaultdict(list)

    async def subscribe(self, event_type: str, subscriber: Subscriber) -> None:
        """
        Register a handler function for a specific event type.

        Args:
            event_type (str): The type of event to subscribe to.
            handler (Callable[[Dict[str, Any]], None]): A callable that will be invoked
                when an event of the specified type is received. The handler receives
                the event payload as a dictionary.

        This method should be implemented by subclasses to associate the handler
        with the event type in the underlying event system.
        """
        self._subscribers.setdefault(event_type, []).append(subscriber)

    async def unsubscribe(self, event_type: str, subscriber: Subscriber) -> None:
        """
        Remove a handler for an event type.

        Args:
            event_type (str): The event type.
            handler (Observer): The handler to remove.
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(subscriber)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    async def start(self) -> None:
        """
        Begin consuming events from the event source.

        This method should be implemented to start the event loop or background
        process that listens for incoming events and dispatches them to the
        registered handlers.
        """
        try:
            self._running = True
            self._loop_task = asyncio.create_task(self._loop())
        except Exception as e:
            logger.error(f"An error occured while attempting to start consumer: {e}")
            raise ConsumerStartError(
                f"An error occured while attempting to start consumer: {e}"
            )

    async def _loop(self) -> None:
        """
        Loop the consumer.
        """

        try:
            while self._running:
                try:
                    events = await self._consume()
                    if events:
                        await asyncio.gather(
                            *(self._dispatch(event) for event in events)
                        )
                except Exception as e:
                    logger.error(f"Error consuming events: {e}")
                    await asyncio.sleep(self._config.interval)

        except Exception as e:
            logger.error(f"An error occured while attempting to start consumer: {e}")
            raise e

    async def _dispatch(self, event: EventContext) -> None:
        """
        Dispatch events to the appropriate subscribers.
        Each subscriber is retried independently using tenacity.
        """
        event_type = event.get("type")
        if not event_type:
            logger.warning("Event missing 'type' field, skipping ...")
            return

        subscribers = self._subscribers.get(event_type, [])
        if not subscribers:
            logger.warning(
                f"No subscribers registered for event type '{event_type}', skipping event..."
            )
            return

        coros: List[Awaitable[Any]] = []

        async def run_with_retry(sub: Subscriber):
            try:
                retryable_sub = with_async_exponential_backoff(
                    max_attempts=self._config.max_retries,
                    retry_on_exceptions=(RetryableSubscriberError,),
                )(sub)
                return await retryable_sub(Message(**event))
            except Exception as e:
                logger.error(
                    f"Subscriber {sub.__name__} failed for event '{event_type}': {e}"
                )
                # move to dead-letter queue
                return await self.nack(event, requeue=True)

        for subscriber in subscribers:
            coros.append(run_with_retry(subscriber))

        # run all subscribers concurrently
        results = await asyncio.gather(*coros, return_exceptions=True)

        # check if at least one subscriber succeeded
        if all(isinstance(r, Exception) for r in results):
            logger.error(f"All subscribers failed for event '{event_type}'")
            return await self.nack(event, requeue=True)

        return await self.ack(event)

    @abstractmethod
    async def _consume(self) -> List[EventContext]:
        """
        Consume events from the event source.
        """
        ...

    async def _close(self) -> None:
        """
        Close the consumer and release any resources.
        """
        raise NotImplementedError("close() is not implemented")

    async def stop(self) -> None:
        """
        Stop consuming events and perform any necessary cleanup.

        This method should be implemented to halt event processing, release
        resources, and ensure that no further events are delivered to handlers.
        """
        try:
            await self._close()
        except NotImplementedError:
            logger.info("Consumer does not implement close() method, skipping ...")
            pass

        except Exception as e:
            logger.error(f"An error occured while attempting to close consumer: {e}")
            raise ConsumerStopError(
                f"An error occured while attempting to close consumer: {e}"
            )

        finally:
            self._running = False
            self._subscribers.clear()
            if self._loop_task:
                self._loop_task.cancel()
            self._loop_task = None

    @abstractmethod
    async def ack(self, context: EventContext) -> None:
        """
        Acknowledge the receipt of an event.

        This method should be implemented to acknowledge the receipt of an event,
        such as confirming that the event has been processed successfully.

        Args:
            message: The message to ack.
            requeue: Whether to requeue the message.
        """
        pass

    @abstractmethod
    async def nack(self, context: EventContext, requeue: bool = True) -> None:
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
