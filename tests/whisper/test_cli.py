from typer.testing import CliRunner

from ugc_video.cli import app


def test_whisper_cli_exposes_install_health_and_repair() -> None:
    result = CliRunner().invoke(app, ["whisper", "--help"])
    assert result.exit_code == 0
    assert "install" in result.stdout
    assert "health" in result.stdout
    assert "repair" in result.stdout
