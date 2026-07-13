import os
from pathlib import Path
from dotenv import dotenv_values
from ugc_video.paths import config_dir, ensure_dirs

NAMES = ("FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY", "XAI_API_KEY")


def secret_file() -> Path:
    return config_dir() / "secrets.env"


def load_secrets() -> dict[str, str]:
    vals = {k: v for k, v in dotenv_values(secret_file()).items() if v}
    vals.update({k: v for k in NAMES if (v := os.getenv(k))})
    return vals


def save_secrets(values: dict[str, str]) -> Path:
    ensure_dirs()
    p = secret_file()
    p.write_text("".join(f"{k}={v}\n" for k, v in values.items() if k in NAMES), encoding="utf-8")
    p.chmod(0o600)
    return p
