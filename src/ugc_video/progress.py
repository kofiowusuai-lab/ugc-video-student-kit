import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TextIO

from ugc_video.redaction import redact


@dataclass
class ProgressReporter:
    stream: TextIO = sys.stderr
    clock: Callable[[], float] = time.monotonic
    secrets: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.started_at = self.clock()

    def _emit(self, stage: str, message: str) -> None:
        elapsed = self.clock() - self.started_at
        self.stream.write(f"[{elapsed:.2f}s] {stage}: {redact(message, self.secrets)}\n")
        self.stream.flush()

    def start(self, stage: str, message: str) -> None:
        self._emit(stage, message)

    def update(self, stage: str, message: str) -> None:
        self._emit(stage, message)

    def complete(self, stage: str, message: str) -> None:
        self._emit(stage, message)
