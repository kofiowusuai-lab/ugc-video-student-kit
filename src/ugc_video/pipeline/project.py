import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    brief: Path
    script: Path
    still: Path
    animation: Path
    voice: Path
    fitted_voice: Path
    final: Path
    manifest: Path


def project_paths(root: Path) -> ProjectPaths:
    return ProjectPaths(root=root, brief=root / "brief.json", script=root / "script.txt", still=root / "assets/still.png", animation=root / "work/animation.mp4", voice=root / "work/voice.mp3", fitted_voice=root / "work/voice-fitted.wav", final=root / "output/final.mp4", manifest=root / "run.json")


def create_project(root: Path, brief: dict[str, Any]) -> ProjectPaths:
    paths = project_paths(root)
    for directory in (paths.root, paths.still.parent, paths.animation.parent, paths.final.parent):
        directory.mkdir(parents=True, exist_ok=True)
    paths.brief.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
    return paths
