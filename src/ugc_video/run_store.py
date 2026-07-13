import hashlib
import json
import threading
from pathlib import Path
from typing import Any

from ugc_video.domain import RunManifest, StageRecord, StageStatus, utc_now


def hash_inputs(paths: list[Path], values: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(values, sort_keys=True).encode("utf-8"))
    for path in sorted(paths):
        digest.update(str(path.resolve()).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


class RunStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()

    def load(self) -> RunManifest:
        with self._lock:
            return self._load_unlocked()

    def _load_unlocked(self) -> RunManifest:
        if not self.path.exists():
            return RunManifest(project=self.path.parent.name)
        return RunManifest.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, manifest: RunManifest) -> None:
        with self._lock:
            self._save_unlocked(manifest)

    def _save_unlocked(self, manifest: RunManifest) -> None:
        manifest.updated_at = utc_now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def start(self, name: str, input_hash: str) -> None:
        with self._lock:
            manifest = self._load_unlocked()
            previous = manifest.stages.get(name, StageRecord())
            manifest.stages[name] = StageRecord(
                status=StageStatus.RUNNING,
                input_hash=input_hash,
                attempts=previous.attempts + 1,
                started_at=utc_now(),
            )
            self._save_unlocked(manifest)

    def complete(
        self, name: str, input_hash: str, outputs: list[Path], metadata: dict[str, Any]
    ) -> None:
        with self._lock:
            manifest = self._load_unlocked()
            previous = manifest.stages.get(name, StageRecord())
            manifest.stages[name] = StageRecord(
                status=StageStatus.PASSED,
                input_hash=input_hash,
                outputs=outputs,
                attempts=max(previous.attempts, 1),
                started_at=previous.started_at,
                completed_at=utc_now(),
                metadata=metadata,
            )
            self._save_unlocked(manifest)

    def fail(self, name: str, detail: str) -> None:
        with self._lock:
            manifest = self._load_unlocked()
            record = manifest.stages.get(name, StageRecord(attempts=1))
            record.status = StageStatus.FAILED
            record.detail = detail
            record.completed_at = utc_now()
            manifest.stages[name] = record
            self._save_unlocked(manifest)

    def can_reuse(self, name: str, input_hash: str) -> bool:
        with self._lock:
            record = self._load_unlocked().stages.get(name)
            return bool(
                record
                and record.status == StageStatus.PASSED
                and record.input_hash == input_hash
                and record.outputs
                and all(path.exists() for path in record.outputs)
            )
