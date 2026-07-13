import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class IntegrityResult:
    ok: bool
    errors: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": str(path.relative_to(root)),
            "size": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def verify_inventory(root: Path, inventory: list[dict[str, object]], deep: bool) -> IntegrityResult:
    errors: list[str] = []
    for item in inventory:
        path = root / str(item["path"])
        if not path.is_file():
            errors.append(f"missing: {item['path']}")
            continue
        stat = path.stat()
        if stat.st_size != int(item["size"]):
            errors.append(f"size changed: {item['path']}")
            continue
        if stat.st_mtime_ns != int(item["mtime_ns"]):
            errors.append(f"timestamp changed: {item['path']}")
            continue
        if deep and sha256_file(path) != str(item["sha256"]):
            errors.append(f"checksum changed: {item['path']}")
    return IntegrityResult(ok=not errors, errors=errors)


def load_manifest(path: Optional[Path] = None) -> dict:
    path = path or Path(__file__).parents[3] / "config" / "models.json"
    return json.loads(path.read_text(encoding="utf-8"))
