import abc


class BaseEventStrategy(abc.ABC):
    """
    Base class for event consumption strategies.

    Subclasses should implement the logic for starting and stopping
    the event consumption process, such as polling or streaming from a queue.
    """

    @abc.abstractmethod
    def start(self) -> None:
        """
        Non-blocking method to start the event consumption strategy.

        This method should be implemented by subclasses to begin processing events,
        such as starting a polling loop or subscribing to a stream.
        This method should not block.
        """
        ...

    @abc.abstractmethod
    async def stop(self) -> None:
        """
        Stop the event consumption strategy.

        This method should be implemented by subclasses to gracefully shut down
        the event processing, clean up resources, and ensure all in-flight events
        are handled appropriately.
        """
        ...
