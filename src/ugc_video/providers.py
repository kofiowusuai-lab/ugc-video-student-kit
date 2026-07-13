from dataclasses import dataclass
from typing import Protocol


class VoiceProvider(Protocol):
    name: str

    def synthesize(self, text: str, voice_id: str) -> bytes: ...


@dataclass
class VoiceRouter:
    primary: VoiceProvider
    fallback: VoiceProvider | None = None

    def synthesize(self, text: str, voice_id: str) -> tuple[bytes, str]:
        try:
            return self.primary.synthesize(text, voice_id), self.primary.name
        except (TimeoutError, ConnectionError, RuntimeError):
            if self.fallback is None:
                raise
            return self.fallback.synthesize(text, voice_id), self.fallback.name
