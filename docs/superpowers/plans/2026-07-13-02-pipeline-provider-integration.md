# UGC Pipeline and Provider Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $subagent-driven-development (recommended) or $executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a resumable local pipeline that accepts an approved script and still, animates through Grok, renders Fish Audio with ElevenLabs fallback, fits the voice naturally, verifies dialogue through local Whisper, and exports a vertical video.

**Architecture:** Provider adapters normalize vendor-specific errors and results behind small contracts. An atomic run store uses input hashes and output existence to decide whether a stage may be reused. Codex supplies creative artifacts through the bundled skill; the Python pipeline owns deterministic cloud calls, bounded retries, media operations, QA gates, and final output.

**Tech Stack:** Python 3.11, Pydantic, HTTPX, ElevenLabs Python SDK, xAI Imagine REST API, Fish Audio REST API, local Whisper router, FFmpeg/FFprobe, Rubber Band, Typer, Remotion, pytest, respx.

---

## File map

- `src/ugc_video/domain.py` — shared stage, provider, request, result, health, and failure types.
- `src/ugc_video/run_store.py` — atomic run manifests and reusable-stage decisions.
- `src/ugc_video/providers/base.py` — provider protocols and normalized exceptions.
- `src/ugc_video/providers/retry.py` — two-retry bounded policy.
- `src/ugc_video/providers/voice_router.py` — Fish-first routing and ElevenLabs fallback.
- `src/ugc_video/providers/fish.py` — Fish Audio bookmarks, health, and synthesis.
- `src/ugc_video/providers/elevenlabs.py` — ElevenLabs health, voice validation, and synthesis.
- `src/ugc_video/providers/grok.py` — guided and xAI API animation modes.
- `src/ugc_video/transcription/exact.py` — content-word dialogue gate.
- `src/ugc_video/audio/media.py` — FFmpeg/FFprobe wrappers.
- `src/ugc_video/audio/fit.py` — silence-aware, pitch-preserving duration fitting.
- `src/ugc_video/pipeline/project.py` — project creation and required creative inputs.
- `src/ugc_video/pipeline/orchestrator.py` — concurrent, checkpointed stage execution.
- `src/ugc_video/render/finish.py` — final FFmpeg and optional Remotion finishing.
- `remotion/` — vertical composition with captions and CTA props.
- `tests/providers/`, `tests/media/`, `tests/pipeline/` — mocked contracts and fixture media.

### Task 1: Domain contracts and atomic run store

**Files:**
- Create: `src/ugc_video/domain.py`
- Create: `src/ugc_video/run_store.py`
- Create: `tests/pipeline/test_run_store.py`

- [ ] **Step 1: Write failing checkpoint tests**

```python
from pathlib import Path

from ugc_video.domain import RunManifest, StageStatus
from ugc_video.run_store import RunStore, hash_inputs


def test_completed_stage_is_reused_only_when_hash_and_outputs_match(tmp_path: Path) -> None:
    script = tmp_path / "script.txt"
    output = tmp_path / "voice.mp3"
    script.write_text("Exact line.", encoding="utf-8")
    output.write_bytes(b"audio")
    store = RunStore(tmp_path / "run.json")
    digest = hash_inputs([script], {"voice": "fish-a"})
    store.complete("voice", digest, [output], {"provider": "fish"})
    assert store.can_reuse("voice", digest) is True
    script.write_text("Changed line.", encoding="utf-8")
    assert store.can_reuse("voice", hash_inputs([script], {"voice": "fish-a"})) is False


def test_failed_stage_retains_error_and_attempt_count(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "run.json")
    store.start("animation", "abc")
    store.fail("animation", "transient provider failure")
    manifest = RunManifest.model_validate_json((tmp_path / "run.json").read_text())
    assert manifest.stages["animation"].status == StageStatus.FAILED
    assert manifest.stages["animation"].attempts == 1
    assert "transient" in manifest.stages["animation"].detail
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/pipeline/test_run_store.py -q`

Expected: collection fails because `ugc_video.domain` does not exist.

- [ ] **Step 3: Create stable domain models**

`src/ugc_video/domain.py`:

```python
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
```

- [ ] **Step 4: Implement atomic run storage and hashing**

`src/ugc_video/run_store.py`:

```python
import hashlib
import json
import threading
from pathlib import Path
from typing import Any

from ugc_video.domain import RunManifest, StageRecord, StageStatus, utc_now


def hash_inputs(paths: list[Path], values: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(values, sort_keys=True).encode("utf-8"))
    for path in sorted(paths):
        digest.update(str(path.resolve()).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


class RunStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()

    def load(self) -> RunManifest:
        with self._lock:
            return self._load_unlocked()

    def _load_unlocked(self) -> RunManifest:
        if not self.path.exists():
            return RunManifest(project=self.path.parent.name)
        return RunManifest.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, manifest: RunManifest) -> None:
        with self._lock:
            self._save_unlocked(manifest)

    def _save_unlocked(self, manifest: RunManifest) -> None:
        manifest.updated_at = utc_now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def start(self, name: str, input_hash: str) -> None:
        with self._lock:
            manifest = self._load_unlocked()
            previous = manifest.stages.get(name, StageRecord())
            manifest.stages[name] = StageRecord(
                status=StageStatus.RUNNING,
                input_hash=input_hash,
                attempts=previous.attempts + 1,
                started_at=utc_now(),
            )
            self._save_unlocked(manifest)

    def complete(
        self,
        name: str,
        input_hash: str,
        outputs: list[Path],
        metadata: dict[str, Any],
    ) -> None:
        with self._lock:
            manifest = self._load_unlocked()
            previous = manifest.stages.get(name, StageRecord())
            manifest.stages[name] = StageRecord(
                status=StageStatus.PASSED,
                input_hash=input_hash,
                outputs=outputs,
                attempts=max(previous.attempts, 1),
                started_at=previous.started_at,
                completed_at=utc_now(),
                metadata=metadata,
            )
            self._save_unlocked(manifest)

    def fail(self, name: str, detail: str) -> None:
        with self._lock:
            manifest = self._load_unlocked()
            record = manifest.stages.get(name, StageRecord(attempts=1))
            record.status = StageStatus.FAILED
            record.detail = detail
            record.completed_at = utc_now()
            manifest.stages[name] = record
            self._save_unlocked(manifest)

    def can_reuse(self, name: str, input_hash: str) -> bool:
        with self._lock:
            record = self._load_unlocked().stages.get(name)
            return bool(
                record
                and record.status == StageStatus.PASSED
                and record.input_hash == input_hash
                and record.outputs
                and all(path.exists() for path in record.outputs)
            )
```

- [ ] **Step 5: Run GREEN and commit**

```bash
uv run pytest tests/pipeline/test_run_store.py -q
git add src/ugc_video/domain.py src/ugc_video/run_store.py tests/pipeline/test_run_store.py
git commit -m "feat: add atomic pipeline checkpoints"
```

Expected: two tests pass before the commit.

### Task 2: Provider errors, bounded retry, and voice routing

**Files:**
- Create: `src/ugc_video/providers/__init__.py`
- Create: `src/ugc_video/providers/base.py`
- Create: `src/ugc_video/providers/retry.py`
- Create: `src/ugc_video/providers/voice_router.py`
- Create: `tests/providers/test_retry_router.py`

- [ ] **Step 1: Write failing retry and fallback tests**

```python
from pathlib import Path

import pytest

from ugc_video.domain import FailureKind, ProviderHealth, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError
from ugc_video.providers.retry import RetryPolicy
from ugc_video.providers.voice_router import VoiceRouter


class FakeVoiceProvider:
    def __init__(self, name: str, outcomes: list[VoiceResult | Exception]) -> None:
        self.name = name
        self.outcomes = outcomes
        self.calls = 0

    def health(self) -> ProviderHealth:
        return ProviderHealth(provider=self.name, ok=True)

    def list_voices(self) -> dict[str, str]:
        return {"voice": "Voice"}

    def validate_voice(self, voice_id: str) -> None:
        return None

    def synthesize(self, request: VoiceRequest) -> VoiceResult:
        outcome = self.outcomes[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def request(tmp_path: Path) -> VoiceRequest:
    return VoiceRequest(text="Exact line.", voice_id="voice", model="model", destination=tmp_path / "voice.mp3")


def test_transient_fish_failure_retries_twice_then_falls_back(tmp_path: Path) -> None:
    fish = FakeVoiceProvider(
        "fish",
        [ProviderError(FailureKind.TRANSIENT, "down")] * 3,
    )
    eleven = FakeVoiceProvider(
        "elevenlabs",
        [VoiceResult(provider="elevenlabs", model="m", voice_id="v", audio_path=tmp_path / "voice.mp3")],
    )
    router = VoiceRouter(fish, eleven, RetryPolicy(sleep=lambda _: None))
    result = router.synthesize("auto", request(tmp_path), request(tmp_path))
    assert result.provider == "elevenlabs"
    assert fish.calls == 3


def test_policy_failure_never_switches_provider(tmp_path: Path) -> None:
    fish = FakeVoiceProvider("fish", [ProviderError(FailureKind.POLICY, "blocked")])
    eleven = FakeVoiceProvider("elevenlabs", [])
    router = VoiceRouter(fish, eleven, RetryPolicy(sleep=lambda _: None))
    with pytest.raises(ProviderError, match="blocked"):
        router.synthesize("auto", request(tmp_path), request(tmp_path))
    assert eleven.calls == 0
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/providers/test_retry_router.py -q`

Expected: collection fails because `ugc_video.providers.base` does not exist.

- [ ] **Step 3: Define provider contracts and normalized errors**

`src/ugc_video/providers/base.py`:

```python
from typing import Protocol

from ugc_video.domain import (
    AnimationRequest,
    AnimationResult,
    FailureKind,
    ProviderHealth,
    VoiceRequest,
    VoiceResult,
)


class ProviderError(RuntimeError):
    def __init__(self, kind: FailureKind, message: str, retry_after: float | None = None) -> None:
        self.kind = kind
        self.retry_after = retry_after
        super().__init__(message)


class VoiceProvider(Protocol):
    name: str

    def health(self) -> ProviderHealth:
        raise NotImplementedError

    def list_voices(self) -> dict[str, str]:
        raise NotImplementedError

    def validate_voice(self, voice_id: str) -> None:
        raise NotImplementedError

    def synthesize(self, request: VoiceRequest) -> VoiceResult:
        raise NotImplementedError


class AnimationProvider(Protocol):
    name: str

    def animate(self, request: AnimationRequest) -> AnimationResult:
        raise NotImplementedError
```

- [ ] **Step 4: Implement the two-retry policy**

`src/ugc_video/providers/retry.py`:

```python
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from ugc_video.domain import FailureKind
from ugc_video.providers.base import ProviderError


T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    delays: tuple[float, ...] = (2.0, 5.0)
    sleep: Callable[[float], None] = time.sleep

    def run(self, operation: Callable[[], T]) -> T:
        for attempt in range(self.max_attempts):
            try:
                return operation()
            except ProviderError as exc:
                retryable = exc.kind in {FailureKind.TRANSIENT, FailureKind.RATE_LIMIT}
                if not retryable or attempt + 1 >= self.max_attempts:
                    raise
                delay = exc.retry_after if exc.retry_after is not None else self.delays[attempt]
                self.sleep(delay)
        raise RuntimeError("retry policy exhausted without a result")
```

- [ ] **Step 5: Implement Fish-first routing with policy-safe fallback**

`src/ugc_video/providers/voice_router.py`:

```python
from typing import Literal

from ugc_video.domain import FailureKind, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError, VoiceProvider
from ugc_video.providers.retry import RetryPolicy


FALLBACK_KINDS = {
    FailureKind.AUTHENTICATION,
    FailureKind.CONFIGURATION,
    FailureKind.QUOTA,
    FailureKind.RATE_LIMIT,
    FailureKind.TRANSIENT,
}


class VoiceRouter:
    def __init__(
        self,
        fish: VoiceProvider,
        elevenlabs: VoiceProvider,
        retry: RetryPolicy,
    ) -> None:
        self.fish = fish
        self.elevenlabs = elevenlabs
        self.retry = retry

    @staticmethod
    def _generate(provider: VoiceProvider, request: VoiceRequest) -> VoiceResult:
        provider.validate_voice(request.voice_id)
        return provider.synthesize(request)

    def synthesize(
        self,
        provider: Literal["auto", "fish", "elevenlabs"],
        fish_request: VoiceRequest,
        elevenlabs_request: VoiceRequest,
    ) -> VoiceResult:
        if provider == "fish":
            return self.retry.run(lambda: self._generate(self.fish, fish_request))
        if provider == "elevenlabs":
            return self.retry.run(lambda: self._generate(self.elevenlabs, elevenlabs_request))
        try:
            return self.retry.run(lambda: self._generate(self.fish, fish_request))
        except ProviderError as exc:
            if exc.kind not in FALLBACK_KINDS:
                raise
            return self.retry.run(lambda: self._generate(self.elevenlabs, elevenlabs_request))
```

- [ ] **Step 6: Run GREEN and commit**

```bash
uv run pytest tests/providers/test_retry_router.py -q
git add src/ugc_video/providers tests/providers/test_retry_router.py
git commit -m "feat: add bounded voice provider routing"
```

Expected: two tests pass; Fish is called exactly three times in the retry test.

### Task 3: Fish Audio provider

**Files:**
- Create: `src/ugc_video/providers/fish.py`
- Create: `tests/providers/test_fish.py`

- [ ] **Step 1: Write mocked Fish API tests**

```python
from pathlib import Path

import httpx
import pytest
import respx

from ugc_video.domain import FailureKind, VoiceRequest
from ugc_video.providers.base import ProviderError
from ugc_video.providers.fish import FishAudioProvider


@respx.mock
def test_lists_only_bookmarked_voices_and_synthesizes_free_model(tmp_path: Path) -> None:
    respx.get("https://api.fish.audio/model").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"_id": "a", "title": "Saved", "marked": True},
                    {"_id": "b", "title": "Other", "marked": False},
                ],
                "has_more": False,
            },
        )
    )
    tts = respx.post("https://api.fish.audio/v1/tts").mock(
        return_value=httpx.Response(200, content=b"ID3audio")
    )
    provider = FishAudioProvider("fish-key")
    assert provider.bookmarked_voices() == {"a": "Saved"}
    result = provider.synthesize(
        VoiceRequest(text="Exact line.", voice_id="a", model="s2.1-pro-free", destination=tmp_path / "voice.mp3")
    )
    assert result.audio_path.read_bytes() == b"ID3audio"
    assert tts.calls[0].request.headers["model"] == "s2.1-pro-free"
    assert "fish-key" not in repr(result)


@respx.mock
def test_quota_error_is_classified_for_fallback(tmp_path: Path) -> None:
    respx.post("https://api.fish.audio/v1/tts").mock(
        return_value=httpx.Response(429, json={"message": "quota reached"})
    )
    with pytest.raises(ProviderError) as captured:
        FishAudioProvider("secret").synthesize(
            VoiceRequest(text="Line", voice_id="a", model="s2.1-pro-free", destination=tmp_path / "voice.mp3")
        )
    assert captured.value.kind == FailureKind.RATE_LIMIT
    assert "secret" not in str(captured.value)
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/providers/test_fish.py -q`

Expected: collection fails because `ugc_video.providers.fish` does not exist.

- [ ] **Step 3: Implement Fish health, bookmark discovery, and synthesis**

`src/ugc_video/providers/fish.py`:

```python
from pathlib import Path

import httpx

from ugc_video.domain import FailureKind, ProviderHealth, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError


class FishAudioProvider:
    name = "fish"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.fish.audio",
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=60)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def _raise(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            kind = FailureKind.AUTHENTICATION
        elif response.status_code == 429:
            kind = FailureKind.RATE_LIMIT
        elif response.status_code >= 500:
            kind = FailureKind.TRANSIENT
        else:
            body = response.text.lower()
            kind = FailureKind.POLICY if "policy" in body else FailureKind.CONFIGURATION
        raise ProviderError(kind, f"Fish Audio request failed with HTTP {response.status_code}")

    def bookmarked_voices(self) -> dict[str, str]:
        voices: dict[str, str] = {}
        for page in range(1, 101):
            response = self.client.get(
                f"{self.base_url}/model",
                params={"page_size": 100, "page_number": page},
                headers=self.headers,
            )
            if response.is_error:
                self._raise(response)
            payload = response.json()
            for item in payload.get("items", []):
                if item.get("marked") is True and item.get("_id"):
                    voices[str(item["_id"])] = str(item.get("title") or item["_id"])
            if payload.get("has_more") is not True:
                return voices
        raise ProviderError(FailureKind.CONFIGURATION, "Fish Audio pagination exceeded 100 pages")

    def health(self) -> ProviderHealth:
        try:
            count = len(self.bookmarked_voices())
            return ProviderHealth(provider=self.name, ok=True, detail=f"{count} bookmarked voices")
        except ProviderError as exc:
            return ProviderHealth(provider=self.name, ok=False, detail=str(exc))

    def list_voices(self) -> dict[str, str]:
        return self.bookmarked_voices()

    def validate_voice(self, voice_id: str) -> None:
        if voice_id not in self.bookmarked_voices():
            raise ProviderError(FailureKind.CONFIGURATION, "Fish Audio voice is not bookmarked")

    def synthesize(self, request: VoiceRequest) -> VoiceResult:
        response = self.client.post(
            f"{self.base_url}/v1/tts",
            headers={**self.headers, "Content-Type": "application/json", "model": request.model},
            json={"text": request.text, "reference_id": request.voice_id, "format": "mp3"},
        )
        if response.is_error:
            self._raise(response)
        if not response.content:
            raise ProviderError(FailureKind.TRANSIENT, "Fish Audio returned empty audio")
        request.destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = request.destination.with_suffix(request.destination.suffix + ".part")
        temporary.write_bytes(response.content)
        temporary.replace(request.destination)
        return VoiceResult(
            provider=self.name,
            model=request.model,
            voice_id=request.voice_id,
            audio_path=request.destination,
        )
```

- [ ] **Step 4: Run GREEN and commit**

```bash
uv run pytest tests/providers/test_fish.py -q
git add src/ugc_video/providers/fish.py tests/providers/test_fish.py
git commit -m "feat: integrate Fish Audio primary voice"
```

Expected: two tests pass and no secret appears in assertion output.

### Task 4: ElevenLabs fallback provider

**Files:**
- Modify: `pyproject.toml`
- Create: `src/ugc_video/providers/elevenlabs.py`
- Create: `tests/providers/test_elevenlabs.py`

- [ ] **Step 1: Add the official SDK and mock dependency**

Add to `[project].dependencies`:

```text
"elevenlabs>=2,<3",
```

Add to `[project.optional-dependencies].dev`:

```text
"respx>=0.22,<1",
```

Run:

```bash
uv lock
uv sync --extra dev --extra mac-whisper
```

Expected: lock and sync exit `0`.

- [ ] **Step 2: Write failing ElevenLabs adapter tests**

```python
from pathlib import Path
from types import SimpleNamespace

from ugc_video.domain import VoiceRequest
from ugc_video.providers.elevenlabs import ElevenLabsProvider


class FakeElevenClient:
    def __init__(self) -> None:
        self.voices = SimpleNamespace(
            get_all=lambda: SimpleNamespace(voices=[SimpleNamespace(voice_id="v1", name="Demo")])
        )
        self.user = SimpleNamespace(
            get_subscription=lambda: SimpleNamespace(character_limit=10_000, character_count=125)
        )
        self.text_to_speech = SimpleNamespace(
            convert=lambda **kwargs: iter([b"ID3", b"audio"])
        )


def test_health_voice_validation_and_atomic_audio(tmp_path: Path) -> None:
    provider = ElevenLabsProvider("secret", client=FakeElevenClient())
    assert provider.health().remaining == 9_875
    provider.validate_voice("v1")
    result = provider.synthesize(
        VoiceRequest(
            text="Exact line.",
            voice_id="v1",
            model="eleven_flash_v2_5",
            destination=tmp_path / "voice.mp3",
        )
    )
    assert result.audio_path.read_bytes() == b"ID3audio"
```

- [ ] **Step 3: Run the test and verify RED**

Run: `uv run pytest tests/providers/test_elevenlabs.py -q`

Expected: collection fails because `ugc_video.providers.elevenlabs` does not exist.

- [ ] **Step 4: Implement the official ElevenLabs SDK adapter**

`src/ugc_video/providers/elevenlabs.py`:

```python
from typing import Any

from elevenlabs.client import ElevenLabs

from ugc_video.domain import FailureKind, ProviderHealth, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError


class ElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self, api_key: str, client: Any | None = None) -> None:
        self._api_key = api_key
        self.client = client or ElevenLabs(api_key=api_key)

    def health(self) -> ProviderHealth:
        try:
            subscription = self.client.user.get_subscription()
            limit = float(getattr(subscription, "character_limit", 0))
            used = float(getattr(subscription, "character_count", 0))
            return ProviderHealth(
                provider=self.name,
                ok=True,
                detail=f"tier={getattr(subscription, 'tier', 'unknown')}",
                remaining=max(limit - used, 0),
            )
        except Exception as exc:
            return ProviderHealth(provider=self.name, ok=False, detail=type(exc).__name__)

    def list_voices(self) -> dict[str, str]:
        try:
            return {
                str(item.voice_id): str(getattr(item, "name", item.voice_id))
                for item in self.client.voices.get_all().voices
            }
        except Exception as exc:
            raise ProviderError(FailureKind.AUTHENTICATION, "ElevenLabs voice lookup failed") from exc

    def validate_voice(self, voice_id: str) -> None:
        if voice_id not in self.list_voices():
            raise ProviderError(FailureKind.CONFIGURATION, "ElevenLabs voice ID is unavailable")

    def synthesize(self, request: VoiceRequest) -> VoiceResult:
        try:
            chunks = self.client.text_to_speech.convert(
                voice_id=request.voice_id,
                output_format="mp3_44100_128",
                text=request.text,
                model_id=request.model,
            )
            audio = b"".join(chunks)
        except Exception as exc:
            message = str(exc).lower()
            if "quota" in message or "credit" in message:
                kind = FailureKind.QUOTA
            elif "401" in message or "unauthorized" in message:
                kind = FailureKind.AUTHENTICATION
            elif "policy" in message:
                kind = FailureKind.POLICY
            else:
                kind = FailureKind.TRANSIENT
            raise ProviderError(kind, f"ElevenLabs generation failed: {type(exc).__name__}") from exc
        if not audio:
            raise ProviderError(FailureKind.TRANSIENT, "ElevenLabs returned empty audio")
        request.destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = request.destination.with_suffix(request.destination.suffix + ".part")
        temporary.write_bytes(audio)
        temporary.replace(request.destination)
        return VoiceResult(
            provider=self.name,
            model=request.model,
            voice_id=request.voice_id,
            audio_path=request.destination,
        )
```

- [ ] **Step 5: Run GREEN and commit**

```bash
uv run pytest tests/providers/test_elevenlabs.py tests/providers/test_retry_router.py -q
git add pyproject.toml uv.lock src/ugc_video/providers/elevenlabs.py tests/providers/test_elevenlabs.py
git commit -m "feat: add ElevenLabs voice fallback"
```

Expected: all ElevenLabs and routing tests pass.

### Task 5: Grok guided and automatic animation

**Files:**
- Create: `src/ugc_video/providers/grok.py`
- Create: `tests/providers/test_grok.py`

- [ ] **Step 1: Write mocked asynchronous Grok tests**

```python
from pathlib import Path

import httpx
import respx

from ugc_video.domain import AnimationRequest
from ugc_video.providers.grok import GrokApiProvider, GuidedGrokProvider


@respx.mock
def test_api_mode_persists_request_and_downloads_result(tmp_path: Path) -> None:
    image = tmp_path / "still.png"
    image.write_bytes(b"png")
    respx.post("https://api.x.ai/v1/videos/generations").mock(
        return_value=httpx.Response(200, json={"request_id": "req-1"})
    )
    respx.get("https://api.x.ai/v1/videos/req-1").mock(
        side_effect=[
            httpx.Response(200, json={"status": "pending", "progress": 25}),
            httpx.Response(200, json={"status": "done", "video": {"url": "https://cdn.test/video.mp4"}, "usage": {"cost": 1}}),
        ]
    )
    respx.get("https://cdn.test/video.mp4").mock(return_value=httpx.Response(200, content=b"video"))
    provider = GrokApiProvider("xai-key", sleep=lambda _: None)
    result = provider.animate(
        AnimationRequest(image_path=image, prompt="Say the exact line.", destination=tmp_path / "animation.mp4")
    )
    assert result.request_id == "req-1"
    assert result.video_path.read_bytes() == b"video"


def test_guided_mode_writes_handoff_without_fake_output(tmp_path: Path) -> None:
    image = tmp_path / "still.png"
    image.write_bytes(b"png")
    provider = GuidedGrokProvider(tmp_path / "handoff.json")
    result = provider.prepare(
        AnimationRequest(image_path=image, prompt="Natural movement", destination=tmp_path / "animation.mp4")
    )
    assert result == tmp_path / "handoff.json"
    assert not (tmp_path / "animation.mp4").exists()
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/providers/test_grok.py -q`

Expected: collection fails because `ugc_video.providers.grok` does not exist.

- [ ] **Step 3: Implement Grok API and guided handoff adapters**

`src/ugc_video/providers/grok.py`:

```python
import base64
import json
import time
from collections.abc import Callable
from pathlib import Path

import httpx

from ugc_video.domain import AnimationRequest, AnimationResult, FailureKind
from ugc_video.providers.base import ProviderError


class GrokApiProvider:
    name = "grok-api"

    def __init__(
        self,
        api_key: str,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_polls: int = 120,
    ) -> None:
        self._api_key = api_key
        self.client = client or httpx.Client(timeout=90)
        self.sleep = sleep
        self.max_polls = max_polls

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def animate(self, request: AnimationRequest) -> AnimationResult:
        mime = "image/png" if request.image_path.suffix.lower() == ".png" else "image/jpeg"
        encoded = base64.b64encode(request.image_path.read_bytes()).decode("ascii")
        response = self.client.post(
            "https://api.x.ai/v1/videos/generations",
            headers=self.headers,
            json={
                "model": "grok-imagine-video",
                "prompt": request.prompt,
                "image": {"url": f"data:{mime};base64,{encoded}"},
                "duration": request.duration_seconds,
                "aspect_ratio": request.aspect_ratio,
                "resolution": request.resolution,
            },
        )
        if response.is_error:
            self._raise(response)
        request_id = str(response.json()["request_id"])
        for _ in range(self.max_polls):
            poll = self.client.get(
                f"https://api.x.ai/v1/videos/{request_id}",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            if poll.is_error:
                self._raise(poll)
            payload = poll.json()
            if payload.get("status") == "done":
                media = self.client.get(payload["video"]["url"])
                media.raise_for_status()
                request.destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = request.destination.with_suffix(".part")
                temporary.write_bytes(media.content)
                temporary.replace(request.destination)
                return AnimationResult(
                    provider=self.name,
                    model=str(payload.get("model", "grok-imagine-video")),
                    video_path=request.destination,
                    request_id=request_id,
                    usage=payload.get("usage", {}),
                )
            if payload.get("status") in {"failed", "expired"}:
                raise ProviderError(FailureKind.TRANSIENT, f"Grok video request {payload['status']}")
            self.sleep(5)
        raise ProviderError(FailureKind.TRANSIENT, "Grok video polling timed out")

    def _raise(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            kind = FailureKind.AUTHENTICATION
        elif response.status_code == 429:
            kind = FailureKind.RATE_LIMIT
        elif response.status_code >= 500:
            kind = FailureKind.TRANSIENT
        else:
            kind = FailureKind.CONFIGURATION
        raise ProviderError(kind, f"Grok request failed with HTTP {response.status_code}")


class GuidedGrokProvider:
    name = "grok-guided"

    def __init__(self, handoff_path: Path) -> None:
        self.handoff_path = handoff_path

    def prepare(self, request: AnimationRequest) -> Path:
        self.handoff_path.parent.mkdir(parents=True, exist_ok=True)
        self.handoff_path.write_text(
            json.dumps(
                {
                    "image": str(request.image_path.resolve()),
                    "prompt": request.prompt,
                    "destination": str(request.destination.resolve()),
                    "durationSeconds": request.duration_seconds,
                    "aspectRatio": request.aspect_ratio,
                    "resolution": request.resolution,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return self.handoff_path
```

- [ ] **Step 4: Run GREEN and commit**

```bash
uv run pytest tests/providers/test_grok.py -q
git add src/ugc_video/providers/grok.py tests/providers/test_grok.py
git commit -m "feat: add Grok animation modes"
```

Expected: two tests pass and the temporary media URL is downloaded locally.

### Task 6: Exact-dialogue gate and natural voice fitting

**Files:**
- Create: `src/ugc_video/transcription/__init__.py`
- Create: `src/ugc_video/transcription/exact.py`
- Create: `src/ugc_video/audio/__init__.py`
- Create: `src/ugc_video/audio/media.py`
- Create: `src/ugc_video/audio/fit.py`
- Create: `tests/media/test_exact_fit.py`

- [ ] **Step 1: Write failing dialogue and timing tests**

```python
from pathlib import Path
from types import SimpleNamespace

import pytest

from ugc_video.audio.fit import FitDecision, decide_fit
from ugc_video.audio.media import speech_window
from ugc_video.transcription.exact import compare_dialogue


def test_dialogue_normalizes_punctuation_but_rejects_missing_content() -> None:
    assert compare_dialogue("I had a feeling.", "i had a feeling").ok is True
    mismatch = compare_dialogue("I had a feeling.", "Had a feeling.")
    assert mismatch.ok is False
    assert mismatch.missing == ["i"]


def test_fit_policy_prefers_small_change_and_rejects_robotic_factor() -> None:
    assert decide_fit(5.0, 5.2) == FitDecision("fit", pytest.approx(1.04), "preferred")
    assert decide_fit(5.0, 5.5) == FitDecision("fit", pytest.approx(1.10), "hard-limit")
    assert decide_fit(5.0, 6.0).action == "regenerate-animation"


def test_speech_window_removes_leading_and_trailing_silence(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("ugc_video.audio.media.probe_duration", lambda path: 6.0)
    monkeypatch.setattr(
        "ugc_video.audio.media.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            stderr="silence_start: 0\nsilence_end: 0.5\nsilence_start: 5.25\nsilence_end: 6.0\n"
        ),
    )
    assert speech_window(tmp_path / "guide.wav") == (0.5, 5.25)
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/media/test_exact_fit.py -q`

Expected: collection fails because `ugc_video.audio.fit` does not exist.

- [ ] **Step 3: Implement the exact content-word comparison**

`src/ugc_video/transcription/exact.py`:

```python
import re
from dataclasses import dataclass


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower().replace("’", "'"))


@dataclass(frozen=True)
class DialogueComparison:
    ok: bool
    expected: list[str]
    actual: list[str]
    missing: list[str]
    unexpected: list[str]


def compare_dialogue(expected_text: str, actual_text: str) -> DialogueComparison:
    expected = words(expected_text)
    actual = words(actual_text)
    missing = [token for index, token in enumerate(expected) if index >= len(actual) or actual[index] != token]
    unexpected = [token for index, token in enumerate(actual) if index >= len(expected) or expected[index] != token]
    return DialogueComparison(not missing and not unexpected, expected, actual, missing, unexpected)
```

- [ ] **Step 4: Implement FFmpeg/FFprobe media wrappers**

`src/ugc_video/audio/media.py`:

```python
import re
import subprocess
from pathlib import Path


def run_media(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def probe_duration(path: Path) -> float:
    result = run_media(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ]
    )
    return float(result.stdout.strip())


def normalize_wav(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_media(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(destination),
        ]
    )
    return destination


def extract_audio(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_media(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-vn", "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(destination),
        ]
    )
    return destination


def speech_window(audio: Path) -> tuple[float, float]:
    duration = probe_duration(audio)
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", str(audio),
            "-af", "silencedetect=noise=-35dB:d=0.20", "-f", "null", "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    starts = [float(value) for value in re.findall(r"silence_start:\s*([\d.]+)", result.stderr)]
    ends = [float(value) for value in re.findall(r"silence_end:\s*([\d.]+)", result.stderr)]
    speech_start = ends[0] if starts and ends and starts[0] <= 0.05 else 0.0
    speech_end = duration
    if starts and len(starts) > len(ends):
        speech_end = starts[-1]
    elif starts and ends and ends[-1] >= duration - 0.05:
        speech_end = starts[-1]
    if speech_end <= speech_start:
        raise ValueError("no usable speech window detected")
    return speech_start, speech_end


def mux_voice(video: Path, audio: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_media(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-shortest", str(destination),
        ]
    )
    return destination
```

- [ ] **Step 5: Implement fit decisions and Rubber Band execution**

`src/ugc_video/audio/fit.py`:

```python
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ugc_video.audio.media import extract_audio, probe_duration, speech_window


@dataclass(frozen=True)
class FitDecision:
    action: str
    factor: float
    quality: str


def decide_fit(source_duration: float, target_duration: float) -> FitDecision:
    if source_duration <= 0 or target_duration <= 0:
        raise ValueError("audio durations must be positive")
    factor = target_duration / source_duration
    if 0.94 <= factor <= 1.06:
        return FitDecision("fit", factor, "preferred")
    if 0.90 <= factor <= 1.10:
        return FitDecision("fit", factor, "hard-limit")
    return FitDecision("regenerate-animation", factor, "unnatural")


def fit_audio(source: Path, target_video: Path, destination: Path) -> FitDecision:
    guide = destination.with_suffix(".guide.wav")
    extract_audio(target_video, guide)
    speech_start, speech_end = speech_window(guide)
    target_speech_duration = speech_end - speech_start
    decision = decide_fit(probe_duration(source), target_speech_duration)
    if decision.action != "fit":
        guide.unlink(missing_ok=True)
        return decision
    stretched = destination.with_suffix(".stretched.wav")
    subprocess.run(
        ["rubberband", "--time", f"{decision.factor:.6f}", "--pitch", "1.0", str(source), str(stretched)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(stretched),
            "-af",
            f"adelay={round(speech_start * 1000)}:all=1,apad,atrim=0:{probe_duration(target_video):.6f}",
            str(destination),
        ],
        check=True,
    )
    stretched.unlink(missing_ok=True)
    guide.unlink(missing_ok=True)
    return decision
```

- [ ] **Step 6: Run GREEN and commit**

```bash
uv run pytest tests/media/test_exact_fit.py -q
git add src/ugc_video/transcription src/ugc_video/audio tests/media/test_exact_fit.py
git commit -m "feat: add exact dialogue and natural timing gates"
```

Expected: two tests pass.

### Task 7: Project structure and checkpointed orchestration

**Files:**
- Create: `src/ugc_video/pipeline/__init__.py`
- Create: `src/ugc_video/pipeline/project.py`
- Create: `src/ugc_video/pipeline/orchestrator.py`
- Create: `tests/pipeline/test_orchestrator.py`

- [ ] **Step 1: Write failing project and resume tests**

```python
from pathlib import Path

from ugc_video.pipeline.orchestrator import PipelineServices, run_pipeline
from ugc_video.pipeline.project import create_project


def test_new_project_has_explicit_creative_inputs(tmp_path: Path) -> None:
    project = create_project(tmp_path / "ad-one", {"product": "Demo", "cta": "Try it"})
    assert project.brief.exists()
    assert project.script == tmp_path / "ad-one/script.txt"
    assert project.still == tmp_path / "ad-one/assets/still.png"


def test_resume_does_not_repeat_completed_cloud_work(tmp_path: Path) -> None:
    project = create_project(tmp_path / "ad-two", {"product": "Demo", "cta": "Try it"})
    project.script.write_text("I had a feeling.", encoding="utf-8")
    project.still.parent.mkdir(parents=True, exist_ok=True)
    project.still.write_bytes(b"png")
    calls = {"animate": 0, "voice": 0, "verify": 0, "finish": 0}

    def make_services() -> PipelineServices:
        def animate(script: str, still: Path, output: Path) -> dict[str, str]:
            calls["animate"] += 1
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"video")
            return {"provider": "fake-grok"}

        def voice(script: str, output: Path) -> dict[str, str]:
            calls["voice"] += 1
            output.write_bytes(b"audio")
            return {"provider": "fish"}

        def verify(media: Path, expected: str) -> dict[str, str]:
            calls["verify"] += 1
            return {"backend": "fake-whisper", "text": expected}

        def finish(animation: Path, audio: Path, output: Path) -> dict[str, str]:
            calls["finish"] += 1
            output.write_bytes(b"final")
            return {"renderer": "fake"}

        return PipelineServices(animate=animate, voice=voice, verify=verify, finish=finish)

    run_pipeline(project, make_services())
    run_pipeline(project, make_services())
    assert calls == {"animate": 1, "voice": 1, "verify": 2, "finish": 1}
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -q`

Expected: collection fails because `ugc_video.pipeline.project` does not exist.

- [ ] **Step 3: Implement the project layout**

`src/ugc_video/pipeline/project.py`:

```python
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    brief: Path
    script: Path
    still: Path
    animation: Path
    voice: Path
    fitted_voice: Path
    final: Path
    manifest: Path


def project_paths(root: Path) -> ProjectPaths:
    return ProjectPaths(
        root=root,
        brief=root / "brief.json",
        script=root / "script.txt",
        still=root / "assets/still.png",
        animation=root / "work/animation.mp4",
        voice=root / "work/voice.mp3",
        fitted_voice=root / "work/voice-fitted.wav",
        final=root / "output/final.mp4",
        manifest=root / "run.json",
    )


def create_project(root: Path, brief: dict[str, Any]) -> ProjectPaths:
    paths = project_paths(root)
    for directory in (paths.root, paths.still.parent, paths.animation.parent, paths.final.parent):
        directory.mkdir(parents=True, exist_ok=True)
    paths.brief.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
    return paths
```

- [ ] **Step 4: Implement concurrent cloud preparation and reusable outputs**

`src/ugc_video/pipeline/orchestrator.py`:

```python
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ugc_video.pipeline.project import ProjectPaths
from ugc_video.run_store import RunStore, hash_inputs


@dataclass(frozen=True)
class PipelineServices:
    animate: Callable[[str, Path, Path], dict[str, Any]]
    voice: Callable[[str, Path], dict[str, Any]]
    verify: Callable[[Path, str], dict[str, Any]]
    finish: Callable[[Path, Path, Path], dict[str, Any]]


def _run_stage(
    store: RunStore,
    name: str,
    digest: str,
    outputs: list[Path],
    operation: Callable[[], dict[str, Any]],
) -> None:
    if store.can_reuse(name, digest):
        return
    store.start(name, digest)
    try:
        metadata = operation()
        if not all(path.exists() and path.stat().st_size > 0 for path in outputs):
            raise RuntimeError(f"{name} produced no usable output")
        store.complete(name, digest, outputs, metadata)
    except Exception as exc:
        store.fail(name, str(exc))
        raise


def run_pipeline(project: ProjectPaths, services: PipelineServices) -> Path:
    if not project.script.is_file() or not project.script.read_text(encoding="utf-8").strip():
        raise RuntimeError("script.txt is missing; run the bundled Codex skill")
    if not project.still.is_file() or project.still.stat().st_size == 0:
        raise RuntimeError("assets/still.png is missing; run the bundled Codex skill")
    script = project.script.read_text(encoding="utf-8").strip()
    store = RunStore(project.manifest)
    animation_hash = hash_inputs([project.script, project.still], {"stage": "animation"})
    voice_hash = hash_inputs([project.script], {"stage": "voice"})

    with ThreadPoolExecutor(max_workers=2) as executor:
        animation_future = executor.submit(
            _run_stage,
            store,
            "animation",
            animation_hash,
            [project.animation],
            lambda: services.animate(script, project.still, project.animation),
        )
        voice_future = executor.submit(
            _run_stage,
            store,
            "voice",
            voice_hash,
            [project.voice],
            lambda: services.voice(script, project.voice),
        )
        animation_future.result()
        voice_future.result()

    verify_animation_hash = hash_inputs(
        [project.animation, project.script], {"stage": "verify-animation"}
    )
    _run_stage(
        store,
        "verify-animation",
        verify_animation_hash,
        [project.animation],
        lambda: services.verify(project.animation, script),
    )
    final_hash = hash_inputs([project.animation, project.voice, project.script], {"stage": "finish"})
    _run_stage(
        store,
        "finish",
        final_hash,
        [project.final],
        lambda: services.finish(project.animation, project.voice, project.final),
    )
    verify_final_hash = hash_inputs([project.final, project.script], {"stage": "verify-final"})
    _run_stage(
        store,
        "verify-final",
        verify_final_hash,
        [project.final],
        lambda: services.verify(project.final, script),
    )
    return project.final
```

- [ ] **Step 5: Run GREEN and commit**

```bash
uv run pytest tests/pipeline/test_orchestrator.py -q
git add src/ugc_video/pipeline tests/pipeline/test_orchestrator.py
git commit -m "feat: orchestrate resumable parallel production"
```

Expected: two tests pass; the second pipeline run does not call cloud work again.

### Task 8: Final rendering and Remotion composition

**Files:**
- Create: `src/ugc_video/render/__init__.py`
- Create: `src/ugc_video/render/finish.py`
- Create: `remotion/package.json`
- Create: `remotion/tsconfig.json`
- Create: `remotion/src/index.ts`
- Create: `remotion/src/Root.tsx`
- Create: `remotion/src/UgcVertical.tsx`
- Create: `tests/media/test_finish.py`

- [ ] **Step 1: Write the failing FFmpeg command test**

```python
from pathlib import Path

from ugc_video.render.finish import finish_video


def test_finish_uses_vertical_safe_audio_and_atomic_output(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    animation = tmp_path / "animation.mp4"
    voice = tmp_path / "voice.wav"
    destination = tmp_path / "final.mp4"
    animation.write_bytes(b"video")
    voice.write_bytes(b"audio")

    def runner(command: list[str]) -> None:
        commands.append(command)
        Path(command[-1]).write_bytes(b"final")

    finish_video(animation, voice, destination, runner=runner)
    assert destination.read_bytes() == b"final"
    assert "loudnorm=I=-16:LRA=11:TP=-1.5" in commands[0]
    assert "scale=1080:1920:force_original_aspect_ratio=decrease" in commands[0]
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/media/test_finish.py -q`

Expected: collection fails because `ugc_video.render.finish` does not exist.

- [ ] **Step 3: Implement atomic FFmpeg finishing**

`src/ugc_video/render/finish.py`:

```python
import subprocess
from collections.abc import Callable
from pathlib import Path


Runner = Callable[[list[str]], None]


def default_runner(command: list[str]) -> None:
    subprocess.run(command, check=True)


def finish_video(
    animation: Path,
    voice: Path,
    destination: Path,
    runner: Runner = default_runner,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".part.mp4")
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(animation), "-i", str(voice),
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        str(temporary),
    ]
    runner(command)
    temporary.replace(destination)
    return destination
```

- [ ] **Step 4: Create the Remotion package and typed composition**

`remotion/package.json`:

```json
{
  "name": "ugc-video-remotion",
  "private": true,
  "scripts": {"render": "remotion render src/index.ts UgcVertical"},
  "dependencies": {
    "@remotion/cli": "4.0.486",
    "@remotion/media": "4.0.486",
    "remotion": "4.0.486",
    "react": "19.1.0",
    "react-dom": "19.1.0"
  },
  "devDependencies": {"typescript": "5.8.3"}
}
```

`remotion/src/index.ts`:

```typescript
import {registerRoot} from 'remotion';
import {Root} from './Root';

registerRoot(Root);
```

`remotion/src/Root.tsx`:

```tsx
import React from 'react';
import {Composition} from 'remotion';
import {UgcVertical, UgcVerticalProps} from './UgcVertical';

export const Root: React.FC = () => (
  <Composition
    id="UgcVertical"
    component={UgcVertical}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={450}
    defaultProps={{videoSrc: '', headline: '', cta: '', accent: '#ffffff', captions: []} satisfies UgcVerticalProps}
  />
);
```

`remotion/src/UgcVertical.tsx`:

```tsx
import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, interpolate} from 'remotion';

export type UgcVerticalProps = {
  videoSrc: string;
  headline: string;
  cta: string;
  accent: string;
  captions: Array<{text: string; startFrame: number; endFrame: number}>;
};

export const UgcVertical: React.FC<UgcVerticalProps> = ({videoSrc, headline, cta, accent, captions}) => {
  const frame = useCurrentFrame();
  const ctaOpacity = interpolate(frame, [330, 360], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const caption = captions.find((item) => frame >= item.startFrame && frame < item.endFrame);
  return (
    <AbsoluteFill style={{backgroundColor: '#000', fontFamily: 'Arial, sans-serif'}}>
      <OffthreadVideo src={staticFile(videoSrc)} />
      <div style={{position: 'absolute', top: 96, left: 72, right: 72, color: '#fff', fontSize: 64, fontWeight: 800, textShadow: '0 3px 16px #000'}}>
        {headline}
      </div>
      {caption ? (
        <div style={{position: 'absolute', bottom: 360, left: 72, right: 72, color: '#fff', fontSize: 54, lineHeight: 1.12, fontWeight: 800, textAlign: 'center', textShadow: '0 4px 18px #000'}}>
          {caption.text}
        </div>
      ) : null}
      <div style={{position: 'absolute', bottom: 140, left: 96, right: 96, opacity: ctaOpacity, background: accent, color: '#111', borderRadius: 28, padding: 28, textAlign: 'center', fontSize: 48, fontWeight: 800}}>
        {cta}
      </div>
    </AbsoluteFill>
  );
};
```

`remotion/tsconfig.json`:

```json
{"compilerOptions":{"target":"ES2022","module":"ESNext","jsx":"react-jsx","strict":true,"moduleResolution":"Bundler","esModuleInterop":true},"include":["src"]}
```

- [ ] **Step 5: Run GREEN and verify TypeScript**

```bash
uv run pytest tests/media/test_finish.py -q
npm install --prefix remotion
npm --prefix remotion exec tsc -- --noEmit
```

Expected: one Python test passes and TypeScript exits `0`.

- [ ] **Step 6: Commit rendering**

```bash
git add src/ugc_video/render remotion tests/media/test_finish.py
git commit -m "feat: add vertical FFmpeg and Remotion finishing"
```

### Task 9: Pipeline CLI, provider assembly, and offline demo

**Files:**
- Create: `src/ugc_video/pipeline/services.py`
- Create: `src/ugc_video/providers/voice_setup.py`
- Modify: `src/ugc_video/cli.py`
- Create: `tests/pipeline/test_cli.py`
- Create: `tests/fixtures/make_media.sh`

- [ ] **Step 1: Write failing CLI lifecycle tests**

```python
import json
from pathlib import Path

from typer.testing import CliRunner

from ugc_video.cli import app
from ugc_video.domain import ProviderHealth
from ugc_video.providers.voice_setup import choose_voice


def test_new_and_status_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    result = CliRunner().invoke(
        app,
        ["new", "demo-ad", "--product", "Demo", "--cta", "Try it"],
    )
    assert result.exit_code == 0
    project = tmp_path / "home/projects/demo-ad"
    assert json.loads((project / "brief.json").read_text())["product"] == "Demo"
    status = CliRunner().invoke(app, ["status", str(project)])
    assert status.exit_code == 0
    assert "No stages have run" in status.stdout


def test_provider_doctor_is_non_billable_and_actionable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(
        "ugc_video.cli.provider_health",
        lambda secrets, name: ProviderHealth(provider=name, ok=False, detail="key missing"),
    )
    result = CliRunner().invoke(app, ["doctor", "--provider", "fish"])
    assert result.exit_code == 2
    assert "FAIL fish: key missing" in result.stdout


def test_voice_choice_uses_displayed_number_without_exposing_id() -> None:
    output: list[str] = []
    chosen = choose_voice(
        "Fish Audio",
        {"private-id": "Natural Voice"},
        input_fn=lambda prompt: "1",
        output_fn=output.append,
    )
    assert chosen == "private-id"
    assert "Natural Voice" in "\n".join(output)
    assert "private-id" not in "\n".join(output)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/pipeline/test_cli.py -q`

Expected: `new` is not a registered command.

- [ ] **Step 3: Assemble real provider services**

`src/ugc_video/providers/voice_setup.py`:

```python
from collections.abc import Callable

from ugc_video.config import AppConfig
from ugc_video.providers.base import ProviderError, VoiceProvider


def choose_voice(
    label: str,
    voices: dict[str, str],
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> str:
    if not voices:
        return ""
    ordered = list(voices.items())
    output_fn(f"{label} voices:")
    for index, (_, title) in enumerate(ordered, start=1):
        output_fn(f"{index}. {title}")
    for _ in range(3):
        raw = input_fn("Choose a voice number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(ordered):
            return ordered[int(raw) - 1][0]
        output_fn("Enter one of the displayed voice numbers.")
    raise ValueError(f"Too many invalid {label} voice selections")


def configure_voice_ids(
    config: AppConfig,
    fish: VoiceProvider,
    elevenlabs: VoiceProvider,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> AppConfig:
    try:
        fish_voices = fish.list_voices()
    except ProviderError as exc:
        output_fn(f"Fish Audio voice lookup unavailable: {exc}")
        fish_voices = {}
    try:
        elevenlabs_voices = elevenlabs.list_voices()
    except ProviderError as exc:
        output_fn(f"ElevenLabs voice lookup unavailable: {exc}")
        elevenlabs_voices = {}
    fish_id = choose_voice("Fish Audio bookmarked", fish_voices, input_fn, output_fn)
    elevenlabs_id = choose_voice("ElevenLabs", elevenlabs_voices, input_fn, output_fn)
    return config.model_copy(
        update={
            "fish_voice_id": fish_id or config.fish_voice_id,
            "elevenlabs_voice_id": elevenlabs_id or config.elevenlabs_voice_id,
        }
    )
```

`src/ugc_video/pipeline/services.py`:

```python
import math
from pathlib import Path

from ugc_video.audio.fit import fit_audio
from ugc_video.audio.media import normalize_wav
from ugc_video.config import AppConfig
from ugc_video.domain import (
    AnimationRequest,
    FailureKind,
    ProviderHealth,
    VoiceRequest,
    VoiceResult,
)
from ugc_video.pipeline.orchestrator import PipelineServices
from ugc_video.pipeline.project import ProjectPaths
from ugc_video.providers.base import ProviderError, VoiceProvider
from ugc_video.providers.elevenlabs import ElevenLabsProvider
from ugc_video.providers.fish import FishAudioProvider
from ugc_video.providers.grok import GrokApiProvider, GuidedGrokProvider
from ugc_video.providers.retry import RetryPolicy
from ugc_video.providers.voice_router import VoiceRouter
from ugc_video.render.finish import finish_video
from ugc_video.transcription.exact import compare_dialogue
from ugc_video.whisper.backends import load_backends
from ugc_video.whisper.router import transcribe_with_fallback


class MissingVoiceProvider:
    def __init__(self, name: str, secret_name: str) -> None:
        self.name = name
        self.secret_name = secret_name

    def health(self) -> ProviderHealth:
        return ProviderHealth(provider=self.name, ok=False, detail=f"{self.secret_name} is missing")

    def list_voices(self) -> dict[str, str]:
        return {}

    def validate_voice(self, voice_id: str) -> None:
        raise ProviderError(FailureKind.AUTHENTICATION, f"{self.secret_name} is missing")

    def synthesize(self, request: VoiceRequest) -> VoiceResult:
        raise ProviderError(FailureKind.AUTHENTICATION, f"{self.secret_name} is missing")


def build_voice_providers(secrets: dict[str, str]) -> tuple[VoiceProvider, VoiceProvider]:
    fish = (
        FishAudioProvider(secrets["FISH_AUDIO_API_KEY"])
        if secrets.get("FISH_AUDIO_API_KEY")
        else MissingVoiceProvider("fish", "FISH_AUDIO_API_KEY")
    )
    elevenlabs = (
        ElevenLabsProvider(secrets["ELEVENLABS_API_KEY"])
        if secrets.get("ELEVENLABS_API_KEY")
        else MissingVoiceProvider("elevenlabs", "ELEVENLABS_API_KEY")
    )
    return fish, elevenlabs


def provider_health(secrets: dict[str, str], name: str) -> ProviderHealth:
    fish, elevenlabs = build_voice_providers(secrets)
    if name == "fish":
        return fish.health()
    if name == "elevenlabs":
        return elevenlabs.health()
    if name == "grok":
        if secrets.get("XAI_API_KEY"):
            return ProviderHealth(provider="grok", ok=True, detail="xAI API key configured")
        return ProviderHealth(provider="grok", ok=True, detail="guided Grok login checked by doctor --fast")
    raise ValueError("provider must be fish, elevenlabs, or grok")


def build_services(
    config: AppConfig,
    secrets: dict[str, str],
    project: ProjectPaths,
) -> PipelineServices:
    fish, elevenlabs = build_voice_providers(secrets)
    voice_router = VoiceRouter(fish, elevenlabs, RetryPolicy(max_attempts=3))
    guided = GuidedGrokProvider(project.root / "work/grok-handoff.json")
    grok_api = (
        GrokApiProvider(secrets["XAI_API_KEY"])
        if secrets.get("XAI_API_KEY")
        else None
    )

    def animate(script: str, still: Path, output: Path) -> dict[str, object]:
        prompt = (
            "Animate this adult UGC spokesperson with restrained natural head movement, "
            "realistic blinking, and conversational mouth movement. Keep identity, clothing, "
            f"camera, and background stable. She says exactly: {script}"
        )
        request = AnimationRequest(
            image_path=still,
            prompt=prompt,
            destination=output,
            duration_seconds=min(15, max(5, math.ceil(len(script.split()) / 2.4))),
        )
        if config.grok_mode == "guided":
            if output.exists() and output.stat().st_size > 0:
                return {"provider": "grok-guided", "source": "student-import"}
            handoff = guided.prepare(request)
            raise ProviderError(
                FailureKind.CONFIGURATION,
                f"Complete the Grok handoff at {handoff}, save the result to {output}, then resume",
            )
        if grok_api is None:
            raise ProviderError(FailureKind.AUTHENTICATION, "XAI_API_KEY is missing")
        result = grok_api.animate(request)
        return {
            "provider": result.provider,
            "model": result.model,
            "request_id": result.request_id,
            "usage": result.usage,
        }

    def voice(script: str, output: Path) -> dict[str, object]:
        fish_request = VoiceRequest(
            text=script,
            voice_id=config.fish_voice_id,
            model=config.fish_model,
            destination=output,
        )
        elevenlabs_request = VoiceRequest(
            text=script,
            voice_id=config.elevenlabs_voice_id,
            model=config.elevenlabs_model,
            destination=output,
        )
        result = voice_router.synthesize(
            config.voice_provider,
            fish_request,
            elevenlabs_request,
        )
        metadata: dict[str, object] = {
            "provider": result.provider,
            "model": result.model,
            "voice_id": result.voice_id,
        }
        if result.provider == "elevenlabs":
            metadata["license_warning"] = (
                "Verify the ElevenLabs plan before publishing; Free output is non-commercial with attribution"
            )
        return metadata

    def verify(media: Path, expected: str) -> dict[str, object]:
        wav = project.root / "work" / f"{media.stem}-verify.wav"
        normalize_wav(media, wav)
        routed = transcribe_with_fallback(
            load_backends(),
            wav,
            config.whisper_language,
            expected_text=expected,
        )
        comparison = compare_dialogue(expected, routed.transcript.text)
        if not comparison.ok:
            raise ProviderError(
                FailureKind.QA_REJECTION,
                f"dialogue mismatch; missing={comparison.missing}, unexpected={comparison.unexpected}",
            )
        return {"backend": routed.backend, "text": routed.transcript.text}

    def finish(animation: Path, raw_voice: Path, destination: Path) -> dict[str, object]:
        normalized = project.root / "work/voice-normalized.wav"
        normalize_wav(raw_voice, normalized)
        decision = fit_audio(normalized, animation, project.fitted_voice)
        if decision.action == "regenerate-animation":
            raise ProviderError(
                FailureKind.QA_REJECTION,
                f"voice timing factor {decision.factor:.3f} would sound unnatural; regenerate animation",
            )
        finish_video(animation, project.fitted_voice, destination)
        return {"renderer": "ffmpeg", "time_factor": decision.factor}

    return PipelineServices(animate=animate, voice=voice, verify=verify, finish=finish)
```

- [ ] **Step 4: Add lifecycle commands**

Append these command signatures to `src/ugc_video/cli.py` and delegate behavior to `create_project`, `project_paths`, `RunStore`, `build_services`, and `run_pipeline`:

```python
@app.command("new")
def new_project(
    name: str,
    product: str = typer.Option("", "--product", prompt=True),
    cta: str = typer.Option("", "--cta", prompt=True),
) -> None:
    paths = AppPaths.from_environment(os.environ)
    project = create_project(paths.projects / name, {"product": product, "cta": cta})
    typer.echo(f"Project created: {project.root}")


@app.command()
def status(project: Path) -> None:
    manifest = RunStore(project / "run.json").load()
    if not manifest.stages:
        typer.echo("No stages have run")
        return
    for name, record in manifest.stages.items():
        typer.echo(f"{record.status.value.upper()} {name}: {record.detail}")


@app.command()
def run(project: Path) -> None:
    paths = AppPaths.from_environment(os.environ)
    config = load_config(paths.config)
    secrets = read_secrets(paths.secrets)
    project_config = project_paths(project)
    output = run_pipeline(project_config, build_services(config, secrets, project_config))
    typer.echo(f"Final video: {output}")


@app.command()
def resume(project: Path) -> None:
    run(project)
```

Extend the existing `doctor` signature with:

```python
provider: str = typer.Option("", "--provider"),
```

Insert this branch before `run_doctor`:

```python
if provider:
    paths = AppPaths.from_environment(os.environ)
    health = provider_health(read_secrets(paths.secrets), provider)
    typer.echo(f"{'PASS' if health.ok else 'FAIL'} {health.provider}: {health.detail}")
    if not health.ok:
        raise typer.Exit(2)
    return
```

This health path does not perform billable synthesis.

At the end of the existing `setup` command, reload the saved secrets, build both voice providers, display Fish bookmarks and ElevenLabs voices, then persist the choices:

```python
saved_secrets = read_secrets(paths.secrets)
fish, elevenlabs = build_voice_providers(saved_secrets)
configured = configure_voice_ids(load_config(paths.config), fish, elevenlabs)
save_config(paths.config, configured)
```

Add imports for `Path`, `RunStore`, `project_paths`, `create_project`, `build_services`, `build_voice_providers`, `provider_health`, `configure_voice_ids`, `run_pipeline`, and `read_secrets`.

- [ ] **Step 5: Add deterministic fixture media generation**

`tests/fixtures/make_media.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail
OUT="${1:?output directory required}"
mkdir -p "$OUT"
ffmpeg -y -loglevel error -f lavfi -i color=c=0x334455:s=1080x1920:d=2:r=30 \
  -f lavfi -i sine=frequency=440:duration=2 -shortest -c:v libx264 -pix_fmt yuv420p \
  -c:a aac "$OUT/animation.mp4"
ffmpeg -y -loglevel error -f lavfi -i sine=frequency=220:duration=2 \
  -ac 1 -ar 44100 "$OUT/voice.wav"
```

- [ ] **Step 6: Run the complete pipeline test suite**

```bash
chmod +x tests/fixtures/make_media.sh
uv run pytest tests/providers tests/media tests/pipeline -q
uv run ruff check src tests/providers tests/media tests/pipeline
uv run mypy src
```

Expected: every command exits `0`.

- [ ] **Step 7: Commit pipeline completion**

```bash
git add src/ugc_video/pipeline src/ugc_video/cli.py tests/pipeline tests/fixtures
git commit -m "feat: expose resumable UGC pipeline commands"
```

- [ ] **Step 8: Record the integration checkpoint**

Run:

```bash
git status --short
git log --oneline --max-count=9
```

Expected: empty status and nine coherent task commits for the pipeline plan.
