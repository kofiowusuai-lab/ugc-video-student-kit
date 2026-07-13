from pathlib import Path

import pytest

from ugc_video.whisper.manifest import build_inventory, verify_inventory
from ugc_video.whisper.router import AllBackendsFailed, transcribe_with_fallback
from ugc_video.whisper.types import Transcript


class FakeBackend:
    def __init__(self, name: str, transcript: str = "", error: str = "") -> None:
        self.name = name
        self.transcript = transcript
        self.error = error

    def transcribe(self, media: Path, language: str) -> Transcript:
        if self.error:
            raise RuntimeError(self.error)
        return Transcript(text=self.transcript, words=[])


def test_inventory_detects_changed_model(tmp_path: Path) -> None:
    model = tmp_path / "model.bin"
    model.write_bytes(b"healthy")
    inventory = build_inventory(tmp_path)
    model.write_bytes(b"broken")
    assert verify_inventory(tmp_path, inventory, deep=False).ok is False


def test_router_rejects_mismatch_and_uses_next_backend(tmp_path: Path) -> None:
    result = transcribe_with_fallback(
        [FakeBackend("first", "wrong"), FakeBackend("second", "exact line")],
        tmp_path / "fixture.wav",
        "en",
        expected_text="Exact line.",
    )
    assert result.backend == "second"
    assert result.attempts[0].status == "rejected"


def test_router_reports_every_failure(tmp_path: Path) -> None:
    with pytest.raises(AllBackendsFailed, match="first.*corrupt.*second.*timeout"):
        transcribe_with_fallback(
            [FakeBackend("first", error="corrupt"), FakeBackend("second", error="timeout")],
            tmp_path / "fixture.wav",
            "en",
        )
