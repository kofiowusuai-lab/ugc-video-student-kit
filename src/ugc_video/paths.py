from pathlib import Path
from platformdirs import user_config_dir, user_data_dir, user_cache_dir

APP = "ugc-video"
def config_dir() -> Path: return Path(user_config_dir(APP))
def data_dir() -> Path: return Path(user_data_dir(APP))
def cache_dir() -> Path: return Path(user_cache_dir(APP))
def ensure_dirs() -> None:
    for p in (config_dir(), data_dir(), cache_dir()): p.mkdir(parents=True, exist_ok=True)
