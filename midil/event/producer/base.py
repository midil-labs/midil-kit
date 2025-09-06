from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel, Field


class BaseProducerConfig(BaseModel):
    type: str = Field(..., description="Type of the producer configuration")


class EventProducer(ABC):
    """
    Abstract base class for event producers.

    Event producers are responsible for emitting events to an external system or message bus.
    Implementations of this class should provide concrete logic for publishing events to
    backends such as message queues, pub/sub systems, or other event streaming platforms.

    Methods:
        publish(payload, **kwargs):
            Asynchronously publish an event of the specified type with the given payload.
            The payload should be a dictionary containing the event data. Implementations
            may use additional keyword arguments for backend-specific options such as
            message attributes, delivery delay, or partitioning.

        close():
            Release any resources held by the producer, such as network connections,
            file handles, or background threads. This method should be called when the
            producer is no longer needed to ensure proper cleanup.
    """

    @abstractmethod
    async def publish(self, payload: Dict[str, Any], **kwargs) -> None:
        """
        Asynchronously publish an event to the event backend.

        Args:
            payload (Dict[str, Any]): The event data to be sent, as a dictionary.
            **kwargs: Additional backend-specific options (e.g., message attributes,
                delivery delay, partition key).

        Raises:
            Exception: Implementations should raise an exception if publishing fails.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Release any resources associated with the producer.

        This may include closing network connections, flushing buffers, or shutting down
        background threads. After calling this method, the producer should not be used
        to publish further events.
        """
        pass
