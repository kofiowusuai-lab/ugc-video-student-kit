from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Transcript:
    text: str
    backend: str

class WhisperRouter:
    def __init__(self, backends: list[Callable[[str], Transcript]]): self.backends=backends
    def transcribe(self, audio: str) -> Transcript:
        errors=[]
        for backend in self.backends:
            try: return backend(audio)
            except Exception as exc: errors.append(str(exc))
        raise RuntimeError("all whisper backends failed: " + "; ".join(errors))
