from pathlib import Path
import tomllib
from ugc_video.paths import config_dir, ensure_dirs
DEFAULT = "[pipeline]\nvoice_provider = 'fish'\n"
def config_file() -> Path: return config_dir() / "config.toml"
def load_config() -> dict:
    ensure_dirs(); p=config_file()
    if not p.exists(): p.write_text(DEFAULT, encoding="utf-8")
    return tomllib.loads(p.read_text(encoding="utf-8"))
