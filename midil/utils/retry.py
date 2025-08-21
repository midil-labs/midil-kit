from __future__ import annotations

import abc


class RetryPolicy(abc.ABC):
    """Abstract base for retry policies"""

    @abc.abstractmethod
    def max_attempts(self) -> int:  # pragma: no cover - interface
        raise NotImplementedError

    @abc.abstractmethod
    def should_retry(
        self, attempt: int, exception: Exception
    ) -> bool:  # pragma: no cover - interface
        raise NotImplementedError


class ExponentialRetryPolicy(RetryPolicy):
    """Exponential retry policy with max attempts"""

    def __init__(self, max_attempts: int = 3) -> None:
        self._max_attempts = max_attempts

    def max_attempts(self) -> int:
        return self._max_attempts

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        return attempt < self._max_attempts


__all__ = [
    "RetryPolicy",
    "ExponentialRetryPolicy",
]
