from __future__ import annotations

import random
from typing import Protocol


class BackoffStrategy(Protocol):
    def next_delay(self, attempt: int) -> float:
        ...


class ExponentialBackoffWithJitter:
    def __init__(
        self, base: float = 1.0, cap: float = 60.0, jitter: float = 0.2
    ) -> None:
        self.base = base
        self.cap = cap
        self.jitter = jitter

    def next_delay(self, attempt: int) -> float:
        delay = min(self.cap, self.base * (2 ** (attempt - 1)))
        jitter_amt = (random.random() * 2 - 1) * self.jitter * delay
        return max(0.0, delay + jitter_amt)


__all__ = [
    "BackoffStrategy",
    "ExponentialBackoffWithJitter",
]
