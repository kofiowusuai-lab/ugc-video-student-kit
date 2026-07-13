import json
from pathlib import Path

from typer.testing import CliRunner

from ugc_video.cli import app
from ugc_video.domain import ProviderHealth
from ugc_video.providers.voice_setup import choose_voice
from ugc_video.secrets import read_secrets


def test_new_and_status_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    result = CliRunner().invoke(app, ["new", "demo-ad", "--product", "Demo", "--cta", "Try it"])
    assert result.exit_code == 0
    project = tmp_path / "home/projects/demo-ad"
    assert json.loads((project / "brief.json").read_text())["product"] == "Demo"
    status = CliRunner().invoke(app, ["status", str(project)])
    assert status.exit_code == 0
    assert "No stages have run" in status.stdout


def test_provider_doctor_is_non_billable_and_actionable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(
        "ugc_video.cli.provider_health",
        lambda secrets, name: ProviderHealth(provider=name, ok=False, detail="key missing"),
    )
    result = CliRunner().invoke(app, ["doctor", "--provider", "fish"])
    assert result.exit_code == 2
    assert "FAIL fish: key missing" in result.stdout


def test_voice_choice_uses_displayed_number_without_exposing_id() -> None:
    output: list[str] = []
    chosen = choose_voice(
        "Fish Audio",
        {"private-id": "Natural Voice"},
        input_fn=lambda prompt: "1",
        output_fn=output.append,
    )
    assert chosen == "private-id"
    assert "Natural Voice" in "\n".join(output)
    assert "private-id" not in "\n".join(output)


def test_setup_saves_keys_only_in_local_secret_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    result = CliRunner().invoke(
        app,
        [
            "setup",
            "--fish-key",
            "fish-test-key",
            "--elevenlabs-key",
            "eleven-test-key",
            "--xai-key",
            "xai-test-key",
        ],
    )
    assert result.exit_code == 0
    values = read_secrets(tmp_path / "home/secrets.env")
    assert set(values) == {"FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY", "XAI_API_KEY"}
    assert "fish-test-key" not in result.stdout
