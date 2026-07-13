from typing import Any

from elevenlabs.client import ElevenLabs

from ugc_video.domain import FailureKind, ProviderHealth, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError


class ElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self, api_key: str, client: Any | None = None) -> None:
        self._api_key = api_key
        self.client = client or ElevenLabs(api_key=api_key)

    def health(self) -> ProviderHealth:
        try:
            subscription = self.client.user.get_subscription()
            limit = float(getattr(subscription, "character_limit", 0))
            used = float(getattr(subscription, "character_count", 0))
            return ProviderHealth(provider=self.name, ok=True, detail=f"tier={getattr(subscription, 'tier', 'unknown')}", remaining=max(limit - used, 0))
        except Exception as exc:
            return ProviderHealth(provider=self.name, ok=False, detail=type(exc).__name__)

    def list_voices(self) -> dict[str, str]:
        try:
            return {str(item.voice_id): str(getattr(item, "name", item.voice_id)) for item in self.client.voices.get_all().voices}
        except Exception as exc:
            raise ProviderError(FailureKind.AUTHENTICATION, "ElevenLabs voice lookup failed") from exc

    def validate_voice(self, voice_id: str) -> None:
        if voice_id not in self.list_voices():
            raise ProviderError(FailureKind.CONFIGURATION, "ElevenLabs voice ID is unavailable")

    def synthesize(self, request: VoiceRequest) -> VoiceResult:
        try:
            chunks = self.client.text_to_speech.convert(voice_id=request.voice_id, output_format="mp3_44100_128", text=request.text, model_id=request.model)
            audio = b"".join(chunks)
        except Exception as exc:
            message = str(exc).lower()
            if "quota" in message or "credit" in message:
                kind = FailureKind.QUOTA
            elif "401" in message or "unauthorized" in message:
                kind = FailureKind.AUTHENTICATION
            elif "policy" in message:
                kind = FailureKind.POLICY
            else:
                kind = FailureKind.TRANSIENT
            raise ProviderError(kind, f"ElevenLabs generation failed: {type(exc).__name__}") from exc
        if not audio:
            raise ProviderError(FailureKind.TRANSIENT, "ElevenLabs returned empty audio")
        request.destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = request.destination.with_suffix(request.destination.suffix + ".part")
        temporary.write_bytes(audio)
        temporary.replace(request.destination)
        return VoiceResult(provider=self.name, model=request.model, voice_id=request.voice_id, audio_path=request.destination)
