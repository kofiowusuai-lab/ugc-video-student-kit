import subprocess
from dataclasses import dataclass
from pathlib import Path

from ugc_video.audio.media import extract_audio, probe_duration, speech_window


@dataclass(frozen=True)
class FitDecision:
    action: str
    factor: float
    quality: str


def decide_fit(source_duration: float, target_duration: float) -> FitDecision:
    if source_duration <= 0 or target_duration <= 0:
        raise ValueError("audio durations must be positive")
    factor = target_duration / source_duration
    if 0.94 <= factor <= 1.06:
        return FitDecision("fit", factor, "preferred")
    if 0.90 <= factor <= 1.10:
        return FitDecision("fit", factor, "hard-limit")
    return FitDecision("regenerate-animation", factor, "unnatural")


def fit_audio(source: Path, target_video: Path, destination: Path) -> FitDecision:
    guide = destination.with_suffix(".guide.wav")
    extract_audio(target_video, guide)
    speech_start, speech_end = speech_window(guide)
    decision = decide_fit(probe_duration(source), speech_end - speech_start)
    if decision.action != "fit":
        guide.unlink(missing_ok=True)
        return decision
    stretched = destination.with_suffix(".stretched.wav")
    subprocess.run(
        [
            "rubberband",
            "--time",
            f"{decision.factor:.6f}",
            "--pitch",
            "1.0",
            str(source),
            str(stretched),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(stretched),
            "-af",
            f"adelay={round(speech_start * 1000)}:all=1,apad,atrim=0:{probe_duration(target_video):.6f}",
            str(destination),
        ],
        check=True,
    )
    stretched.unlink(missing_ok=True)
    guide.unlink(missing_ok=True)
    return decision
