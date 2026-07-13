from dataclasses import dataclass
import platform
import shutil


@dataclass(frozen=True)
class Capability:
    name: str
    ok: bool
    value: str
    detail: str


def discover() -> dict[str, object]:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "uv": shutil.which("uv"),
        "node": shutil.which("node"),
    }
