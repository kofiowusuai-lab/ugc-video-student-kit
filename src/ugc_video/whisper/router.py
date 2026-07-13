import re
import time
from pathlib import Path

from ugc_video.whisper.types import Attempt, RoutedTranscript, WhisperBackend


def normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


class AllBackendsFailed(RuntimeError):
    def __init__(self, attempts: list[Attempt]) -> None:
        self.attempts = attempts
        detail = "; ".join(f"{item.backend}: {item.detail}" for item in attempts)
        super().__init__(f"All Whisper backends failed: {detail}")


def transcribe_with_fallback(
    backends: list[WhisperBackend],
    media: Path,
    language: str,
    expected_text: str = "",
) -> RoutedTranscript:
    expected = normalize_text(expected_text) if expected_text else ""
    attempts: list[Attempt] = []
    for backend in backends:
        started = time.monotonic()
        try:
            transcript = backend.transcribe(media, language)
            normalized = normalize_text(transcript.text)
            elapsed = time.monotonic() - started
            if not normalized:
                attempts.append(Attempt(backend.name, "rejected", elapsed, "empty transcript"))
                continue
            if expected and normalized != expected:
                attempts.append(Attempt(backend.name, "rejected", elapsed, "expected text mismatch"))
                continue
            attempts.append(Attempt(backend.name, "succeeded", elapsed))
            return RoutedTranscript(backend.name, transcript, attempts)
        except Exception as exc:
            attempts.append(Attempt(backend.name, "failed", time.monotonic() - started, str(exc)))
    raise AllBackendsFailed(attempts)
