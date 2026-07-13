# Foundation and Platform Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $subagent-driven-development (recommended) or $executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a locally installable `ugc-video` package with secure configuration, actionable diagnostics, three isolated Whisper backends, and idempotent Apple Silicon and Windows 11/WSL2 bootstraps.

**Architecture:** A Python 3.11 control plane owns paths, configuration, diagnostics, model manifests, health state, and fallback routing. Platform scripts install only external prerequisites and then delegate to the same Python commands. Whisper engines run in isolated subprocesses so one corrupt native runtime cannot disable the others.

**Tech Stack:** Python 3.11, `uv`, Typer, Rich, Pydantic, platformdirs, python-dotenv, pytest, FFmpeg/FFprobe, Rubber Band, whisper.cpp, Faster-Whisper, MLX Whisper, OpenAI Whisper, Bash, PowerShell, WSL2.

---

## File map

- `.gitignore` — secrets, environments, models, caches, and generated projects.
- `.env.example` — secret names with empty values.
- `LICENSE` — MIT license for repository-authored code.
- `pyproject.toml` / `uv.lock` — package and locked environment.
- `src/ugc_video/paths.py` — user-scoped XDG paths.
- `src/ugc_video/config.py` — validated non-secret TOML configuration.
- `src/ugc_video/secrets.py` — hidden secret collection and mode-`600` storage.
- `src/ugc_video/redaction.py` — deterministic token redaction.
- `src/ugc_video/capabilities.py` — platform and executable discovery.
- `src/ugc_video/doctor.py` — diagnostic aggregation and exit status.
- `src/ugc_video/cli.py` — setup, doctor, version, and Whisper commands.
- `src/ugc_video/whisper/` — manifests, backends, health, installer, and router.
- Platform launchers and scripts — macOS, Windows, WSL Ubuntu, models, uninstall.
- `tests/foundation/`, `tests/whisper/`, `tests/platform/` — deterministic tests.

### Task 1: Package skeleton and public command

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `LICENSE`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `src/ugc_video/__init__.py`
- Create: `src/ugc_video/cli.py`
- Create: `tests/foundation/test_package.py`

- [ ] **Step 1: Write the failing package test**

```python
from typer.testing import CliRunner

import ugc_video
from ugc_video.cli import app


def test_package_and_cli_are_importable() -> None:
    assert ugc_video.__version__ == "0.1.0"
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ugc-video 0.1.0"
```

- [ ] **Step 2: Run the test to verify RED**

Run: `python3 -m pytest tests/foundation/test_package.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'ugc_video'`.

- [ ] **Step 3: Create the package metadata and minimal CLI**

`.gitignore`:

```gitignore
.env
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
__pycache__/
*.py[cod]
*.egg-info/
.coverage
htmlcov/
.ugc-video/
output/
projects/
models/
*.mp3
*.wav
*.opus
*.mp4
*.mov
auth.json
secrets.env
```

`.env.example`:

```dotenv
FISH_AUDIO_API_KEY=
ELEVENLABS_API_KEY=
XAI_API_KEY=
```

`README.md`:

```markdown
# UGC Video Student Kit

This repository contains the approved design and implementation plans for a supported Apple Silicon and Windows 11/WSL2 student video workflow. The complete student setup guide is delivered by the release plan before publication.
```

`pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[project]
name = "ugc-video-student-kit"
version = "0.1.0"
description = "Reproducible UGC video workflow for supported student machines"
readme = "README.md"
requires-python = ">=3.11,<3.13"
license = {text = "MIT"}
dependencies = [
  "httpx>=0.28,<1",
  "platformdirs>=4.3,<5",
  "pydantic>=2.11,<3",
  "python-dotenv>=1.1,<2",
  "rich>=14,<15",
  "tomli-w>=1.2,<2",
  "typer>=0.16,<1",
]

[project.optional-dependencies]
dev = [
  "mypy>=1.16,<2",
  "pytest>=8.4,<9",
  "pytest-cov>=6.2,<7",
  "ruff>=0.12,<1",
]
mac-whisper = [
  "faster-whisper>=1.2,<2",
  "huggingface-hub>=0.33,<1",
  "mlx-whisper>=0.4,<1",
  "numpy>=1.26,<3",
  "scipy>=1.13,<2",
]
wsl-whisper = [
  "faster-whisper>=1.2,<2",
  "huggingface-hub>=0.33,<1",
  "numpy>=1.26,<3",
  "openai-whisper>=20250625",
  "scipy>=1.13,<2",
]

[project.scripts]
ugc-video = "ugc_video.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/ugc_video"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.mypy]
python_version = "3.11"
strict = true
packages = ["ugc_video"]
```

- [ ] **Step 4: Create the initial package and CLI**

`src/ugc_video/__init__.py`:

```python
__version__ = "0.1.0"
```

`src/ugc_video/cli.py`:

```python
import typer

from ugc_video import __version__


app = typer.Typer(help="Student-safe UGC video production")


@app.command()
def version() -> None:
    """Print the installed student-kit version."""
    typer.echo(f"ugc-video {__version__}")


if __name__ == "__main__":
    app()
```

- [ ] **Step 6: Add the MIT license**

Create `LICENSE` with:

```text
MIT License

Copyright (c) 2026 kofiowusuai-lab

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Run: `python3 -c 'from pathlib import Path; assert "MIT License" in Path("LICENSE").read_text()'`

Expected: exit `0`.

- [ ] **Step 7: Resolve dependencies and run GREEN**

Run:

```bash
uv lock
uv sync --extra dev
uv run pytest tests/foundation/test_package.py -q
```

Expected: one test passes and `uv.lock` is created.

- [ ] **Step 8: Commit the baseline**

```bash
git add .gitignore .env.example LICENSE README.md pyproject.toml uv.lock src tests/foundation
git commit -m "build: initialize student kit package"
```

### Task 2: Portable paths, configuration, secrets, and redaction

**Files:**
- Create: `src/ugc_video/paths.py`
- Create: `src/ugc_video/config.py`
- Create: `src/ugc_video/secrets.py`
- Create: `src/ugc_video/redaction.py`
- Create: `tests/foundation/test_config_security.py`

- [ ] **Step 1: Write failing configuration and secret tests**

```python
import os
from pathlib import Path

from ugc_video.config import AppConfig, load_config, save_config
from ugc_video.paths import AppPaths
from ugc_video.redaction import redact
from ugc_video.secrets import read_secrets, write_secret


def test_paths_follow_explicit_home(tmp_path: Path) -> None:
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path)})
    assert paths.root == tmp_path
    assert paths.secrets == tmp_path / "secrets.env"
    assert paths.models == tmp_path / "models"


def test_config_round_trip_and_provider_validation(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    config = AppConfig(voice_provider="elevenlabs", fish_voice_id="fish-a")
    save_config(path, config)
    assert load_config(path) == config


def test_secret_file_is_private_and_value_is_redacted(tmp_path: Path) -> None:
    path = tmp_path / "secrets.env"
    write_secret(path, "FISH_AUDIO_API_KEY", "fish-secret-123")
    assert read_secrets(path)["FISH_AUDIO_API_KEY"] == "fish-secret-123"
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600
    assert redact("Bearer fish-secret-123", ["fish-secret-123"]) == "Bearer [REDACTED]"
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/foundation/test_config_security.py -q`

Expected: collection fails because `ugc_video.config` does not exist.

- [ ] **Step 3: Implement portable paths**

`src/ugc_video/paths.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from platformdirs import user_cache_path, user_config_path, user_data_path, user_state_path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    config: Path
    secrets: Path
    models: Path
    state: Path
    cache: Path
    projects: Path

    @classmethod
    def from_environment(cls, env: Mapping[str, str]) -> "AppPaths":
        override = env.get("UGC_VIDEO_HOME")
        if override:
            root = Path(override).expanduser().resolve()
            return cls(
                root=root,
                config=root / "config.toml",
                secrets=root / "secrets.env",
                models=root / "models",
                state=root / "state",
                cache=root / "cache",
                projects=root / "projects",
            )
        config_root = user_config_path("ugc-video", appauthor=False)
        data_root = user_data_path("ugc-video", appauthor=False)
        return cls(
            root=data_root,
            config=config_root / "config.toml",
            secrets=config_root / "secrets.env",
            models=data_root / "models",
            state=user_state_path("ugc-video", appauthor=False),
            cache=user_cache_path("ugc-video", appauthor=False),
            projects=data_root / "projects",
        )
```

- [ ] **Step 4: Implement validated TOML configuration**

`src/ugc_video/config.py`:

```python
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
```

- [ ] **Step 5: Implement local secrets and redaction**

`src/ugc_video/secrets.py`:

```python
import os
from pathlib import Path


ALLOWED_SECRET_NAMES = {
    "FISH_AUDIO_API_KEY",
    "ELEVENLABS_API_KEY",
    "XAI_API_KEY",
}


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
        "".join(f"{key}={values[key]}\n" for key in sorted(values)),
        encoding="utf-8",
    )
    if os.name != "nt":
        temporary.chmod(0o600)
    temporary.replace(path)
```

`src/ugc_video/redaction.py`:

```python
import re
from collections.abc import Iterable


_PATTERNS = (
    re.compile(r"(?i)(authorization:\s*bearer\s+)\S+"),
    re.compile(r"(?i)(xi-api-key[:=]\s*)\S+"),
    re.compile(r"(?i)((?:FISH_AUDIO|ELEVENLABS|XAI)_API_KEY=)\S+"),
)


def redact(message: str, secrets: Iterable[str] = ()) -> str:
    safe = str(message)
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, "[REDACTED]")
    for pattern in _PATTERNS:
        safe = pattern.sub(r"\1[REDACTED]", safe)
    return safe
```

- [ ] **Step 6: Run GREEN and commit**

```bash
uv run pytest tests/foundation/test_config_security.py -q
git add src/ugc_video/paths.py src/ugc_video/config.py src/ugc_video/secrets.py src/ugc_video/redaction.py tests/foundation/test_config_security.py
git commit -m "feat: add secure portable configuration"
```

Expected: three tests pass before the commit.

### Task 3: Capability discovery, setup command, and fast doctor

**Files:**
- Create: `src/ugc_video/capabilities.py`
- Create: `src/ugc_video/doctor.py`
- Modify: `src/ugc_video/cli.py`
- Create: `tests/foundation/test_doctor.py`

- [ ] **Step 1: Write failing diagnostic tests**

```python
import json
from pathlib import Path

from typer.testing import CliRunner

from ugc_video.capabilities import Capability, inspect_commands
from ugc_video.cli import app
from ugc_video.doctor import DoctorReport


def test_command_inspection_reports_missing_without_raising() -> None:
    results = inspect_commands(
        ["ffmpeg", "codex"],
        which=lambda name: "/bin/ffmpeg" if name == "ffmpeg" else None,
    )
    assert results == [
        Capability("ffmpeg", True, "/bin/ffmpeg", ""),
        Capability("codex", False, "", "not found on PATH"),
    ]


def test_doctor_json_uses_nonzero_exit_for_required_failure(monkeypatch, tmp_path: Path) -> None:
    report = DoctorReport(
        ok=False,
        checks=[Capability("ffmpeg", False, "", "not found on PATH")],
    )
    monkeypatch.setattr("ugc_video.cli.run_doctor", lambda full=False: report)
    result = CliRunner().invoke(app, ["doctor", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["checks"][0]["name"] == "ffmpeg"
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/foundation/test_doctor.py -q`

Expected: collection fails because `ugc_video.capabilities` does not exist.

- [ ] **Step 3: Implement capability records and platform validation**

`src/ugc_video/capabilities.py`:

```python
import platform
import shutil
from dataclasses import asdict, dataclass
from typing import Callable


@dataclass(frozen=True)
class Capability:
    name: str
    ok: bool
    value: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def inspect_commands(
    names: list[str], which: Callable[[str], str | None] = shutil.which
) -> list[Capability]:
    checks: list[Capability] = []
    for name in names:
        path = which(name)
        checks.append(
            Capability(name, path is not None, path or "", "" if path else "not found on PATH")
        )
    return checks


def inspect_platform() -> Capability:
    system = platform.system()
    machine = platform.machine().lower()
    release = platform.release()
    if system == "Darwin" and machine == "arm64":
        return Capability("platform", True, f"macOS {release} arm64", "")
    if system == "Linux" and "microsoft" in release.lower():
        return Capability("platform", True, f"WSL2 {release}", "")
    return Capability(
        "platform",
        False,
        f"{system} {release} {machine}",
        "supported targets are Apple Silicon macOS and Windows 11 through WSL2",
    )
```

- [ ] **Step 4: Implement doctor aggregation**

`src/ugc_video/doctor.py`:

```python
from dataclasses import asdict, dataclass

from ugc_video.capabilities import Capability, inspect_commands, inspect_platform


REQUIRED_COMMANDS = ["ffmpeg", "ffprobe", "rubberband", "node", "npm", "codex", "grok"]


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    checks: list[Capability]

    def to_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "checks": [asdict(item) for item in self.checks]}


def run_doctor(full: bool = False) -> DoctorReport:
    checks = [inspect_platform(), *inspect_commands(REQUIRED_COMMANDS)]
    if full:
        from ugc_video.whisper.health import inspect_whisper

        checks.extend(inspect_whisper(deep=True))
    return DoctorReport(ok=all(item.ok for item in checks), checks=checks)
```

- [ ] **Step 5: Extend the CLI with setup and doctor commands**

Replace `src/ugc_video/cli.py` with:

```python
import json
import os
from getpass import getpass

import typer

from ugc_video import __version__
from ugc_video.config import load_config, save_config
from ugc_video.doctor import run_doctor
from ugc_video.paths import AppPaths
from ugc_video.secrets import write_secret


app = typer.Typer(help="Student-safe UGC video production")
whisper_app = typer.Typer(help="Install and verify local Whisper fallbacks")
app.add_typer(whisper_app, name="whisper")


@app.command()
def version() -> None:
    typer.echo(f"ugc-video {__version__}")


@app.command()
def setup() -> None:
    paths = AppPaths.from_environment(os.environ)
    save_config(paths.config, load_config(paths.config))
    for name in ("FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY", "XAI_API_KEY"):
        value = getpass(f"{name} (leave blank to skip): ").strip()
        if value:
            write_secret(paths.secrets, name, value)
    typer.echo(f"Configuration saved under {paths.root}")


@app.command()
def doctor(
    fast: bool = typer.Option(False, "--fast"),
    full: bool = typer.Option(False, "--full"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    if fast and full:
        raise typer.BadParameter("choose either --fast or --full")
    report = run_doctor(full=full)
    if json_output:
        typer.echo(json.dumps(report.to_dict(), indent=2))
    else:
        for check in report.checks:
            mark = "PASS" if check.ok else "FAIL"
            typer.echo(f"{mark} {check.name}: {check.value or check.detail}")
    if not report.ok:
        raise typer.Exit(2)


if __name__ == "__main__":
    app()
```

- [ ] **Step 6: Run GREEN and commit**

```bash
uv run pytest tests/foundation/test_doctor.py -q
git add src/ugc_video/capabilities.py src/ugc_video/doctor.py src/ugc_video/cli.py tests/foundation/test_doctor.py
git commit -m "feat: add capability doctor and secure setup"
```

Expected: two tests pass before the commit.

### Task 4: Whisper inventory and ordered fallback router

**Files:**
- Create: `src/ugc_video/whisper/__init__.py`
- Create: `src/ugc_video/whisper/types.py`
- Create: `src/ugc_video/whisper/manifest.py`
- Create: `src/ugc_video/whisper/router.py`
- Create: `tests/whisper/test_manifest_router.py`

- [ ] **Step 1: Write failing manifest and router tests**

```python
from pathlib import Path

import pytest

from ugc_video.whisper.manifest import build_inventory, verify_inventory
from ugc_video.whisper.router import AllBackendsFailed, transcribe_with_fallback
from ugc_video.whisper.types import Transcript


class FakeBackend:
    def __init__(self, name: str, transcript: str = "", error: str = "") -> None:
        self.name = name
        self.transcript = transcript
        self.error = error

    def transcribe(self, media: Path, language: str) -> Transcript:
        if self.error:
            raise RuntimeError(self.error)
        return Transcript(text=self.transcript, words=[])


def test_inventory_detects_changed_model(tmp_path: Path) -> None:
    model = tmp_path / "model.bin"
    model.write_bytes(b"healthy")
    inventory = build_inventory(tmp_path)
    model.write_bytes(b"broken")
    assert verify_inventory(tmp_path, inventory, deep=False).ok is False


def test_router_rejects_mismatch_and_uses_next_backend(tmp_path: Path) -> None:
    result = transcribe_with_fallback(
        [FakeBackend("first", "wrong"), FakeBackend("second", "exact line")],
        tmp_path / "fixture.wav",
        "en",
        expected_text="Exact line.",
    )
    assert result.backend == "second"
    assert result.attempts[0].status == "rejected"


def test_router_reports_every_failure(tmp_path: Path) -> None:
    with pytest.raises(AllBackendsFailed, match="first.*corrupt.*second.*timeout"):
        transcribe_with_fallback(
            [FakeBackend("first", error="corrupt"), FakeBackend("second", error="timeout")],
            tmp_path / "fixture.wav",
            "en",
        )
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/whisper/test_manifest_router.py -q`

Expected: collection fails because `ugc_video.whisper.manifest` does not exist.

- [ ] **Step 3: Implement Whisper types**

`src/ugc_video/whisper/types.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Transcript:
    text: str
    words: list[Word]


@dataclass(frozen=True)
class Attempt:
    backend: str
    status: str
    elapsed_seconds: float
    detail: str = ""


@dataclass(frozen=True)
class RoutedTranscript:
    backend: str
    transcript: Transcript
    attempts: list[Attempt] = field(default_factory=list)


class WhisperBackend(Protocol):
    name: str

    def transcribe(self, media: Path, language: str) -> Transcript:
        raise NotImplementedError
```

- [ ] **Step 4: Implement atomic model inventory**

`src/ugc_video/whisper/manifest.py`:

```python
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IntegrityResult:
    ok: bool
    errors: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": str(path.relative_to(root)),
            "size": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def verify_inventory(
    root: Path, inventory: list[dict[str, object]], deep: bool
) -> IntegrityResult:
    errors: list[str] = []
    for item in inventory:
        path = root / str(item["path"])
        if not path.is_file():
            errors.append(f"missing: {item['path']}")
            continue
        stat = path.stat()
        if stat.st_size != int(item["size"]):
            errors.append(f"size changed: {item['path']}")
            continue
        if deep and sha256_file(path) != str(item["sha256"]):
            errors.append(f"checksum changed: {item['path']}")
    return IntegrityResult(ok=not errors, errors=errors)
```

- [ ] **Step 5: Implement exact-text fallback routing**

`src/ugc_video/whisper/router.py`:

```python
import re
import time
from pathlib import Path

from ugc_video.whisper.types import Attempt, RoutedTranscript, WhisperBackend


def normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


class AllBackendsFailed(RuntimeError):
    def __init__(self, attempts: list[Attempt]) -> None:
        self.attempts = attempts
        detail = "; ".join(f"{item.backend}: {item.detail}" for item in attempts)
        super().__init__(f"All Whisper backends failed: {detail}")


def transcribe_with_fallback(
    backends: list[WhisperBackend],
    media: Path,
    language: str,
    expected_text: str = "",
) -> RoutedTranscript:
    expected = normalize_text(expected_text) if expected_text else ""
    attempts: list[Attempt] = []
    for backend in backends:
        started = time.monotonic()
        try:
            transcript = backend.transcribe(media, language)
            normalized = normalize_text(transcript.text)
            elapsed = time.monotonic() - started
            if not normalized:
                attempts.append(Attempt(backend.name, "rejected", elapsed, "empty transcript"))
                continue
            if expected and normalized != expected:
                attempts.append(Attempt(backend.name, "rejected", elapsed, "expected text mismatch"))
                continue
            attempts.append(Attempt(backend.name, "succeeded", elapsed))
            return RoutedTranscript(backend.name, transcript, attempts)
        except Exception as exc:
            attempts.append(
                Attempt(backend.name, "failed", time.monotonic() - started, str(exc))
            )
    raise AllBackendsFailed(attempts)
```

- [ ] **Step 6: Run GREEN and commit**

```bash
uv run pytest tests/whisper/test_manifest_router.py -q
git add src/ugc_video/whisper tests/whisper/test_manifest_router.py
git commit -m "feat: add Whisper integrity and fallback routing"
```

Expected: three tests pass before the commit.

### Task 5: Isolated Whisper backends, model installation, and health

**Files:**
- Create: `config/models.json`
- Create: `src/ugc_video/whisper/backends.py`
- Create: `src/ugc_video/whisper/worker_faster.py`
- Create: `src/ugc_video/whisper/worker_mlx.py`
- Create: `src/ugc_video/whisper/worker_openai.py`
- Create: `src/ugc_video/whisper/install.py`
- Create: `src/ugc_video/whisper/health.py`
- Modify: `src/ugc_video/cli.py`
- Create: `tests/whisper/test_install_health.py`

- [ ] **Step 1: Write failing backend and health tests**

```python
import json
from pathlib import Path

import pytest

from ugc_video.paths import AppPaths
from ugc_video.whisper.backends import JsonSubprocessBackend
from ugc_video.whisper.health import inspect_whisper
from ugc_video.whisper.install import repair_model
from ugc_video.whisper.types import Transcript


def test_subprocess_backend_normalizes_json(tmp_path: Path) -> None:
    payload = {"text": "health check", "words": [{"text": "health", "start": 0, "end": 0.4}]}

    def runner(command: list[str], timeout: int) -> str:
        assert str(tmp_path / "fixture.wav") in command
        assert timeout == 180
        return json.dumps(payload)

    backend = JsonSubprocessBackend("faster-small-en", ["python", "worker.py"], 180, runner)
    result = backend.transcribe(tmp_path / "fixture.wav", "en")
    assert result == Transcript(text="health check", words=result.words)
    assert result.words[0].text == "health"


def test_deep_health_reports_three_backends(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path))
    monkeypatch.setattr("ugc_video.whisper.health.load_backends", lambda: [])
    checks = inspect_whisper(deep=True)
    assert checks[0].name == "whisper-model-manifest"
    assert checks[0].ok is False


def test_repair_rejects_unknown_backend_before_download(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "models.json"
    source.write_text('{"test-platform":[{"name":"known"}]}', encoding="utf-8")
    monkeypatch.setattr("ugc_video.whisper.install.platform_key", lambda: "test-platform")
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path / "home")})
    with pytest.raises(ValueError, match="Unknown Whisper backend unknown"):
        repair_model(paths, source, "unknown")
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/whisper/test_install_health.py -q`

Expected: collection fails because `ugc_video.whisper.backends` does not exist.

- [ ] **Step 3: Define platform model sources**

`config/models.json`:

```json
{
  "darwin-arm64": [
    {"name": "whispercpp-small-en", "kind": "whispercpp", "source": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"},
    {"name": "faster-small-en", "kind": "huggingface", "source": "Systran/faster-whisper-small.en"},
    {"name": "mlx-small", "kind": "huggingface", "source": "mlx-community/whisper-small-mlx"}
  ],
  "linux-wsl2": [
    {"name": "whispercpp-small-en", "kind": "whispercpp", "source": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"},
    {"name": "faster-small-en", "kind": "huggingface", "source": "Systran/faster-whisper-small.en"},
    {"name": "openai-small", "kind": "openai-whisper", "source": "small"}
  ]
}
```

- [ ] **Step 4: Implement the isolated JSON subprocess adapter**

`src/ugc_video/whisper/backends.py`:

```python
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from ugc_video.paths import AppPaths
from ugc_video.whisper.types import Transcript, Word


Runner = Callable[[list[str], int], str]


def default_runner(command: list[str], timeout: int) -> str:
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return result.stdout


class JsonSubprocessBackend:
    def __init__(self, name: str, prefix: list[str], timeout: int, runner: Runner = default_runner) -> None:
        self.name = name
        self.prefix = prefix
        self.timeout = timeout
        self.runner = runner

    def transcribe(self, media: Path, language: str) -> Transcript:
        payload = json.loads(self.runner([*self.prefix, str(media), language], self.timeout))
        words = [
            Word(str(item["text"]), float(item["start"]), float(item["end"]))
            for item in payload.get("words", [])
        ]
        return Transcript(text=str(payload.get("text", "")).strip(), words=words)


class WhisperCppBackend:
    name = "whispercpp-small-en"

    def __init__(self, model: Path, executable: str = "whisper-cli") -> None:
        self.model = model
        self.executable = executable

    def transcribe(self, media: Path, language: str) -> Transcript:
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "result"
            subprocess.run(
                [
                    self.executable,
                    "-m", str(self.model),
                    "-f", str(media),
                    "-l", language,
                    "-oj",
                    "-of", str(prefix),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=180,
            )
            payload = json.loads(prefix.with_suffix(".json").read_text(encoding="utf-8"))
        segments = payload.get("transcription", [])
        words = [
            Word(
                str(item.get("text", "")).strip(),
                float(item.get("offsets", {}).get("from", 0)) / 1000,
                float(item.get("offsets", {}).get("to", 0)) / 1000,
            )
            for item in segments
            if str(item.get("text", "")).strip()
        ]
        return Transcript(
            text=" ".join(item.text for item in words),
            words=words,
        )


def load_backends(paths: AppPaths | None = None) -> list[JsonSubprocessBackend | WhisperCppBackend]:
    paths = paths or AppPaths.from_environment(os.environ)
    cpp = WhisperCppBackend(paths.models / "whispercpp-small-en/ggml-small.en.bin")
    faster = JsonSubprocessBackend(
        "faster-small-en",
        [sys.executable, "-m", "ugc_video.whisper.worker_faster", str(paths.models / "faster-small-en")],
        240,
    )
    if platform.system() == "Darwin":
        third = JsonSubprocessBackend(
            "mlx-small",
            [sys.executable, "-m", "ugc_video.whisper.worker_mlx", str(paths.models / "mlx-small")],
            180,
        )
    else:
        third = JsonSubprocessBackend(
            "openai-small",
            [sys.executable, "-m", "ugc_video.whisper.worker_openai", str(paths.models / "openai-small")],
            300,
        )
    return [cpp, faster, third]
```

- [ ] **Step 5: Implement model installation with recorded revisions and checksums**

Create `src/ugc_video/whisper/install.py`:

```python
import importlib
import json
import platform
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from ugc_video.paths import AppPaths
from ugc_video.whisper.manifest import build_inventory


def platform_key() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    release = platform.release().lower()
    if system == "Darwin" and machine == "arm64":
        return "darwin-arm64"
    if system == "Linux" and "microsoft" in release:
        return "linux-wsl2"
    raise RuntimeError("Whisper installation supports Apple Silicon and WSL2 only")


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def install_models(
    paths: AppPaths,
    source_manifest: Path,
    force_names: set[str] | None = None,
) -> Path:
    definitions = json.loads(source_manifest.read_text(encoding="utf-8"))[platform_key()]
    installed: list[dict[str, object]] = []
    force_names = force_names or set()
    quarantines: dict[Path, Path] = {}
    try:
        for definition in definitions:
            destination = paths.models / definition["name"]
            if definition["name"] in force_names and destination.exists():
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                quarantine = destination.with_name(f"{destination.name}.corrupt-{stamp}")
                destination.replace(quarantine)
                quarantines[destination] = quarantine
            destination.mkdir(parents=True, exist_ok=True)
            if definition["kind"] == "whispercpp":
                target = destination / "ggml-small.en.bin"
                if not target.exists():
                    temporary = target.with_suffix(".part")
                    urllib.request.urlretrieve(definition["source"], temporary)
                    temporary.replace(target)
                revision = "downloaded-file-sha256"
            elif definition["kind"] == "huggingface":
                revision = HfApi().model_info(definition["source"]).sha
                snapshot_download(
                    repo_id=definition["source"],
                    local_dir=destination,
                    revision=revision,
                )
            else:
                whisper = importlib.import_module("whisper")
                whisper.load_model(definition["source"], download_root=str(destination))
                revision = str(getattr(whisper, "__version__", "package-version-unavailable"))
            installed.append(
                {
                    **definition,
                    "revision": revision,
                    "inventory": build_inventory(destination),
                }
            )
    except Exception:
        for destination, quarantine in quarantines.items():
            shutil.rmtree(destination, ignore_errors=True)
            quarantine.replace(destination)
        raise
    for quarantine in quarantines.values():
        shutil.rmtree(quarantine, ignore_errors=True)
    create_health_fixture(paths)
    manifest = paths.models / "manifest.json"
    atomic_json(manifest, {"platform": platform_key(), "models": installed})
    return manifest


def repair_model(paths: AppPaths, source_manifest: Path, name: str) -> Path:
    definitions = json.loads(source_manifest.read_text(encoding="utf-8"))[platform_key()]
    valid = {str(item["name"]) for item in definitions}
    if name not in valid:
        raise ValueError(f"Unknown Whisper backend {name}; choose one of {sorted(valid)}")
    return install_models(paths, source_manifest, force_names={name})


def create_health_fixture(paths: AppPaths) -> Path:
    fixture_root = paths.root / "fixtures"
    fixture_root.mkdir(parents=True, exist_ok=True)
    destination = fixture_root / "whisper-health.wav"
    if destination.exists():
        return destination
    if platform.system() == "Darwin":
        aiff = fixture_root / "whisper-health.aiff"
        subprocess.run(["say", "-o", str(aiff), "Whisper health check."], check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), "-ar", "16000", "-ac", "1", str(destination)],
            check=True,
        )
        aiff.unlink(missing_ok=True)
    else:
        subprocess.run(
            ["espeak-ng", "-w", str(destination), "Whisper health check."],
            check=True,
        )
    return destination
```

- [ ] **Step 6: Implement health and platform backend loading**

`src/ugc_video/whisper/worker_faster.py`:

```python
import json
import sys

from faster_whisper import WhisperModel


def main() -> None:
    model_path, media, language = sys.argv[1:4]
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(media, language=language, word_timestamps=True)
    words = []
    text = []
    for segment in segments:
        text.append(segment.text.strip())
        for word in segment.words or []:
            words.append({"text": word.word.strip(), "start": word.start, "end": word.end})
    print(json.dumps({"text": " ".join(text), "words": words}))


if __name__ == "__main__":
    main()
```

`src/ugc_video/whisper/worker_mlx.py`:

```python
import json
import sys

import mlx_whisper


def main() -> None:
    model_path, media, language = sys.argv[1:4]
    result = mlx_whisper.transcribe(
        media,
        path_or_hf_repo=model_path,
        language=language,
        word_timestamps=True,
    )
    words = [word for segment in result.get("segments", []) for word in segment.get("words", [])]
    print(json.dumps({"text": result.get("text", ""), "words": words}))


if __name__ == "__main__":
    main()
```

`src/ugc_video/whisper/worker_openai.py`:

```python
import json
import sys

import whisper


def main() -> None:
    model_root, media, language = sys.argv[1:4]
    model = whisper.load_model("small", download_root=model_root)
    result = model.transcribe(media, language=language, word_timestamps=True)
    words = [word for segment in result.get("segments", []) for word in segment.get("words", [])]
    print(json.dumps({"text": result.get("text", ""), "words": words}))


if __name__ == "__main__":
    main()
```

`src/ugc_video/whisper/health.py`:

```python
import json
import os

from ugc_video.capabilities import Capability
from ugc_video.paths import AppPaths
from ugc_video.whisper.backends import load_backends
from ugc_video.whisper.manifest import verify_inventory
from ugc_video.whisper.router import normalize_text


FIXTURE_TEXT = "Whisper health check."


def inspect_whisper(deep: bool = False) -> list[Capability]:
    paths = AppPaths.from_environment(os.environ)
    manifest_path = paths.models / "manifest.json"
    if not manifest_path.exists():
        return [Capability("whisper-model-manifest", False, "", "run ugc-video whisper install")]
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [Capability("whisper-model-manifest", False, "", f"invalid manifest: {exc}")]

    checks = [Capability("whisper-model-manifest", True, str(manifest_path), "")]
    by_name = {item["name"]: item for item in payload.get("models", [])}
    for name, item in by_name.items():
        integrity = verify_inventory(paths.models / name, item.get("inventory", []), deep=deep)
        checks.append(
            Capability(name, integrity.ok, str(paths.models / name), "; ".join(integrity.errors))
        )
    if not deep:
        return checks

    fixture = paths.root / "fixtures/whisper-health.wav"
    for backend in load_backends(paths):
        try:
            transcript = backend.transcribe(fixture, "en")
            ok = normalize_text(transcript.text) == normalize_text(FIXTURE_TEXT)
            checks.append(
                Capability(
                    f"{backend.name}-deep",
                    ok,
                    transcript.text,
                    "" if ok else "fixture transcript mismatch",
                )
            )
        except Exception as exc:
            checks.append(Capability(f"{backend.name}-deep", False, "", str(exc)))
    return checks
```

- [ ] **Step 7: Add Whisper CLI commands**

Append to `src/ugc_video/cli.py`:

```python
@whisper_app.command("install")
def whisper_install() -> None:
    from pathlib import Path
    from ugc_video.whisper.install import install_models

    paths = AppPaths.from_environment(os.environ)
    manifest = install_models(paths, Path("config/models.json"))
    typer.echo(f"Whisper model manifest: {manifest}")


@whisper_app.command("health")
def whisper_health(deep: bool = typer.Option(False, "--deep")) -> None:
    from ugc_video.whisper.health import inspect_whisper

    checks = inspect_whisper(deep=deep)
    for check in checks:
        typer.echo(f"{'PASS' if check.ok else 'FAIL'} {check.name}: {check.value or check.detail}")
    if not all(item.ok for item in checks):
        raise typer.Exit(2)


@whisper_app.command("repair")
def whisper_repair(backend: str) -> None:
    from pathlib import Path
    from ugc_video.whisper.install import repair_model

    paths = AppPaths.from_environment(os.environ)
    manifest = repair_model(paths, Path("config/models.json"), backend)
    typer.echo(f"Repaired {backend}; manifest: {manifest}")
```

- [ ] **Step 8: Run GREEN, perform static checks, and commit**

```bash
uv sync --extra dev --extra mac-whisper
uv run pytest tests/whisper/test_install_health.py -q
uv run ruff check src/ugc_video/whisper tests/whisper
uv run mypy src/ugc_video/whisper
git add config/models.json src/ugc_video/whisper src/ugc_video/cli.py tests/whisper/test_install_health.py
git commit -m "feat: install and health-check three Whisper backends"
```

Expected: tests, Ruff, and mypy exit `0` before the commit.

### Task 6: Apple Silicon bootstrap

**Files:**
- Create: `START-HERE-MAC.command`
- Create: `setup-macos.sh`
- Create: `scripts/download-models.sh`
- Create: `tests/platform/test_macos_scripts.py`

- [ ] **Step 1: Write failing script-contract tests**

```python
from pathlib import Path


def test_macos_setup_is_guarded_and_idempotent() -> None:
    script = Path("setup-macos.sh").read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in script
    assert '"$(uname -m)" != "arm64"' in script
    assert "command -v brew" in script
    assert "uv sync --frozen" in script
    assert "ugc-video doctor --fast" in script


def test_start_here_delegates_to_setup() -> None:
    launcher = Path("START-HERE-MAC.command").read_text(encoding="utf-8")
    assert 'exec "$ROOT/setup-macos.sh"' in launcher
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/platform/test_macos_scripts.py -q`

Expected: two failures because the scripts do not exist.

- [ ] **Step 3: Create the macOS launcher**

`START-HERE-MAC.command`:

```bash
#!/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$ROOT/setup-macos.sh"
```

- [ ] **Step 4: Create the idempotent macOS installer**

`setup-macos.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This installer supports Apple Silicon macOS only. Contact the instructor for alternatives." >&2
  exit 64
fi

MEMORY_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
if (( MEMORY_GB < 16 )); then
  echo "Warning: 16 GB RAM is recommended; detected ${MEMORY_GB} GB." >&2
fi
FREE_KB=$(df -Pk "$HOME" | awk 'NR==2 {print $4}')
if (( FREE_KB < 15728640 )); then
  echo "At least 15 GB free storage is required for setup and video outputs." >&2
  exit 64
fi

if ! command -v brew >/dev/null 2>&1; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

brew install git git-lfs node@22 python@3.11 ffmpeg rubberband uv whisper-cpp
brew link --overwrite node@22
npm install --global @openai/codex

if ! command -v grok >/dev/null 2>&1; then
  curl -fsSL https://x.ai/cli/install.sh | bash
fi
export PATH="$HOME/.grok/bin:$PATH"

cd "$ROOT"
uv sync --frozen --python 3.11 --extra dev --extra mac-whisper
if [[ -f "$ROOT/remotion/package.json" ]]; then
  npm install --prefix "$ROOT/remotion"
fi
"$ROOT/scripts/download-models.sh"
uv run ugc-video doctor --fast

echo "Local installation is ready. Run: uv run ugc-video setup"
```

- [ ] **Step 5: Create the shared model command**

`scripts/download-models.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
uv run ugc-video whisper install
uv run ugc-video whisper health --deep
```

- [ ] **Step 6: Verify scripts, run GREEN, and commit**

```bash
chmod +x START-HERE-MAC.command setup-macos.sh scripts/download-models.sh
bash -n START-HERE-MAC.command setup-macos.sh scripts/download-models.sh
uv run pytest tests/platform/test_macos_scripts.py -q
git add START-HERE-MAC.command setup-macos.sh scripts/download-models.sh tests/platform/test_macos_scripts.py
git commit -m "build: add Apple Silicon bootstrap"
```

Expected: Bash syntax passes and two tests pass.

### Task 7: Windows 11 and WSL2 bootstrap

**Files:**
- Create: `START-HERE-WINDOWS.cmd`
- Create: `setup-windows.ps1`
- Create: `scripts/setup-linux.sh`
- Create: `tests/platform/Test-WindowsScripts.ps1`

- [ ] **Step 1: Create PowerShell contract tests**

`tests/platform/Test-WindowsScripts.ps1`:

```powershell
$ErrorActionPreference = "Stop"
$setup = Get-Content "$PSScriptRoot/../../setup-windows.ps1" -Raw
$linux = Get-Content "$PSScriptRoot/../../scripts/setup-linux.sh" -Raw

if ($setup -notmatch "WSL2" -or $setup -notmatch "wsl.exe --install") {
    throw "Windows setup must install and verify WSL2"
}
if ($setup -notmatch "resume-windows-setup.json") {
    throw "Windows setup must write a reboot checkpoint"
}
if ($linux -notmatch "uv sync --frozen" -or $linux -notmatch "ugc-video doctor --fast") {
    throw "Linux setup must sync the package and run doctor"
}
Write-Output "Windows bootstrap contracts passed"
```

- [ ] **Step 2: Run the test and verify RED**

Run: `pwsh -NoProfile -File tests/platform/Test-WindowsScripts.ps1`

Expected: failure because `setup-windows.ps1` does not exist.

- [ ] **Step 3: Create the Windows launcher**

`START-HERE-WINDOWS.cmd`:

```batch
@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1"
if errorlevel 1 pause
```

- [ ] **Step 4: Create WSL2 setup and reboot checkpointing**

`setup-windows.ps1`:

```powershell
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateRoot = Join-Path $env:LOCALAPPDATA "ugc-video"
$Checkpoint = Join-Path $StateRoot "resume-windows-setup.json"
New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null

$os = Get-CimInstance Win32_OperatingSystem
if ([int]$os.BuildNumber -lt 22000) {
    throw "Windows 11 is required. Contact the instructor for alternatives."
}
$memoryGB = [math]::Floor($os.TotalVisibleMemorySize / 1MB)
if ($memoryGB -lt 16) {
    Write-Warning "16 GB RAM is recommended; detected $memoryGB GB."
}
$driveName = (Split-Path -Qualifier $Root).TrimEnd(':')
$drive = Get-PSDrive -Name $driveName
if ($drive.Free -lt 15GB) {
    throw "At least 15 GB free storage is required for setup and video outputs."
}
$virtualization = (Get-CimInstance Win32_Processor | Where-Object { $_.VirtualizationFirmwareEnabled })
if (-not $virtualization) {
    throw "Hardware virtualization must be enabled in firmware before installing WSL2."
}

$status = & wsl.exe --status 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or $status -notmatch "Default Version: 2") {
    @{ stage = "wsl-install"; root = $Root } |
        ConvertTo-Json | Set-Content -Encoding UTF8 $Checkpoint
    & wsl.exe --install -d Ubuntu
    Write-Host "Restart Windows, then run START-HERE-WINDOWS.cmd again."
    exit 3010
}

$distros = & wsl.exe --list --quiet
if ($distros -notcontains "Ubuntu") {
    & wsl.exe --install -d Ubuntu
    Write-Host "Finish the Ubuntu account prompt, then run START-HERE-WINDOWS.cmd again."
    exit 3010
}

$wslRoot = (& wsl.exe -d Ubuntu -- wslpath -a $Root).Trim()
$wslHome = (& wsl.exe -d Ubuntu -- bash -lc 'printf %s "$HOME"').Trim()
$wslTarget = "$wslHome/ugc-video-student-kit"
& wsl.exe -d Ubuntu -- bash -lc "mkdir -p '$wslTarget' && cp -a '$wslRoot/.' '$wslTarget/' && cd '$wslTarget' && ./scripts/setup-linux.sh"
if ($LASTEXITCODE -ne 0) {
    throw "WSL2 setup failed with exit code $LASTEXITCODE"
}
Remove-Item -Force -ErrorAction SilentlyContinue $Checkpoint
Write-Host "Installation complete. Open Ubuntu and run: cd '$wslTarget' && uv run ugc-video setup"
```

- [ ] **Step 5: Create the WSL Ubuntu bootstrap**

`scripts/setup-linux.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! grep -qi microsoft /proc/sys/kernel/osrelease; then
  echo "This Linux installer is supported inside Windows 11 WSL2 only." >&2
  exit 64
fi

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  build-essential cmake curl espeak-ng ffmpeg git git-lfs jq libsndfile1 \
  python3 python3-venv rubberband-cli

if ! command -v node >/dev/null 2>&1 || [[ "$(node --version)" != v22.* ]]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv python install 3.11

if ! command -v whisper-cli >/dev/null 2>&1; then
  BUILD_ROOT="$HOME/.cache/ugc-video/whisper.cpp"
  mkdir -p "$(dirname "$BUILD_ROOT")"
  if [[ ! -d "$BUILD_ROOT/.git" ]]; then
    git clone --branch v1.7.6 --depth 1 https://github.com/ggerganov/whisper.cpp.git "$BUILD_ROOT"
  fi
  cmake -S "$BUILD_ROOT" -B "$BUILD_ROOT/build" -DWHISPER_BUILD_EXAMPLES=ON
  cmake --build "$BUILD_ROOT/build" --config Release -j2
  sudo install -m 0755 "$BUILD_ROOT/build/bin/whisper-cli" /usr/local/bin/whisper-cli
fi

sudo npm install --global @openai/codex
if ! command -v grok >/dev/null 2>&1; then
  curl -fsSL https://x.ai/cli/install.sh | bash
  export PATH="$HOME/.grok/bin:$PATH"
fi

cd "$ROOT"
uv sync --frozen --python 3.11 --extra dev --extra wsl-whisper
if [[ -f "$ROOT/remotion/package.json" ]]; then
  npm install --prefix "$ROOT/remotion"
fi
./scripts/download-models.sh
uv run ugc-video doctor --fast
echo "WSL2 installation is ready. Run: uv run ugc-video setup"
```

- [ ] **Step 6: Verify scripts, run GREEN, and commit**

```bash
chmod +x scripts/setup-linux.sh
bash -n scripts/setup-linux.sh
pwsh -NoProfile -File tests/platform/Test-WindowsScripts.ps1
git add START-HERE-WINDOWS.cmd setup-windows.ps1 scripts/setup-linux.sh tests/platform/Test-WindowsScripts.ps1
git commit -m "build: add Windows 11 WSL2 bootstrap"
```

Expected: Bash syntax and PowerShell contract tests pass.

### Task 8: Scoped uninstall and foundation acceptance

**Files:**
- Create: `scripts/uninstall.sh`
- Create: `tests/platform/test_uninstall.py`
- Modify: `README.md` only if a temporary foundation command reference is necessary for acceptance; the student README is completed in Plan 3.

- [ ] **Step 1: Write a failing uninstall ownership test**

```python
import os
import subprocess
from pathlib import Path


def test_uninstall_removes_only_kit_owned_root(tmp_path: Path) -> None:
    home = tmp_path / "home"
    kit = home / ".local/share/ugc-video"
    unrelated = home / ".local/share/unrelated"
    kit.mkdir(parents=True)
    unrelated.mkdir(parents=True)
    env = {**os.environ, "HOME": str(home), "UGC_VIDEO_HOME": str(kit)}
    subprocess.run(["bash", "scripts/uninstall.sh", "--yes"], check=True, env=env)
    assert not kit.exists()
    assert unrelated.exists()
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/platform/test_uninstall.py -q`

Expected: failure because `scripts/uninstall.sh` does not exist.

- [ ] **Step 3: Create the scoped uninstaller**

`scripts/uninstall.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail

YES=0
if [[ "${1:-}" == "--yes" ]]; then
  YES=1
fi

ROOT="${UGC_VIDEO_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/ugc-video}"
case "$ROOT" in
  "$HOME"|"/"|"")
    echo "Refusing unsafe uninstall root: $ROOT" >&2
    exit 64
    ;;
esac

if [[ $YES -ne 1 ]]; then
  read -r -p "Remove kit-owned data at $ROOT? [y/N] " answer
  [[ "$answer" == "y" || "$answer" == "Y" ]] || exit 0
fi

rm -rf -- "$ROOT"
echo "Removed kit-owned data: $ROOT"
echo "Shared tools such as Python, Node, FFmpeg, Homebrew, WSL2, Codex, and Grok were retained."
```

- [ ] **Step 4: Run full foundation verification**

```bash
chmod +x scripts/uninstall.sh
uv run pytest tests/foundation tests/whisper tests/platform -q
uv run ruff check src tests/foundation tests/whisper tests/platform
uv run mypy src
bash -n START-HERE-MAC.command setup-macos.sh scripts/setup-linux.sh scripts/download-models.sh scripts/uninstall.sh
pwsh -NoProfile -File tests/platform/Test-WindowsScripts.ps1
```

Expected: every command exits `0`.

- [ ] **Step 5: Commit foundation completion**

```bash
git add scripts/uninstall.sh tests/platform/test_uninstall.py
git commit -m "feat: add scoped uninstall and foundation checks"
```

- [ ] **Step 6: Record the integration checkpoint**

Run:

```bash
git status --short
git log --oneline --max-count=8
```

Expected: empty status and eight coherent task commits for the foundation plan.
