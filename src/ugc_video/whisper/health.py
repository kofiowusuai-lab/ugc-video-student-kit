from pathlib import Path
def health_fixture(path: Path) -> dict[str, object]:
    return {"exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}
