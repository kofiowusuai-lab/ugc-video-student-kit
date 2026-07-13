from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Transcript:
    text: str
    words: list[Word] = field(default_factory=list)


@dataclass(frozen=True)
class Attempt:
    backend: str
    status: str
    elapsed_seconds: float
    detail: str = ""


@dataclass(frozen=True)
class RoutedTranscript:
    backend: str
    transcript: Transcript
    attempts: list[Attempt] = field(default_factory=list)


class WhisperBackend(Protocol):
    name: str

    def transcribe(self, media: Path, language: str) -> Transcript: ...
