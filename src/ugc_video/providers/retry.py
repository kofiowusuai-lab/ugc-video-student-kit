import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from ugc_video.domain import FailureKind
from ugc_video.providers.base import ProviderError

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    delays: tuple[float, ...] = (2.0, 5.0)
    sleep: Callable[[float], None] = time.sleep

    def run(self, operation: Callable[[], T]) -> T:
        for attempt in range(self.max_attempts):
            try:
                return operation()
            except ProviderError as exc:
                retryable = exc.kind in {FailureKind.TRANSIENT, FailureKind.RATE_LIMIT}
                if not retryable or attempt + 1 >= self.max_attempts:
                    raise
                delay = exc.retry_after if exc.retry_after is not None else self.delays[attempt]
                self.sleep(delay)
        raise RuntimeError("retry policy exhausted without a result")
