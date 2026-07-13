import json
import shutil
import subprocess
from pathlib import Path

from ugc_video.pipeline.orchestrator import PipelineServices
from ugc_video.pipeline.project import ProjectPaths, create_project
from ugc_video.render.finish import finish_video


def prepare_demo(source: Path, destination: Path) -> ProjectPaths:
    brief = json.loads((source / "brief.json").read_text(encoding="utf-8"))
    project = create_project(destination, brief)
    shutil.copy2(source / "script.txt", project.script)
    project.still.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "assets/presenter.png", project.still)
    return project


def build_offline_services() -> PipelineServices:
    def animate(script: str, still: Path, output: Path) -> dict[str, str]:
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-i",
                str(still),
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=2",
                "-t",
                "2",
                "-r",
                "30",
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(output),
            ],
            check=True,
        )
        return {"provider": "offline-fixture"}

    def voice(script: str, output: Path) -> dict[str, str]:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=220:duration=2",
                "-q:a",
                "4",
                str(output),
            ],
            check=True,
        )
        return {"provider": "offline-fixture"}

    def verify(media: Path, expected: str) -> dict[str, str]:
        if not media.is_file() or media.stat().st_size == 0:
            raise RuntimeError("offline fixture media is missing")
        return {"backend": "offline-fixture", "text": expected}

    def finish(animation: Path, audio: Path, output: Path) -> dict[str, str]:
        finish_video(animation, audio, output)
        return {"renderer": "ffmpeg-offline-fixture"}

    return PipelineServices(animate=animate, voice=voice, verify=verify, finish=finish)
