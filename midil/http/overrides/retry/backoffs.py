import random
from datetime import datetime
from typing import Mapping
from dateutil.parser import isoparse


class ExponentialBackoffWithJitter:
    def __init__(
        self, base_delay=0.1, max_delay=60.0, jitter_ratio=0.1, respect_retry_after=True
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_ratio = jitter_ratio
        self.respect_retry_after = respect_retry_after

    def calculate_sleep(self, attempt: int, headers: Mapping[str, str]) -> float:
        retry_after = (headers.get("Retry-After") or "").strip()
        if self.respect_retry_after and retry_after:
            if retry_after.isdigit():
                return min(float(retry_after), self.max_delay)
            try:
                parsed_date = isoparse(retry_after).astimezone()
                diff = (parsed_date - datetime.now().astimezone()).total_seconds()
                return min(max(diff, 0), self.max_delay)
            except ValueError:
                pass

        base = self.base_delay * (2 ** (attempt - 1))
        jitter = base * self.jitter_ratio * random.choice([-1, 1])
        return min(base + jitter, self.max_delay)
