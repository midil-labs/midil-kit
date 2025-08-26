class ConsumerError(Exception):
    """
    Base class for consumer errors.
    """

    pass


class ConsumerNotImplementedError(ConsumerError):
    """
    Exception raised when a consumer method is not implemented.
    """

    pass


class ConsumerNotRunningError(ConsumerError):
    """
    Exception raised when a consumer is not running.
    """

    pass


class ConsumerAlreadyRunningError(ConsumerError):
    """
    Exception raised when a consumer is already running.
    """

    pass


class ConsumerNotSubscribedError(ConsumerError):
    """
    Exception raised when a consumer is not subscribed to an event type.
    """

    pass


class AcknowledgementError(ConsumerError):
    """
    Exception raised when a consumer fails to acknowledge an event.
    """

    pass


class NegativeAcknowledgementError(ConsumerError):
    """
    Exception raised when a consumer fails to negatively acknowledge an event.
    """

    pass


class MessageProcessingError(ConsumerError):
    """
    Exception raised when a consumer fails to process a message.
    """

    pass


class MessageDeserializationError(ConsumerError):
    """
    Exception raised when a consumer fails to deserialize a message.
    """


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


class RetryableSubscriberError(ConsumerError):
    """
    Exception raised when a subscriber fails to process a message.
    """

    pass
