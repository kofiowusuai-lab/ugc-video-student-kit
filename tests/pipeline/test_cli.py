import json
from pathlib import Path

from typer.testing import CliRunner

from ugc_video.cli import app
from ugc_video.config import load_config
from ugc_video.domain import ProviderHealth
from ugc_video.providers.voice_setup import choose_voice
from ugc_video.secrets import read_secrets


class FakeSetupVoiceProvider:
    def __init__(self, voices: dict[str, str]) -> None:
        self.voices = voices

    def list_voices(self) -> dict[str, str]:
        return self.voices


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


def test_setup_command_runs_full_wizard_without_exposing_private_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(
        "ugc_video.setup_wizard.build_voice_providers",
        lambda _: (
            FakeSetupVoiceProvider({"fish-private-id": "Warm Narrator"}),
            FakeSetupVoiceProvider({"eleven-private-id": "Clear Guide"}),
        ),
    )
    monkeypatch.setattr(
        "ugc_video.setup_wizard.provider_health",
        lambda _, name: ProviderHealth(provider=name, ok=True, detail="available"),
    )
    result = CliRunner().invoke(
        app,
        [
            "setup",
            "--fish-key",
            "fish-example-value",
            "--elevenlabs-key",
            "eleven-example-value",
            "--xai-key",
            "",
        ],
        input="1\n1\n",
    )
    assert result.exit_code == 0
    values = read_secrets(tmp_path / "home/secrets.env")
    assert set(values) == {"FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY"}
    config = load_config(tmp_path / "home/config.toml")
    assert config.fish_voice_id == "fish-private-id"
    assert config.elevenlabs_voice_id == "eleven-private-id"
    assert "Warm Narrator" in result.stdout
    assert "Clear Guide" in result.stdout
    assert "READY Voice setup is complete" in result.stdout
    for private_value in [
        "fish-example-value",
        "eleven-example-value",
        "fish-private-id",
        "eleven-private-id",
    ]:
        assert private_value not in result.stdout


def test_setup_help_does_not_advertise_command_line_key_values() -> None:
    result = CliRunner().invoke(app, ["setup", "--help"])
    assert result.exit_code == 0
    for unsafe_flag in ["--fish-key", "--elevenlabs-key", "--xai-key"]:
        assert unsafe_flag not in result.stdout
