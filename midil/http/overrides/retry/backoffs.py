import random
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from dateutil.parser import isoparse


@dataclass(frozen=True)
class BackoffConfig:
    base_delay: float = 0.1  # starting delay in seconds
    max_delay: float = 60.0  # max cap in seconds
    jitter_ratio: float = 0.1  # % of base delay to apply as jitter
    respect_retry_after: bool = True
    backoff_header: str = "Retry-After"


class ExponentialBackoffWithJitter:
    def __init__(self, config: BackoffConfig | None = None):
        self.config = config or BackoffConfig()

    def calculate_sleep(self, attempt: int, headers: Mapping[str, str]) -> float:
        """
        Calculate the delay before the next retry attempt.

        :param attempt: The retry attempt number (1-based).
        :param headers: HTTP headers that may contain Retry-After.
        :return: Delay in seconds.
        """
        cfg = self.config

        retry_after_value = (headers.get(cfg.backoff_header) or "").strip()
        if cfg.respect_retry_after and retry_after_value:
            # Retry-After in seconds
            if retry_after_value.isdigit():
                return min(float(retry_after_value), cfg.max_delay)

            try:
                parsed_date = isoparse(retry_after_value).astimezone()
                diff = (parsed_date - datetime.now().astimezone()).total_seconds()
                return min(max(diff, 0), cfg.max_delay)
            except (ValueError, OverflowError):
                pass  # fall through to exponential backoff

        base = cfg.base_delay * (2 ** (attempt - 1))

        jitter_amount = base * cfg.jitter_ratio
        jitter = random.uniform(-jitter_amount, jitter_amount)

        return min(base + jitter, cfg.max_delay)
