import json
from pathlib import Path
from typing import Optional
def load_manifest(path: Optional[Path] = None) -> dict:
    path = path or Path(__file__).parents[3] / "config" / "models.json"
    return json.loads(path.read_text(encoding="utf-8"))
