from pathlib import Path

import pytest

from ugc_video.domain import FailureKind, ProviderHealth, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError
from ugc_video.providers.retry import RetryPolicy
from ugc_video.providers.voice_router import VoiceRouter


class FakeVoiceProvider:
    def __init__(self, name: str, outcomes: list[VoiceResult | Exception]) -> None:
        self.name = name
        self.outcomes = outcomes
        self.calls = 0

    def health(self) -> ProviderHealth:
        return ProviderHealth(provider=self.name, ok=True)

    def list_voices(self) -> dict[str, str]:
        return {"voice": "Voice"}

    def validate_voice(self, voice_id: str) -> None:
        return None

    def synthesize(self, request: VoiceRequest) -> VoiceResult:
        outcome = self.outcomes[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def request(tmp_path: Path) -> VoiceRequest:
    return VoiceRequest(
        text="Exact line.", voice_id="voice", model="model", destination=tmp_path / "voice.mp3"
    )


def test_transient_fish_failure_retries_twice_then_falls_back(tmp_path: Path) -> None:
    fish = FakeVoiceProvider("fish", [ProviderError(FailureKind.TRANSIENT, "down")] * 3)
    eleven = FakeVoiceProvider(
        "elevenlabs",
        [
            VoiceResult(
                provider="elevenlabs", model="m", voice_id="v", audio_path=tmp_path / "voice.mp3"
            )
        ],
    )
    router = VoiceRouter(fish, eleven, RetryPolicy(sleep=lambda _: None))
    result = router.synthesize("auto", request(tmp_path), request(tmp_path))
    assert result.provider == "elevenlabs"
    assert fish.calls == 3


def test_policy_failure_never_switches_provider(tmp_path: Path) -> None:
    fish = FakeVoiceProvider("fish", [ProviderError(FailureKind.POLICY, "blocked")])
    eleven = FakeVoiceProvider("elevenlabs", [])
    router = VoiceRouter(fish, eleven, RetryPolicy(sleep=lambda _: None))
    with pytest.raises(ProviderError, match="blocked"):
        router.synthesize("auto", request(tmp_path), request(tmp_path))
    assert eleven.calls == 0
