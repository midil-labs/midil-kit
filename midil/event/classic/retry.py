from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, Type


class RetryPolicy(Protocol):
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        ...

    def max_attempts(self) -> int:
        ...


@dataclass
class SimpleRetryPolicy:
    max_attempts_value: int = 3
    retry_on_exceptions: Sequence[Type[BaseException]] = (Exception,)

    def should_retry(
        self, attempt: int, exception: Exception
    ) -> bool:  # noqa: ARG002 - exception used for filtering only
        return attempt < self.max_attempts_value and any(
            isinstance(exception, t) for t in self.retry_on_exceptions
        )

    def max_attempts(self) -> int:
        return self.max_attempts_value


__all__ = [
    "RetryPolicy",
    "SimpleRetryPolicy",
]
