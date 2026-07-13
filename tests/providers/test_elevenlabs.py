from pathlib import Path
from types import SimpleNamespace

import pytest

from ugc_video.domain import FailureKind, VoiceRequest
from ugc_video.providers.base import ProviderError
from ugc_video.providers.elevenlabs import ElevenLabsProvider


class FakeElevenClient:
    def __init__(self) -> None:
        self.voices = SimpleNamespace(
            get_all=lambda: SimpleNamespace(voices=[SimpleNamespace(voice_id="v1", name="Demo")])
        )
        self.user = SimpleNamespace(
            get_subscription=lambda: SimpleNamespace(character_limit=10_000, character_count=125)
        )
        self.text_to_speech = SimpleNamespace(convert=lambda **kwargs: iter([b"ID3", b"audio"]))


def test_health_voice_validation_and_atomic_audio(tmp_path: Path) -> None:
    provider = ElevenLabsProvider("secret", client=FakeElevenClient())
    assert provider.health().remaining == 9_875
    provider.validate_voice("v1")
    result = provider.synthesize(
        VoiceRequest(
            text="Exact line.",
            voice_id="v1",
            model="eleven_flash_v2_5",
            destination=tmp_path / "voice.mp3",
        )
    )
    assert result.audio_path.read_bytes() == b"ID3audio"


class FailingVoiceClient:
    def __init__(self, error: Exception) -> None:
        self.voices = SimpleNamespace(get_all=lambda: (_ for _ in ()).throw(error))


@pytest.mark.parametrize(
    ("error", "expected_kind"),
    [
        (RuntimeError("401 unauthorized"), FailureKind.AUTHENTICATION),
        (TimeoutError("private endpoint detail"), FailureKind.TRANSIENT),
    ],
)
def test_voice_lookup_normalizes_sdk_failures(
    error: Exception, expected_kind: FailureKind
) -> None:
    provider = ElevenLabsProvider("secret", client=FailingVoiceClient(error))
    with pytest.raises(ProviderError) as captured:
        provider.list_voices()
    assert captured.value.kind == expected_kind
    assert "private endpoint detail" not in str(captured.value)
