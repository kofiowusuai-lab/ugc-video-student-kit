from pathlib import Path

from ugc_video.pipeline.orchestrator import PipelineServices, run_pipeline
from ugc_video.pipeline.project import create_project


def test_new_project_has_explicit_creative_inputs(tmp_path: Path) -> None:
    project = create_project(tmp_path / "ad-one", {"product": "Demo", "cta": "Try it"})
    assert project.brief.exists()
    assert project.script == tmp_path / "ad-one/script.txt"
    assert project.still == tmp_path / "ad-one/assets/still.png"


def test_resume_does_not_repeat_completed_cloud_work(tmp_path: Path) -> None:
    project = create_project(tmp_path / "ad-two", {"product": "Demo", "cta": "Try it"})
    project.script.write_text("I had a feeling.", encoding="utf-8")
    project.still.parent.mkdir(parents=True, exist_ok=True)
    project.still.write_bytes(b"png")
    calls = {"animate": 0, "voice": 0, "verify": 0, "finish": 0}

    def make_services() -> PipelineServices:
        def animate(script: str, still: Path, output: Path) -> dict[str, str]:
            calls["animate"] += 1
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"video")
            return {"provider": "fake-grok"}

        def voice(script: str, output: Path) -> dict[str, str]:
            calls["voice"] += 1
            output.write_bytes(b"audio")
            return {"provider": "fish"}

        def verify(media: Path, expected: str) -> dict[str, str]:
            calls["verify"] += 1
            return {"backend": "fake-whisper", "text": expected}

        def finish(animation: Path, audio: Path, output: Path) -> dict[str, str]:
            calls["finish"] += 1
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"final")
            return {"renderer": "fake"}

        return PipelineServices(animate=animate, voice=voice, verify=verify, finish=finish)

    run_pipeline(project, make_services())
    run_pipeline(project, make_services())
    assert calls == {"animate": 1, "voice": 1, "verify": 2, "finish": 1}
