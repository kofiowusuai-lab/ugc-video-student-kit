import platform, shutil
def discover() -> dict[str, object]:
    return {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version(), "ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"), "uv": shutil.which("uv"), "node": shutil.which("node")}
