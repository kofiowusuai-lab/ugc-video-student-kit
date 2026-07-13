import json
import os

from ugc_video.capabilities import Capability
from ugc_video.paths import AppPaths
from ugc_video.whisper.backends import load_backends
from ugc_video.whisper.manifest import verify_inventory
from ugc_video.whisper.router import normalize_text

FIXTURE_TEXT = "Whisper health check."


def inspect_whisper(deep: bool = False) -> list[Capability]:
    paths = AppPaths.from_environment(os.environ)
    manifest_path = paths.models / "manifest.json"
    if not manifest_path.exists():
        return [Capability("whisper-model-manifest", False, "", "run ugc-video whisper install")]
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [Capability("whisper-model-manifest", False, "", f"invalid manifest: {exc}")]
    checks = [Capability("whisper-model-manifest", True, str(manifest_path), "")]
    for item in payload.get("models", []):
        name = str(item["name"])
        integrity = verify_inventory(paths.models / name, item.get("inventory", []), deep=deep)
        checks.append(Capability(name, integrity.ok, str(paths.models / name), "; ".join(integrity.errors)))
    if not deep:
        return checks
    fixture = paths.root / "fixtures/whisper-health.wav"
    for backend in load_backends(paths):
        try:
            transcript = backend.transcribe(fixture, "en")
            ok = normalize_text(transcript.text) == normalize_text(FIXTURE_TEXT)
            checks.append(Capability(f"{backend.name}-deep", ok, transcript.text, "" if ok else "fixture transcript mismatch"))
        except Exception as exc:
            checks.append(Capability(f"{backend.name}-deep", False, "", str(exc)))
    return checks
