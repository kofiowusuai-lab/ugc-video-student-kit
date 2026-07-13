from typer.testing import CliRunner
import ugc_video
from ugc_video.cli import app


def test_package_and_cli_are_importable() -> None:
    assert ugc_video.__version__ == "0.1.2"
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ugc-video 0.1.2"
