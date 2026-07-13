import os
import tomllib
from pathlib import Path
from typing import Literal

import tomli_w
from pydantic import BaseModel, ConfigDict, Field


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    voice_provider: Literal["auto", "fish", "elevenlabs"] = "auto"
    fish_model: str = "s2.1-pro-free"
    fish_voice_id: str = ""
    elevenlabs_model: str = "eleven_flash_v2_5"
    elevenlabs_voice_id: str = ""
    grok_mode: Literal["guided", "api"] = "guided"
    whisper_language: str = "en"
    preferred_time_factor_min: float = Field(default=0.94, ge=0.5, le=1.0)
    preferred_time_factor_max: float = Field(default=1.06, ge=1.0, le=2.0)
    hard_time_factor_min: float = Field(default=0.90, ge=0.5, le=1.0)
    hard_time_factor_max: float = Field(default=1.10, ge=1.0, le=2.0)


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()
    with path.open("rb") as stream:
        return AppConfig.model_validate(tomllib.load(stream))


def save_config(path: Path, config: AppConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(tomli_w.dumps(config.model_dump()), encoding="utf-8")
    if os.name != "nt":
        temporary.chmod(0o600)
    temporary.replace(path)
