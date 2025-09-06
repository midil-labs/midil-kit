from abc import ABC


class BaseEventError(Exception, ABC):
    """
    Base class for all errors.
    """

    pass


class ConsumerError(BaseEventError):
    """
    Base class for consumer errors.
    """

    pass


class ConsumerCrashError(ConsumerError):
    """
    Exception raised when a consumer crashes.
    """

    pass


class ConsumerNotImplementedError(ConsumerError):
    """
    Exception raised when a consumer type is not implemented.
    """

    def __init__(self, type: str):
        self.type = type
        super().__init__(f"Consumer type '{type}' is not implemented.")


class ConsumerStartError(ConsumerError):
    """
    Exception raised when a consumer fails to start.
    """

    pass


class ConsumerStopError(ConsumerError):
    """
    Exception raised when a consumer fails to stop.
    """

    pass


class CriticalSubscriberError(Exception):
    """
    Exception raised when a subscriber fails to process a message.
    """

    pass


class ProducerError(Exception):
    """
    Base class for producer errors.
    """

    pass


class ProducerNotImplementedError(ProducerError):
    """
    Exception raised when a producer type is not implemented.
    """

    def __init__(self, type: str):
        self.type = type
        super().__init__(f"Producer type '{type}' is not implemented.")


class TransportNotImplementedError(BaseEventError):
    """
    Exception raised when a transport type is not implemented.
    """

    def __init__(self, type: str):
        self.type = type
        super().__init__(f"Transport type '{type}' is not implemented.")
