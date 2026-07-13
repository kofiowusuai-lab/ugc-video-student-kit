from pathlib import Path
from types import SimpleNamespace

import pytest

from ugc_video.audio.fit import FitDecision, decide_fit
from ugc_video.audio.media import speech_window
from ugc_video.transcription.exact import compare_dialogue


def test_dialogue_normalizes_punctuation_but_rejects_missing_content() -> None:
    assert compare_dialogue("I had a feeling.", "i had a feeling").ok is True
    mismatch = compare_dialogue("I had a feeling.", "Had a feeling.")
    assert mismatch.ok is False
    assert mismatch.missing == ["i"]


def test_fit_policy_prefers_small_change_and_rejects_robotic_factor() -> None:
    assert decide_fit(5.0, 5.2) == FitDecision("fit", pytest.approx(1.04), "preferred")
    assert decide_fit(5.0, 5.5) == FitDecision("fit", pytest.approx(1.10), "hard-limit")
    assert decide_fit(5.0, 6.0).action == "regenerate-animation"


def test_speech_window_removes_leading_and_trailing_silence(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("ugc_video.audio.media.probe_duration", lambda path: 6.0)
    monkeypatch.setattr(
        "ugc_video.audio.media.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            stderr="silence_start: 0\nsilence_end: 0.5\nsilence_start: 5.25\nsilence_end: 6.0\n"
        ),
    )
    assert speech_window(tmp_path / "guide.wav") == (0.5, 5.25)
