from typer.testing import CliRunner

from ugc_video.cli import app


def test_doctor_accepts_explicit_fast_mode() -> None:
    result = CliRunner().invoke(app, ["doctor", "--fast", "--json"])
    assert result.exit_code == 0
    assert '"mode": "fast"' in result.stdout
