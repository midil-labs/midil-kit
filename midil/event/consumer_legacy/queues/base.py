import abc
from typing import Any, Dict, List, Optional, Sequence
import asyncio


class EventQueue(abc.ABC):
    """
    Abstract base class for event queue implementations.

    Defines the interface for receiving, deleting, and managing the visibility of messages
    in a queue. Concrete subclasses should implement these methods for specific queue backends.
    """

    _shutdown: asyncio.Event = asyncio.Event()

    @abc.abstractmethod
    async def receive_messages(
        self,
        max_messages: int = 10,
        wait_time: int = 20,
        visibility_timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Receive a batch of messages from the queue.

        Args:
            max_messages: The maximum number of messages to retrieve.
            wait_time: The maximum amount of time (in seconds) to wait for messages.
            visibility_timeout: The duration (in seconds) that the received messages are hidden from subsequent retrieve requests.

        Returns:
            A list of message dictionaries received from the queue.
        """
        pass

    @abc.abstractmethod
    async def delete_messages_batch(self, receipt_handles: Sequence[str]) -> None:
        """
        Delete a batch of messages from the queue using their receipt handles.

        Args:
            receipt_handles: A sequence of receipt handles identifying the messages to delete.
        """
        pass

    @abc.abstractmethod
    async def change_message_visibility(
        self, receipt_handle: str, visibility_timeout: int
    ) -> None:
        """
        Change the visibility timeout of a specific message in the queue.

        Args:
            receipt_handle: The receipt handle of the message.
            visibility_timeout: The new visibility timeout (in seconds) for the message.
        """
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """
        Close any resources associated with the queue, such as network connections or clients.
        """
        pass
