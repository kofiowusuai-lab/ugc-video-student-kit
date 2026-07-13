import importlib
import json
import platform
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Set

from ugc_video.paths import AppPaths
from ugc_video.whisper.manifest import build_inventory


def platform_key() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    release = platform.release().lower()
    if system == "Darwin" and machine == "arm64":
        return "darwin-arm64"
    if system == "Linux" and "microsoft" in release:
        return "linux-wsl2"
    raise RuntimeError("Whisper installation supports Apple Silicon and WSL2 only")


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def install_models(paths: AppPaths, source_manifest: Path, force_names: Optional[Set[str]] = None) -> Path:
    definitions = json.loads(source_manifest.read_text(encoding="utf-8"))[platform_key()]
    installed: list[dict[str, object]] = []
    force_names = force_names or set()
    quarantines: dict[Path, Path] = {}
    try:
        for definition in definitions:
            destination = paths.models / definition["name"]
            if definition["name"] in force_names and destination.exists():
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                quarantine = destination.with_name(f"{destination.name}.corrupt-{stamp}")
                destination.replace(quarantine)
                quarantines[destination] = quarantine
            destination.mkdir(parents=True, exist_ok=True)
            if definition["kind"] == "whispercpp":
                target = destination / "ggml-small.en.bin"
                if not target.exists():
                    temporary = target.with_suffix(".part")
                    urllib.request.urlretrieve(definition["source"], temporary)
                    temporary.replace(target)
                revision = "downloaded-file-sha256"
            elif definition["kind"] == "huggingface":
                hub = importlib.import_module("huggingface_hub")
                revision = hub.HfApi().model_info(definition["source"]).sha
                hub.snapshot_download(repo_id=definition["source"], local_dir=destination, revision=revision)
            else:
                whisper = importlib.import_module("whisper")
                whisper.load_model(definition["source"], download_root=str(destination))
                revision = str(getattr(whisper, "__version__", "package-version-unavailable"))
            installed.append({**definition, "revision": revision, "inventory": build_inventory(destination)})
    except Exception:
        for destination, quarantine in quarantines.items():
            shutil.rmtree(destination, ignore_errors=True)
            quarantine.replace(destination)
        raise
    for quarantine in quarantines.values():
        shutil.rmtree(quarantine, ignore_errors=True)
    create_health_fixture(paths)
    manifest = paths.models / "manifest.json"
    atomic_json(manifest, {"platform": platform_key(), "models": installed})
    return manifest


def repair_model(paths: AppPaths, source_manifest: Path, name: str) -> Path:
    definitions = json.loads(source_manifest.read_text(encoding="utf-8"))[platform_key()]
    valid = {str(item["name"]) for item in definitions}
    if name not in valid:
        raise ValueError(f"Unknown Whisper backend {name}; choose one of {sorted(valid)}")
    return install_models(paths, source_manifest, force_names={name})


def create_health_fixture(paths: AppPaths) -> Path:
    fixture_root = paths.root / "fixtures"
    fixture_root.mkdir(parents=True, exist_ok=True)
    destination = fixture_root / "whisper-health.wav"
    if destination.exists():
        return destination
    if platform.system() == "Darwin":
        aiff = fixture_root / "whisper-health.aiff"
        subprocess.run(["say", "-o", str(aiff), "Whisper health check."], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), "-ar", "16000", "-ac", "1", str(destination)], check=True)
        aiff.unlink(missing_ok=True)
    else:
        subprocess.run(["espeak-ng", "-w", str(destination), "Whisper health check."], check=True)
    return destination
