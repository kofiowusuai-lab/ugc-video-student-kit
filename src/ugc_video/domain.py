from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FailureKind(str, Enum):
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    QUOTA = "quota"
    RATE_LIMIT = "rate_limit"
    TRANSIENT = "transient"
    POLICY = "policy"
    CONSENT = "consent"
    LICENSING = "licensing"
    INVALID_MEDIA = "invalid_media"
    QA_REJECTION = "qa_rejection"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProviderHealth(BaseModel):
    provider: str
    ok: bool
    detail: str = ""
    remaining: float | None = None


class VoiceRequest(BaseModel):
    text: str
    voice_id: str
    model: str
    destination: Path


class VoiceResult(BaseModel):
    provider: str
    model: str
    voice_id: str
    audio_path: Path
    usage: dict[str, Any] = Field(default_factory=dict)


class AnimationRequest(BaseModel):
    image_path: Path
    prompt: str
    destination: Path
    duration_seconds: int = 8
    aspect_ratio: str = "9:16"
    resolution: str = "720p"


class AnimationResult(BaseModel):
    provider: str
    model: str
    video_path: Path
    request_id: str = ""
    usage: dict[str, Any] = Field(default_factory=dict)


class StageRecord(BaseModel):
    status: StageStatus = StageStatus.PENDING
    input_hash: str = ""
    outputs: list[Path] = Field(default_factory=list)
    attempts: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    detail: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunManifest(BaseModel):
    schema_version: int = 1
    project: str = ""
    stages: dict[str, StageRecord] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utc_now)
