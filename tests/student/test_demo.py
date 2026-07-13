from pathlib import Path

from typer.testing import CliRunner

from ugc_video.cli import app
from ugc_video.demo import prepare_demo


def test_demo_copies_inputs_without_overwriting_run_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "assets").mkdir(parents=True)
    (source / "brief.json").write_text('{"product":"Student Kit"}\n', encoding="utf-8")
    (source / "script.txt").write_text(
        "I had a feeling this would save me time.\n", encoding="utf-8"
    )
    (source / "assets/presenter.png").write_bytes(b"png")
    project = prepare_demo(source, tmp_path / "demo-run")
    assert project.script.read_text().startswith("I had a feeling")
    assert project.still.read_bytes() == b"png"
    assert not project.manifest.exists()


def test_offline_demo_produces_final_media(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    result = CliRunner().invoke(app, ["demo", "--offline-fixtures"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "home/projects/demo/output/final.mp4").is_file()
