import re
import subprocess
from pathlib import Path


def run_media(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def probe_duration(path: Path) -> float:
    result = run_media(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(result.stdout.strip())


def normalize_wav(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_media(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ]
    )
    return destination


def extract_audio(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_media(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ]
    )
    return destination


def speech_window(audio: Path) -> tuple[float, float]:
    duration = probe_duration(audio)
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(audio),
            "-af",
            "silencedetect=noise=-35dB:d=0.20",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    starts = [float(value) for value in re.findall(r"silence_start:\s*([\d.]+)", result.stderr)]
    ends = [float(value) for value in re.findall(r"silence_end:\s*([\d.]+)", result.stderr)]
    speech_start = ends[0] if starts and ends and starts[0] <= 0.05 else 0.0
    speech_end = duration
    if starts and len(starts) > len(ends):
        speech_end = starts[-1]
    elif starts and ends and ends[-1] >= duration - 0.05:
        speech_end = starts[-1]
    if speech_end <= speech_start:
        raise ValueError("no usable speech window detected")
    return speech_start, speech_end
