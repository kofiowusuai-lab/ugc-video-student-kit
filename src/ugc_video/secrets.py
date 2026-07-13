import os
from pathlib import Path

from ugc_video.paths import config_dir

ALLOWED_SECRET_NAMES = {"FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY", "XAI_API_KEY"}
NAMES = tuple(sorted(ALLOWED_SECRET_NAMES))


def read_secrets(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and name in ALLOWED_SECRET_NAMES and value:
            values[name] = value
    return values


def write_secret(path: Path, name: str, value: str) -> None:
    if name not in ALLOWED_SECRET_NAMES:
        raise ValueError(f"Unsupported secret name: {name}")
    if not value or "\n" in value or "\r" in value:
        raise ValueError(f"Invalid value for {name}")
    values = read_secrets(path)
    values[name] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        "".join(f"{key}={values[key]}\n" for key in sorted(values)), encoding="utf-8"
    )
    if os.name != "nt":
        temporary.chmod(0o600)
    temporary.replace(path)


def secret_file() -> Path:
    return config_dir() / "secrets.env"


def load_secrets() -> dict[str, str]:
    values = read_secrets(secret_file())
    values.update({name: value for name in NAMES if (value := os.getenv(name))})
    return values


def save_secrets(values: dict[str, str]) -> Path:
    path = secret_file()
    for name, value in values.items():
        write_secret(path, name, value)
    return path
