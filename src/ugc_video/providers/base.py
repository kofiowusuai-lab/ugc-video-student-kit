from typing import Protocol

from ugc_video.domain import AnimationRequest, AnimationResult, FailureKind, ProviderHealth, VoiceRequest, VoiceResult


class ProviderError(RuntimeError):
    def __init__(self, kind: FailureKind, message: str, retry_after: float | None = None) -> None:
        self.kind = kind
        self.retry_after = retry_after
        super().__init__(message)


class VoiceProvider(Protocol):
    name: str
    def health(self) -> ProviderHealth: ...
    def list_voices(self) -> dict[str, str]: ...
    def validate_voice(self, voice_id: str) -> None: ...
    def synthesize(self, request: VoiceRequest) -> VoiceResult: ...


class AnimationProvider(Protocol):
    name: str
    def animate(self, request: AnimationRequest) -> AnimationResult: ...
