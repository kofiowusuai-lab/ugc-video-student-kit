from typing import Literal

from ugc_video.domain import FailureKind, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError, VoiceProvider
from ugc_video.providers.retry import RetryPolicy

FALLBACK_KINDS = {
    FailureKind.AUTHENTICATION,
    FailureKind.CONFIGURATION,
    FailureKind.QUOTA,
    FailureKind.RATE_LIMIT,
    FailureKind.TRANSIENT,
}


class VoiceRouter:
    def __init__(self, fish: VoiceProvider, elevenlabs: VoiceProvider, retry: RetryPolicy) -> None:
        self.fish = fish
        self.elevenlabs = elevenlabs
        self.retry = retry

    @staticmethod
    def _generate(provider: VoiceProvider, request: VoiceRequest) -> VoiceResult:
        provider.validate_voice(request.voice_id)
        return provider.synthesize(request)

    def synthesize(
        self,
        provider: Literal["auto", "fish", "elevenlabs"],
        fish_request: VoiceRequest,
        elevenlabs_request: VoiceRequest,
    ) -> VoiceResult:
        if provider == "fish":
            return self.retry.run(lambda: self._generate(self.fish, fish_request))
        if provider == "elevenlabs":
            return self.retry.run(lambda: self._generate(self.elevenlabs, elevenlabs_request))
        try:
            return self.retry.run(lambda: self._generate(self.fish, fish_request))
        except ProviderError as exc:
            if exc.kind not in FALLBACK_KINDS:
                raise
            return self.retry.run(lambda: self._generate(self.elevenlabs, elevenlabs_request))
