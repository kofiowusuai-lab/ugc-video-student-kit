from pathlib import Path

import httpx
import pytest
import respx

from ugc_video.domain import FailureKind, VoiceRequest
from ugc_video.providers.base import ProviderError
from ugc_video.providers.fish import FishAudioProvider


@respx.mock
def test_lists_only_bookmarked_voices_and_synthesizes_free_model(tmp_path: Path) -> None:
    respx.get("https://api.fish.audio/model").mock(return_value=httpx.Response(200, json={"items": [{"_id": "a", "title": "Saved", "marked": True}, {"_id": "b", "title": "Other", "marked": False}], "has_more": False}))
    tts = respx.post("https://api.fish.audio/v1/tts").mock(return_value=httpx.Response(200, content=b"ID3audio"))
    provider = FishAudioProvider("fish-key")
    assert provider.bookmarked_voices() == {"a": "Saved"}
    result = provider.synthesize(VoiceRequest(text="Exact line.", voice_id="a", model="s2.1-pro-free", destination=tmp_path / "voice.mp3"))
    assert result.audio_path.read_bytes() == b"ID3audio"
    assert tts.calls[0].request.headers["model"] == "s2.1-pro-free"
    assert "fish-key" not in repr(result)


@respx.mock
def test_quota_error_is_classified_for_fallback(tmp_path: Path) -> None:
    respx.post("https://api.fish.audio/v1/tts").mock(return_value=httpx.Response(429, json={"message": "quota reached"}))
    with pytest.raises(ProviderError) as captured:
        FishAudioProvider("secret").synthesize(VoiceRequest(text="Line", voice_id="a", model="s2.1-pro-free", destination=tmp_path / "voice.mp3"))
    assert captured.value.kind == FailureKind.RATE_LIMIT
    assert "secret" not in str(captured.value)
