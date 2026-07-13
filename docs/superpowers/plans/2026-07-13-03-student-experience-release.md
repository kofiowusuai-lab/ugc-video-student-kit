# Student Experience, Security, and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $subagent-driven-development (recommended) or $executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the tested installer and pipeline into a safe public teaching repository with a bundled Codex skill, transparent progress, a reproducible demo, secret prevention, accurate subscription guidance, cross-platform CI, and controlled publication.

**Architecture:** The repository-level AGENTS instructions and installed Codex skill own the creative script/still steps, then call the deterministic local CLI. Student documentation separates required accounts from paid recommendations and date-stamps changing vendor terms. CI remains non-billable; credentialed and clean-machine checks are explicit release gates performed outside CI.

**Tech Stack:** Codex skills, Markdown, Typer/Rich progress, Gitleaks, pre-commit, GitHub Actions, pytest, Ruff, mypy, Bash, PowerShell, GitHub CLI.

---

## File map

- `AGENTS.md` — repository operating rules for Codex and students.
- `codex-skills/ugc-video-producer/SKILL.md` — creative and deterministic orchestration.
- `scripts/install-codex-skill.sh` — idempotent user-scope skill installation.
- `src/ugc_video/progress.py` — elapsed-time events and heartbeat messages.
- `src/ugc_video/demo.py` — copy legal demo inputs and choose cloud/offline services.
- `demo/` — brief, natural script, generated presenter asset, and provenance record.
- `.gitleaks.toml`, `.pre-commit-config.yaml`, `scripts/check-secrets.sh` — secret controls.
- `README.md` — primary student setup and use path.
- `docs/SUBSCRIPTIONS.md` — dated vendor account and license details.
- `docs/TROUBLESHOOTING.md` — failure category to concrete action.
- `docs/ALTERNATIVE-MACHINES.md` — supported boundary and instructor contact direction.
- `docs/PRIVACY-CONSENT.md` — cloud boundary, voice/likeness permission, and provenance.
- `.github/workflows/quality.yml` — non-billable tests and static checks.
- `.github/workflows/release.yml` — tag validation and checksummed source artifact.
- `scripts/acceptance.sh`, `docs/RELEASE-CHECKLIST.md` — clean-machine and deployment gate.

### Task 1: Repository instructions and installable Codex skill

**Files:**
- Create: `AGENTS.md`
- Create: `codex-skills/ugc-video-producer/SKILL.md`
- Create: `scripts/install-codex-skill.sh`
- Modify: `setup-macos.sh`
- Modify: `scripts/setup-linux.sh`
- Create: `tests/student/test_skill.py`

- [ ] **Step 1: Write failing skill-contract tests**

```python
from pathlib import Path


def test_skill_preserves_required_gates_and_commands() -> None:
    skill = Path("codex-skills/ugc-video-producer/SKILL.md").read_text(encoding="utf-8")
    assert "ugc-video doctor --fast" in skill
    assert "killer-script-system" in skill
    assert "imagegen" in skill
    assert "ugc-video run" in skill
    assert "ugc-video resume" in skill
    assert "Do not expose API keys" in skill
    assert "Do not bypass" in skill


def test_install_script_targets_user_codex_home() -> None:
    script = Path("scripts/install-codex-skill.sh").read_text(encoding="utf-8")
    assert '${CODEX_HOME:-$HOME/.codex}/skills/ugc-video-producer' in script
    assert "cp -R" in script
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/student/test_skill.py -q`

Expected: failures because the skill and install script do not exist.

- [ ] **Step 3: Create repository-level Codex rules**

`AGENTS.md`:

```markdown
# AGENTS.md

## Scope

These rules apply to the entire `ugc-video-student-kit` repository.

## Student workflow

1. Read `README.md` before running installation or production commands.
2. Run `ugc-video doctor --fast` before cloud generation.
3. Use the bundled `ugc-video-producer` skill for creative production.
4. Keep scripts, stills, generated media, manifests, and QA artifacts inside the active project.
5. Use `ugc-video status` and `ugc-video resume` after an interruption.

## Safety and secrets

- Never print, paste into prompts, commit, or upload API keys.
- Never bypass provider moderation, watermarks, provenance, or account limits.
- Use only voices, likenesses, music, and product assets you are authorized to use.
- Free ElevenLabs output is non-commercial and requires attribution; use an eligible commercial plan for ads.
- Stop after two retries of the same failed external action and report the concrete failure.

## Development

- Follow the approved design and implementation plans under `docs/superpowers/`.
- Write a failing test before changing behavior.
- Keep cloud calls out of automated CI.
- Preserve generated-output and secret exclusions in `.gitignore`.
```

- [ ] **Step 4: Create the production skill**

`codex-skills/ugc-video-producer/SKILL.md`:

```markdown
---
name: ugc-video-producer
description: Produce a realistic UGC spokesperson video from a brief using natural scripting, a generated still, Grok animation, Fish Audio with ElevenLabs fallback, local Whisper QA, and local finishing.
---

# UGC Video Producer

Use this skill when the student asks to create, test, resume, or inspect a UGC video project made with this repository.

## Preconditions

1. Read the repository `AGENTS.md` and the active project's `brief.json`.
2. Run `uv run ugc-video doctor --fast` from the repository root.
3. Stop on unsupported-machine, missing-login, policy, consent, or licensing failures.
4. Do not expose API keys in prompts, commands, logs, or chat.

## Production

Set `PROJECT_PATH` to the absolute path printed by `ugc-video new`.

1. Use the `killer-script-system` skill to write one concise, spoken script. Prefer complete natural openings such as “I had a feeling” over compressed fragments such as “Had a feeling.” Save only the approved dialogue to `$PROJECT_PATH/script.txt`.
2. Use the `imagegen` skill to generate an adult UGC spokesperson still at 1080×1920. Keep the person fully clothed, brand-safe, naturally attractive, and realistically framed. Inspect identity, hands, clothing, background, and unexpected text. Save the approved still to `$PROJECT_PATH/assets/still.png`.
3. Run `uv run ugc-video run "$PROJECT_PATH"`.
4. In Grok guided mode, follow `$PROJECT_PATH/work/grok-handoff.json`, save the resulting clip at the exact destination in that file, then run `uv run ugc-video resume "$PROJECT_PATH"`.
5. Review `$PROJECT_PATH/run.json`, the transcript checks, time factor, provider metadata, and `$PROJECT_PATH/output/final.mp4`.
6. If the timing gate requests regeneration, adjust Grok speaking pace and regenerate the animation. Do not force an unnatural audio speed.

## Provider policy

- Fish Audio is primary.
- ElevenLabs is the fallback for outage, quota, unavailable model, or invalid Fish entitlement.
- Do not bypass a policy, consent, or licensing rejection by switching providers.
- Never assume a Fish voice ID is valid in ElevenLabs.

## Completion

Report the final video path, provider used, Whisper backend used, timing factor, QA outcome, and any commercial-license warning. Do not claim completion when a stage is failed or unverified.
```

- [ ] **Step 5: Create the idempotent skill installer**

`scripts/install-codex-skill.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/codex-skills/ugc-video-producer"
DESTINATION="${CODEX_HOME:-$HOME/.codex}/skills/ugc-video-producer"
mkdir -p "$(dirname "$DESTINATION")"
rm -rf -- "$DESTINATION"
cp -R "$SOURCE" "$DESTINATION"
echo "Installed Codex skill: $DESTINATION"
```

- [ ] **Step 6: Call the skill installer from both supported bootstraps**

Insert immediately after `uv sync` in `setup-macos.sh` and `scripts/setup-linux.sh`:

```bash
"$ROOT/scripts/install-codex-skill.sh"
```

- [ ] **Step 7: Run GREEN and commit**

```bash
chmod +x scripts/install-codex-skill.sh
bash -n scripts/install-codex-skill.sh setup-macos.sh scripts/setup-linux.sh
uv run pytest tests/student/test_skill.py -q
git add AGENTS.md codex-skills scripts/install-codex-skill.sh setup-macos.sh scripts/setup-linux.sh tests/student/test_skill.py
git commit -m "feat: bundle the Codex UGC production skill"
```

Expected: two tests pass and all Bash files parse.

### Task 2: Transparent stage progress and sanitized logs

**Files:**
- Create: `src/ugc_video/progress.py`
- Modify: `src/ugc_video/pipeline/orchestrator.py`
- Modify: `src/ugc_video/providers/grok.py`
- Modify: `src/ugc_video/cli.py`
- Create: `tests/student/test_progress.py`
- Modify: `tests/providers/test_grok.py`

- [ ] **Step 1: Write failing progress tests**

```python
import io

from ugc_video.progress import ProgressReporter


def test_progress_reports_elapsed_stage_without_secret() -> None:
    stream = io.StringIO()
    times = iter([10.0, 10.0, 12.5])
    reporter = ProgressReporter(stream=stream, clock=lambda: next(times), secrets=["secret-123"])
    reporter.start("voice", "using secret-123")
    reporter.update("voice", "waiting")
    output = stream.getvalue()
    assert "[0.00s] voice: using [REDACTED]" in output
    assert "[2.50s] voice: waiting" in output
    assert "secret-123" not in output
```

In `tests/providers/test_grok.py`, update the successful API test to construct the provider with `progress=messages.append` and add:

```python
messages: list[str] = []
provider = GrokApiProvider("xai-key", sleep=lambda _: None, progress=messages.append)
result = provider.animate(request)
assert any("req-1: pending, progress=25" in message for message in messages)
assert any("req-1: done" in message for message in messages)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/student/test_progress.py -q`

Expected: collection fails because `ugc_video.progress` does not exist.

- [ ] **Step 3: Implement elapsed progress events**

`src/ugc_video/progress.py`:

```python
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TextIO

from ugc_video.redaction import redact


@dataclass
class ProgressReporter:
    stream: TextIO = sys.stderr
    clock: Callable[[], float] = time.monotonic
    secrets: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.started_at = self.clock()

    def _emit(self, stage: str, message: str) -> None:
        elapsed = self.clock() - self.started_at
        safe = redact(message, self.secrets)
        self.stream.write(f"[{elapsed:.2f}s] {stage}: {safe}\n")
        self.stream.flush()

    def start(self, stage: str, message: str) -> None:
        self._emit(stage, message)

    def update(self, stage: str, message: str) -> None:
        self._emit(stage, message)

    def complete(self, stage: str, message: str) -> None:
        self._emit(stage, message)
```

- [ ] **Step 4: Wire progress into long operations**

Add to `GrokApiProvider.__init__`:

```python
progress: Callable[[str], None] = lambda message: None,
```

Store it with `self.progress = progress`. Immediately after each successful polling payload, add:

```python
status = str(payload.get("status", "unknown"))
reported = payload.get("progress")
suffix = f", progress={reported}" if reported is not None else ""
self.progress(f"Grok request {request_id}: {status}{suffix}")
```

Update `_run_stage` in `pipeline/orchestrator.py` to accept `reporter: ProgressReporter | None = None` and wrap its existing behavior with:

```python
if store.can_reuse(name, digest):
    if reporter:
        reporter.complete(name, "reused verified checkpoint")
    return
if reporter:
    reporter.start(name, "started")
store.start(name, digest)
try:
    metadata = operation()
    if not all(path.exists() and path.stat().st_size > 0 for path in outputs):
        raise RuntimeError(f"{name} produced no usable output")
    store.complete(name, digest, outputs, metadata)
    if reporter:
        reporter.complete(name, "passed")
except Exception as exc:
    store.fail(name, str(exc))
    if reporter:
        reporter.update(name, f"failed: {exc}")
    raise
```

Add `reporter: ProgressReporter | None = None` to `run_pipeline`, and pass it to every `_run_stage` call. Add `reporter: ProgressReporter | None = None` to `build_services`; construct `GrokApiProvider` with:

```python
progress=(lambda message: reporter.update("animation", message)) if reporter else (lambda message: None)
```

In the CLI `run` command, create and pass the same reporter:

```python
reporter = ProgressReporter(secrets=list(secrets.values()))
services = build_services(config, secrets, project_config, reporter=reporter)
output = run_pipeline(project_config, services, reporter=reporter)
```

Import `ProgressReporter` where referenced. Grok polls every five seconds, so these callbacks provide a heartbeat without inventing progress when the provider omits it.

- [ ] **Step 5: Run GREEN and commit**

```bash
uv run pytest tests/student/test_progress.py tests/pipeline tests/providers/test_grok.py -q
uv run mypy src
git add src/ugc_video/progress.py src/ugc_video/pipeline/orchestrator.py src/ugc_video/providers/grok.py src/ugc_video/cli.py tests/student/test_progress.py
git commit -m "feat: show elapsed pipeline progress"
```

Expected: tests and mypy exit `0`; captured logs contain no test secret.

### Task 3: Reproducible demo project

**Files:**
- Create: `demo/brief.json`
- Create: `demo/script.txt`
- Create: `demo/ASSET-LICENSE.md`
- Create: `demo/assets/presenter.png`
- Create: `src/ugc_video/demo.py`
- Modify: `src/ugc_video/cli.py`
- Create: `tests/student/test_demo.py`

- [ ] **Step 1: Write failing demo-copy tests**

```python
from pathlib import Path

from typer.testing import CliRunner

from ugc_video.cli import app
from ugc_video.demo import prepare_demo


def test_demo_copies_inputs_without_overwriting_run_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "assets").mkdir(parents=True)
    (source / "brief.json").write_text('{"product":"Student Kit"}\n', encoding="utf-8")
    (source / "script.txt").write_text("I had a feeling this would save me time.\n", encoding="utf-8")
    (source / "assets/presenter.png").write_bytes(b"png")
    destination = tmp_path / "demo-run"
    project = prepare_demo(source, destination)
    assert project.script.read_text().startswith("I had a feeling")
    assert project.still.read_bytes() == b"png"
    assert not project.manifest.exists()


def test_offline_demo_produces_final_media(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    result = CliRunner().invoke(app, ["demo", "--offline-fixtures"])
    assert result.exit_code == 0
    assert (tmp_path / "home/projects/demo/output/final.mp4").is_file()
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/student/test_demo.py -q`

Expected: collection fails because `ugc_video.demo` does not exist.

- [ ] **Step 3: Create the demo brief and natural script**

`demo/brief.json`:

```json
{
  "product": "UGC Video Student Kit",
  "audience": "students learning an end-to-end AI video workflow",
  "proof": "local health checks and resumable production stages",
  "cta": "Run the demo before starting your first project"
}
```

`demo/script.txt`:

```text
I had a feeling this setup would save me time, but seeing every step checked before I generate anything makes the whole workflow feel much easier.
```

- [ ] **Step 4: Generate and approve the distributable demo still**

Use the `imagegen` skill with this exact prompt:

```text
Create a photorealistic vertical 1080x1920 UGC still of a fictional adult woman in her late twenties, friendly and naturally attractive, wearing a modest solid-color casual top, seated in a bright neutral home-office setting, looking into a phone-height camera. Natural skin texture, realistic hands, subtle everyday makeup, relaxed posture, soft window light, no logos, no text, no products, no resemblance to a real person, brand-safe and suitable for a public educational repository.
```

Inspect the output for adult appearance, realistic hands, modest clothing, no text/logo, and no resemblance claim. Save the approved PNG as `demo/assets/presenter.png`. Record the generation date, prompt, fictional-identity statement, and repository MIT distribution permission in `demo/ASSET-LICENSE.md`.

Create `demo/ASSET-LICENSE.md` with:

```markdown
# Demo asset provenance

`assets/presenter.png` was generated on July 13, 2026 for this repository from the prompt recorded in Task 3 of the approved release plan. The depicted adult is fictional and is not presented as a real person or endorsement. The repository author permits redistribution of this demo asset with the repository under the MIT License. Students may replace it with an asset they are authorized to use.

The SHA-256 recorded below verifies the reviewed asset:
```

Append the actual digest without manually copying it:

```bash
printf '\n```text\n%s  demo/assets/presenter.png\n```\n' "$(shasum -a 256 demo/assets/presenter.png | awk '{print $1}')" >> demo/ASSET-LICENSE.md
```

- [ ] **Step 5: Implement deterministic demo preparation**

`src/ugc_video/demo.py`:

```python
import json
import shutil
import subprocess
from pathlib import Path

from ugc_video.pipeline.orchestrator import PipelineServices
from ugc_video.pipeline.project import ProjectPaths, create_project
from ugc_video.render.finish import finish_video


def prepare_demo(source: Path, destination: Path) -> ProjectPaths:
    brief = json.loads((source / "brief.json").read_text(encoding="utf-8"))
    project = create_project(destination, brief)
    shutil.copy2(source / "script.txt", project.script)
    project.still.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "assets/presenter.png", project.still)
    return project


def build_offline_services() -> PipelineServices:
    def animate(script: str, still: Path, output: Path) -> dict[str, str]:
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-loop", "1", "-i", str(still),
                "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                "-t", "2", "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-shortest", str(output),
            ],
            check=True,
        )
        return {"provider": "offline-fixture"}

    def voice(script: str, output: Path) -> dict[str, str]:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                "-i", "sine=frequency=220:duration=2", "-q:a", "4", str(output),
            ],
            check=True,
        )
        return {"provider": "offline-fixture"}

    def verify(media: Path, expected: str) -> dict[str, str]:
        if not media.is_file() or media.stat().st_size == 0:
            raise RuntimeError("offline fixture media is missing")
        return {"backend": "offline-fixture", "text": expected}

    def finish(animation: Path, audio: Path, output: Path) -> dict[str, str]:
        finish_video(animation, audio, output)
        return {"renderer": "ffmpeg-offline-fixture"}

    return PipelineServices(animate=animate, voice=voice, verify=verify, finish=finish)
```

- [ ] **Step 6: Add the demo command**

Append to `src/ugc_video/cli.py`:

```python
@app.command()
def demo(
    offline_fixtures: bool = typer.Option(False, "--offline-fixtures"),
) -> None:
    paths = AppPaths.from_environment(os.environ)
    project = prepare_demo(Path("demo"), paths.projects / "demo")
    if offline_fixtures:
        output = run_pipeline(project, build_offline_services())
        typer.echo(f"Offline demo complete: {output}")
        return
    run(project.root)
```

Import `prepare_demo`, `build_offline_services`, and `run_pipeline`. Before copying, retain an existing `run.json` and `output/` directory so a repeated demo command can resume.

- [ ] **Step 7: Run GREEN and commit**

```bash
uv run pytest tests/student/test_demo.py -q
uv run ugc-video demo --offline-fixtures
git add demo src/ugc_video/demo.py src/ugc_video/cli.py tests/student/test_demo.py
git commit -m "feat: add reproducible student demo"
```

Expected: test passes and offline preparation prints the project path without a cloud call.

### Task 4: Secret prevention and repository hygiene

**Files:**
- Create: `.gitleaks.toml`
- Create: `.pre-commit-config.yaml`
- Create: `scripts/check-secrets.sh`
- Create: `tests/security/test_repository_hygiene.py`

- [ ] **Step 1: Write failing repository-hygiene tests**

```python
from pathlib import Path


def test_secret_and_output_patterns_are_ignored() -> None:
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in [".env", "secrets.env", "auth.json", "*.mp4", "models/"]:
        assert pattern in ignored


def test_secret_check_scans_git_history_and_worktree() -> None:
    script = Path("scripts/check-secrets.sh").read_text(encoding="utf-8")
    assert "gitleaks git" in script
    assert "gitleaks dir" in script
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/security/test_repository_hygiene.py -q`

Expected: failure because `scripts/check-secrets.sh` does not exist.

- [ ] **Step 3: Configure Gitleaks**

`.gitleaks.toml`:

```toml
title = "ugc-video-student-kit secret rules"

[extend]
useDefault = true

[[rules]]
id = "ugc-video-provider-key"
description = "Cloud provider key assigned in a file"
regex = '''(?i)(FISH_AUDIO_API_KEY|ELEVENLABS_API_KEY|XAI_API_KEY)\s*=\s*[^\s#]{8,}'''
keywords = ["API_KEY"]

[allowlist]
description = "Empty documentation placeholders"
regexTarget = "line"
regexes = ['''(?i)(FISH_AUDIO_API_KEY|ELEVENLABS_API_KEY|XAI_API_KEY)=$''']
paths = ['''.env.example''']
```

- [ ] **Step 4: Configure pre-commit and the explicit scan command**

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.28.0
    hooks:
      - id: gitleaks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.2
    hooks:
      - id: ruff-check
      - id: ruff-format
```

`scripts/check-secrets.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail
gitleaks git --no-banner --redact
gitleaks dir . --no-banner --redact
if git ls-files | grep -E '(^|/)(\.env|secrets\.env|auth\.json)$|\.(mp3|wav|opus|mp4|mov)$' >/dev/null; then
  echo "Tracked secret or generated-media file detected." >&2
  exit 1
fi
```

- [ ] **Step 5: Run GREEN and commit**

```bash
chmod +x scripts/check-secrets.sh
uv run pytest tests/security/test_repository_hygiene.py -q
scripts/check-secrets.sh
git add .gitleaks.toml .pre-commit-config.yaml scripts/check-secrets.sh tests/security/test_repository_hygiene.py
git commit -m "build: prevent secrets and generated media commits"
```

Expected: tests pass and both Gitleaks scans return no findings.

### Task 5: Student README and live subscription guidance

**Files:**
- Modify: `README.md`
- Create: `docs/SUBSCRIPTIONS.md`
- Create: `docs/TROUBLESHOOTING.md`
- Create: `docs/ALTERNATIVE-MACHINES.md`
- Create: `docs/PRIVACY-CONSENT.md`
- Create: `tests/student/test_docs.py`

- [ ] **Step 1: Write failing documentation-contract tests**

```python
from pathlib import Path


def test_readme_has_supported_paths_and_start_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    for text in [
        "Apple Silicon",
        "Windows 11 with WSL2",
        "16 GB RAM",
        "START-HERE-MAC.command",
        "START-HERE-WINDOWS.cmd",
        "contact the instructor",
        "ugc-video doctor --full",
        "ugc-video demo",
    ]:
        assert text in readme


def test_subscriptions_are_dated_and_license_aware() -> None:
    subscriptions = Path("docs/SUBSCRIPTIONS.md").read_text(encoding="utf-8")
    for text in [
        "Last verified: July 13, 2026",
        "10,000 credits",
        "non-commercial use with attribution",
        "s2.1-pro-free",
        "end of July 2026",
        "SuperGrok",
        "xAI API billing",
        "ElevenLabs is not required",
    ]:
        assert text in subscriptions
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/student/test_docs.py -q`

Expected: failures because the student documents do not exist.

- [ ] **Step 3: Write the README as the shortest successful path**

The README must use this section order and these exact commands:

````markdown
# UGC Video Student Kit

Build a vertical UGC spokesperson video with Codex, Grok, Fish Audio with ElevenLabs fallback, three local Whisper checks, and FFmpeg/Remotion finishing.

## Supported computers

- Apple Silicon MacBook on a current supported macOS release.
- Windows 11 with WSL2 and Ubuntu.
- 16 GB RAM recommended.
- 15 GB free storage recommended before model and video downloads.
- Stable internet for Codex, Grok, Fish Audio, ElevenLabs fallback, and initial model downloads.

Intel Macs, older Windows releases, native Windows without WSL2, and other Linux distributions are not supported by the first release. If your machine is outside this list, contact the instructor through the course contact channel for an alternative.

## Start here

### Mac

Double-click `START-HERE-MAC.command`, or run:

```bash
chmod +x START-HERE-MAC.command setup-macos.sh scripts/*.sh
./setup-macos.sh
```

### Windows

Double-click `START-HERE-WINDOWS.cmd`. Restart if WSL asks, then run the same file again.

## Configure your own accounts

```bash
codex login
grok
uv run ugc-video setup
uv run ugc-video doctor --full
```

Complete the Grok sign-in prompt, then exit back to the terminal before continuing.

Your keys stay in a local ignored file. Never paste them into a prompt or commit them.

## Verify the complete workflow

```bash
uv run ugc-video demo
uv run ugc-video status ~/.local/share/ugc-video/projects/demo
```

## Start a project

```bash
uv run ugc-video new my-first-ad --product "My Product" --cta "Try it today"
codex
```

Inside Codex, ask: `Use the ugc-video-producer skill for my-first-ad.`

If a run stops:

```bash
PROJECT_PATH="$HOME/.local/share/ugc-video/projects/my-first-ad"
uv run ugc-video status "$PROJECT_PATH"
uv run ugc-video resume "$PROJECT_PATH"
```
````

Add this navigation below the successful path:

```markdown
## More help

- [Accounts and subscriptions](docs/SUBSCRIPTIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Alternative machines](docs/ALTERNATIVE-MACHINES.md)
- [Privacy, consent, and commercial use](docs/PRIVACY-CONSENT.md)
- Uninstall: `./scripts/uninstall.sh`
- [MIT License](LICENSE)
```

- [ ] **Step 4: Write dated subscription guidance**

`docs/SUBSCRIPTIONS.md` must include this table followed by official links:

```markdown
# Accounts, subscriptions, and usage

Last verified: July 13, 2026. Provider plans change; check the linked live pages before purchasing or publishing commercial work.

| Service | Minimum for a test | Recommended for the course | Commercial note |
|---|---|---|---|
| GitHub | Free account | Free account | Repository access only |
| Codex | Eligible ChatGPT Free login | Plus or Pro for sustained usage | Limits vary by plan |
| Grok guided mode | Grok free access when available | SuperGrok for higher limits | Preserve Grok provenance and watermarking |
| Grok automatic mode | xAI API key with billing | A controlled xAI API budget | SuperGrok does not replace xAI API billing |
| Fish Audio | Personal API key and `s2.1-pro-free` while available | Paid plan when SLA or commercial terms require it | The announced free window runs through the end of July 2026 and is not permanent |
| ElevenLabs fallback | Free API plan with 10,000 credits monthly | Starter or higher when cloning or commercial licensing is needed | Free output is for non-commercial use with attribution |
| Claude | Not required | Optional for students who already use it | The bundled Codex script workflow is sufficient |

ElevenLabs is not required when Fish Audio is available. It is the configured fallback for outages, quota, and unavailable Fish entitlements.
```

Append these live references:

```markdown
## Official live references

- [OpenAI: Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-chatgpt)
- [xAI: Grok plans and usage](https://docs.x.ai/grok/overview)
- [xAI: Imagine API pricing](https://docs.x.ai/developers/pricing)
- [Fish Audio: S2.1 Pro free API announcement](https://fish.audio/blog/s2-1-pro-free-api/)
- [Fish Audio: Pricing and rate limits](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits)
- [ElevenLabs: Current pricing](https://elevenlabs.io/pricing)
- [ElevenLabs: Billing and licensing](https://elevenlabs.io/docs/overview/administration/billing)
- [ElevenLabs: API authentication](https://elevenlabs.io/docs/api-reference/authentication)
```

- [ ] **Step 5: Write troubleshooting, alternatives, and consent documents**

`docs/TROUBLESHOOTING.md`:

```markdown
# Troubleshooting

| Message | Check | Next action |
|---|---|---|
| Unsupported platform | Read `ALTERNATIVE-MACHINES.md` | Contact the instructor through the course contact channel |
| Missing executable | `uv run ugc-video doctor --fast` | Rerun the supported `START HERE` launcher |
| Whisper model or backend failure | `uv run ugc-video whisper health --deep` | Run `uv run ugc-video whisper repair whispercpp-small-en` using the failed backend name, then repeat deep health |
| Fish authentication or quota failure | `uv run ugc-video doctor --provider fish` | Correct the local Fish key or allow the configured ElevenLabs fallback |
| ElevenLabs license warning | Read `SUBSCRIPTIONS.md` | Test non-commercially with attribution or obtain an eligible plan before publishing an ad |
| Grok request interrupted | `uv run ugc-video status "$PROJECT_PATH"` | Run `uv run ugc-video resume "$PROJECT_PATH"` without submitting a duplicate request |
| Dialogue mismatch | Read the mismatch in `$PROJECT_PATH/run.json` | Regenerate the animation with the exact script |
| Unnatural time factor | Read the factor in `$PROJECT_PATH/run.json` | Regenerate Grok with adjusted speaking pace instead of forcing the audio |

Never paste an API key into a support message. Provider-policy, consent, and licensing failures are not retryable through another provider.
```

`docs/ALTERNATIVE-MACHINES.md`:

```markdown
# Alternative machines

The supported first release targets Apple Silicon MacBooks and Windows 11 with WSL2 Ubuntu. Intel Macs, Windows without WSL2, older Windows releases, Chromebooks, mobile devices, and other Linux distributions may require different packages, cloud rendering, or a hosted development machine.

Do not force the supported installer onto an incompatible computer. Contact the instructor through the contact channel provided with the course and include:

- Computer model
- Operating-system version
- RAM
- Available storage
- Whether virtualization or WSL2 is available

Do not include API keys, passwords, account screenshots containing tokens, or private media.
```

`docs/PRIVACY-CONSENT.md`:

```markdown
# Privacy, consent, and commercial use

## What stays local

Project checkpoints, local Whisper models and transcripts, time fitting, FFmpeg/Remotion rendering, and final output files stay on the student's machine unless the student uploads or shares them.

## What is sent to cloud providers

- Codex receives the brief, script context, and still-generation prompt used in its session.
- Grok receives the approved still and animation prompt; guided and API modes follow the student's xAI account settings.
- Fish Audio receives the dialogue and selected Fish voice reference identifier.
- ElevenLabs receives the dialogue and selected ElevenLabs voice identifier only when explicitly selected or used as fallback.

## Consent

Use only voices, likenesses, products, music, footage, and scripts you own or have permission to use. Do not clone or imitate a real person's voice without documented authorization. Do not create deceptive endorsements.

## Commercial publication

Check each provider's current license before publishing. ElevenLabs Free output is non-commercial and requires attribution. Fish Audio's temporary free API may have commercial restrictions. Preserve required Grok watermarks and provenance signals. Switching providers must never be used to bypass a moderation, consent, or licensing decision.
```

- [ ] **Step 6: Run GREEN and commit**

```bash
uv run pytest tests/student/test_docs.py -q
uv run python -m compileall src
git add README.md docs/SUBSCRIPTIONS.md docs/TROUBLESHOOTING.md docs/ALTERNATIVE-MACHINES.md docs/PRIVACY-CONSENT.md tests/student/test_docs.py
git commit -m "docs: add complete student setup and account guidance"
```

Expected: documentation contracts and Python compilation pass.

### Task 6: Non-billable cross-platform CI

**Files:**
- Create: `.github/workflows/quality.yml`
- Create: `.github/workflows/release.yml`
- Create: `tests/platform/test_no_live_ci.py`

- [ ] **Step 1: Write the CI safety test**

```python
from pathlib import Path


def test_ci_never_runs_cloud_demo_or_reads_provider_keys() -> None:
    workflows = "\n".join(path.read_text(encoding="utf-8") for path in Path(".github/workflows").glob("*.yml"))
    assert "ugc-video demo\n" not in workflows
    assert "--offline-fixtures" in workflows
    for secret in ["FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY", "XAI_API_KEY"]:
        assert secret not in workflows
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/platform/test_no_live_ci.py -q`

Expected: failure because workflow files do not exist.

- [ ] **Step 3: Create quality CI**

`.github/workflows/quality.yml`:

```yaml
name: quality
on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  python:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-14]
        python: ['3.11', '3.12']
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          python-version: ${{ matrix.python }}
      - if: runner.os == 'Linux'
        run: sudo apt-get update
      - if: runner.os == 'Linux'
        run: sudo apt-get install -y ffmpeg
      - if: runner.os == 'macOS'
        run: brew install ffmpeg
      - run: uv sync --extra dev
      - run: uv run pytest -q
      - run: uv run ruff check .
      - run: uv run mypy src
      - run: uv run ugc-video demo --offline-fixtures

  scripts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash -n setup-macos.sh scripts/*.sh START-HERE-MAC.command
      - uses: gitleaks/gitleaks-action@v2

  remotion:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: remotion/package-lock.json
      - run: npm ci --prefix remotion
      - run: npm --prefix remotion exec tsc -- --noEmit

  windows-contract:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - shell: pwsh
        run: ./tests/platform/Test-WindowsScripts.ps1
```

- [ ] **Step 4: Create release validation without publication authority**

`.github/workflows/release.yml`:

```yaml
name: release-check
on:
  push:
    tags: ['v*']

permissions:
  contents: read

jobs:
  verify-source:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          python-version: '3.11'
      - run: sudo apt-get update
      - run: sudo apt-get install -y ffmpeg
      - run: uv sync --extra dev
      - run: uv run pytest -q
      - run: uv build
      - run: sha256sum dist/* > dist/SHA256SUMS
      - uses: actions/upload-artifact@v4
        with:
          name: verified-source-artifacts
          path: dist/
```

The workflow validates tag artifacts but does not create a public GitHub release. Publication remains a human deployment gate.

- [ ] **Step 5: Run GREEN and commit**

```bash
uv run pytest tests/platform/test_no_live_ci.py -q
git add .github/workflows tests/platform/test_no_live_ci.py
git commit -m "ci: add non-billable cross-platform checks"
```

Expected: test passes and no provider secret names occur in workflows.

### Task 7: Acceptance, rollback, and publication checklist

**Files:**
- Create: `scripts/acceptance.sh`
- Create: `docs/RELEASE-CHECKLIST.md`
- Create: `CHANGELOG.md`
- Create: `tests/release/test_release_gate.py`

- [ ] **Step 1: Write failing release-gate tests**

```python
from pathlib import Path


def test_release_checklist_requires_both_clean_machines_and_rollback() -> None:
    checklist = Path("docs/RELEASE-CHECKLIST.md").read_text(encoding="utf-8")
    for text in [
        "Apple Silicon clean-machine",
        "Windows 11/WSL2 clean-machine",
        "Fish Audio primary smoke test",
        "ElevenLabs fallback smoke test",
        "Git history secret scan",
        "Rollback tested",
        "User approved deployment",
    ]:
        assert text in checklist


def test_acceptance_script_is_local_and_non_destructive() -> None:
    script = Path("scripts/acceptance.sh").read_text(encoding="utf-8")
    assert "pytest" in script
    assert "gitleaks" in script
    assert "ugc-video doctor --full" in script
    assert "rm -rf /" not in script
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/release/test_release_gate.py -q`

Expected: failures because acceptance files do not exist.

- [ ] **Step 3: Create the deterministic acceptance command**

`scripts/acceptance.sh`:

```bash
#!/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ "$(uname -s)" == "Darwin" ]]; then
  WHISPER_EXTRA="mac-whisper"
elif grep -qi microsoft /proc/sys/kernel/osrelease; then
  WHISPER_EXTRA="wsl-whisper"
else
  echo "Acceptance supports Apple Silicon macOS and Windows 11/WSL2 only." >&2
  exit 64
fi
uv sync --frozen --extra dev --extra "$WHISPER_EXTRA"
uv run pytest -q
uv run ruff check .
uv run mypy src
gitleaks version >/dev/null
scripts/check-secrets.sh
bash -n setup-macos.sh scripts/*.sh START-HERE-MAC.command
uv run ugc-video doctor --full
uv run ugc-video demo --offline-fixtures
git diff --exit-code
test -z "$(git status --short)"
```

- [ ] **Step 4: Create the release checklist**

`docs/RELEASE-CHECKLIST.md`:

```markdown
# Release checklist

## Automated evidence

- [ ] Full pytest, Ruff, mypy, Bash, PowerShell, and Gitleaks checks pass.
- [ ] Git history secret scan passes.
- [ ] Offline demo fixture passes without cloud credentials.

## Supported machines

- [ ] Apple Silicon clean-machine installation and safe rerun pass.
- [ ] Windows 11/WSL2 clean-machine installation, reboot resume, and safe rerun pass.
- [ ] Three Whisper backends pass deep health on both targets.
- [ ] Uninstall removes only kit-owned files on both targets.

## Credentialed smoke tests

- [ ] Codex and Grok CLI login checks pass.
- [ ] Fish Audio primary smoke test generates the approved short sentence.
- [ ] ElevenLabs fallback smoke test generates the approved short sentence.
- [ ] Grok guided mode resumes from a downloaded clip.
- [ ] Grok API mode records a request ID and downloads the temporary result.
- [ ] Final demo passes pre-swap and post-swap dialogue checks.

## Documentation and rights

- [ ] Subscription claims are rechecked against official live pages.
- [ ] Demo asset provenance and fictional identity are recorded.
- [ ] Commercial-license and attribution warnings are visible.
- [ ] Unsupported-machine students are directed to contact the instructor.

## Rollback and deployment

- [ ] Previous tag remains available.
- [ ] Rollback tested by installing the previous tag and restoring backed-up configuration.
- [ ] User approved deployment.
```

- [ ] **Step 5: Create the initial changelog**

`CHANGELOG.md`:

```markdown
# Changelog

## 0.1.0 - Unreleased

- Add Apple Silicon and Windows 11/WSL2 guided installers.
- Add Codex and Grok CLI setup.
- Add three local Whisper health-checked fallbacks.
- Add Fish Audio primary voice with ElevenLabs fallback.
- Add resumable Grok animation, natural voice fitting, transcript QA, and vertical finishing.
- Add student documentation, secret scanning, and non-billable CI.
```

- [ ] **Step 6: Run GREEN and commit**

```bash
chmod +x scripts/acceptance.sh
uv run pytest tests/release/test_release_gate.py -q
git add scripts/acceptance.sh docs/RELEASE-CHECKLIST.md CHANGELOG.md tests/release/test_release_gate.py
git commit -m "docs: add release and rollback gates"
```

Expected: two tests pass.

### Task 8: Final integration review and deployment handoff

**Files:**
- Verify: all tracked repository files.
- No planned modifications. A failure returns work to the owning task and requires its test-first correction before this review restarts.

- [ ] **Step 1: Run the complete non-billable verification**

```bash
uv run pytest -q
uv run ruff check .
uv run mypy src
pre-commit run --all-files
scripts/check-secrets.sh
bash -n setup-macos.sh scripts/*.sh START-HERE-MAC.command
pwsh -NoProfile -File tests/platform/Test-WindowsScripts.ps1
uv run ugc-video demo --offline-fixtures
```

Expected: every command exits `0`.

- [ ] **Step 2: Review spec coverage**

Read `docs/superpowers/specs/2026-07-13-ugc-video-student-kit-design.md` section by section. Record the matching test, command, or documentation path beside every acceptance criterion in `docs/RELEASE-CHECKLIST.md`. If a criterion has no evidence, add the smallest failing test and implementation before continuing.

- [ ] **Step 3: Run the two supported clean-machine acceptance passes**

Follow `docs/RELEASE-CHECKLIST.md` on one clean Apple Silicon Mac and one clean Windows 11/WSL2 machine. Attach sanitized command summaries, installed versions, demo output hashes, and rollback results to the release candidate notes. Never attach keys, auth files, raw provider headers, or private student media.

- [ ] **Step 4: Present the deployment gate**

Report:

- What was built.
- Automated and clean-machine evidence.
- Fish, ElevenLabs, Grok, and Whisper smoke-test results.
- Current subscription claims and their verification date.
- Remaining risks or explicit waivers.
- Rollback command and previous tag.

Wait for explicit user deployment approval.

- [ ] **Step 5: Create the public repository only after approval**

Run:

```bash
gh repo create kofiowusuai-lab/ugc-video-student-kit --public --source . --remote origin --push
```

Expected: GitHub reports the new public repository and `git remote -v` shows the `origin` URL.

- [ ] **Step 6: Tag and publish the approved release**

Run:

```bash
git tag -a v0.1.0 -m "ugc-video-student-kit v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --verify-tag --generate-notes --title "UGC Video Student Kit v0.1.0"
```

Expected: the signed tag and public GitHub release exist, with CI attached to the tag.

- [ ] **Step 7: Verify public rollback artifacts**

Run:

```bash
gh release view v0.1.0
git ls-remote --tags origin v0.1.0
```

Expected: both commands resolve the same release tag and the previous source commit remains reachable.
