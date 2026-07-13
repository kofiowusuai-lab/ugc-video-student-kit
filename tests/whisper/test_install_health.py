import json
from pathlib import Path

import pytest

from ugc_video.paths import AppPaths
from ugc_video.whisper.backends import JsonSubprocessBackend
from ugc_video.whisper.health import inspect_whisper
from ugc_video.whisper.install import repair_model
from ugc_video.whisper.types import Transcript


def test_subprocess_backend_normalizes_json(tmp_path: Path) -> None:
    payload = {"text": "health check", "words": [{"text": "health", "start": 0, "end": 0.4}]}

    def runner(command: list[str], timeout: int) -> str:
        assert str(tmp_path / "fixture.wav") in command
        assert timeout == 180
        return json.dumps(payload)

    backend = JsonSubprocessBackend("faster-small-en", ["python", "worker.py"], 180, runner)
    result = backend.transcribe(tmp_path / "fixture.wav", "en")
    assert result == Transcript(text="health check", words=result.words)
    assert result.words[0].text == "health"


def test_deep_health_reports_three_backends(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path))
    monkeypatch.setattr("ugc_video.whisper.health.load_backends", lambda paths=None: [])
    checks = inspect_whisper(deep=True)
    assert checks[0].name == "whisper-model-manifest"
    assert checks[0].ok is False


def test_repair_rejects_unknown_backend_before_download(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "models.json"
    source.write_text('{"test-platform":[{"name":"known"}]}', encoding="utf-8")
    monkeypatch.setattr("ugc_video.whisper.install.platform_key", lambda: "test-platform")
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path / "home")})
    with pytest.raises(ValueError, match="Unknown Whisper backend unknown"):
        repair_model(paths, source, "unknown")
