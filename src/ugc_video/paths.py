from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from platformdirs import user_cache_dir, user_config_dir, user_data_dir

APP = "ugc-video"


def config_dir() -> Path:
    return Path(user_config_dir(APP))


def data_dir() -> Path:
    return Path(user_data_dir(APP))


def cache_dir() -> Path:
    return Path(user_cache_dir(APP))


def ensure_dirs() -> None:
    for path in (config_dir(), data_dir(), cache_dir()):
        path.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class AppPaths:
    root: Path
    config: Path
    models: Path
    cache: Path
    runs: Path

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "AppPaths":
        override = environment.get("UGC_VIDEO_HOME")
        root = Path(override).expanduser() if override else data_dir()
        paths = cls(root, root / "config", root / "models", root / "cache", root / "runs")
        for path in (paths.root, paths.config, paths.models, paths.cache, paths.runs):
            path.mkdir(parents=True, exist_ok=True)
        return paths
