import abc


class RetryPolicy(abc.ABC):
    """Abstract base for retry policies"""

    @abc.abstractmethod
    def max_attempts(self) -> int:
        ...

    @abc.abstractmethod
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        ...


class NoRetryPolicy(RetryPolicy):
    """Policy that never retries - fails immediately on first error"""

    def max_attempts(self) -> int:
        return 1

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        return False


class ExponentialRetryPolicy(RetryPolicy):
    """Exponential retry policy with max attempts"""

    def __init__(self, max_attempts: int = 3) -> None:
        self._max_attempts = max_attempts

    def max_attempts(self) -> int:
        return self._max_attempts

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        return attempt < self._max_attempts
