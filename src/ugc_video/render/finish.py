import subprocess
from collections.abc import Callable
from pathlib import Path

Runner = Callable[[list[str]], None]


def default_runner(command: list[str]) -> None:
    subprocess.run(command, check=True)


def finish_video(
    animation: Path, voice: Path, destination: Path, runner: Runner = default_runner
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".part.mp4")
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(animation),
        "-i",
        str(voice),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-af",
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(temporary),
    ]
    runner(command)
    temporary.replace(destination)
    return destination
