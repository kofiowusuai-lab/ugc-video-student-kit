import json
from pathlib import Path

from typer.testing import CliRunner

from ugc_video.cli import app
from ugc_video.domain import ProviderHealth
from ugc_video.providers.voice_setup import choose_voice


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
