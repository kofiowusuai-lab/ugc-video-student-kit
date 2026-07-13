import json
from pathlib import Path
from typing import cast


class RunStore:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def save(self, run_id: str, payload: dict[str, object]) -> Path:
        p = self.root / f"{run_id}.json"
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return p

    def load(self, run_id: str) -> dict[str, object]:
        payload = json.loads((self.root / f"{run_id}.json").read_text(encoding="utf-8"))
        return cast(dict[str, object], payload)
