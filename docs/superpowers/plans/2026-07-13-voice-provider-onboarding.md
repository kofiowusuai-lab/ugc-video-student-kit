# Guided Voice Provider Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $subagent-driven-development (recommended) or $executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give students one safe setup command that stores Fish Audio and optional ElevenLabs keys, lists authorized voices by name, saves selections by number, preserves valid rerun state, and reports truthful provider readiness.

**Architecture:** Keep Typer responsible only for hidden credential prompts and exit propagation. Put the deterministic workflow in a new setup-wizard module with injected provider builders, health checks, input, and output so every branch is testable without network calls. Extend the existing voice-selection module to return structured lookup state while keeping secrets and provider IDs out of output.

**Tech Stack:** Python 3.11/3.12, Typer, Pydantic, httpx, ElevenLabs SDK, pytest, Ruff, mypy, uv, Gitleaks, Bash/PowerShell contract checks, Remotion TypeScript checks.

---

## Working rules

- Implement against the approved design in **docs/superpowers/specs/2026-07-13-voice-provider-onboarding-design.md**.
- Follow red-green-refactor for every behavior change. Run each stated RED command before editing production code and confirm it fails for the stated reason.
- Use only fake providers, temporary application homes, and synthetic key strings in automated tests. No test or CI job may contact Fish Audio, ElevenLabs, or xAI.
- Never print, snapshot, or commit API keys or full provider voice IDs.
- Preserve unrelated work in the tree.
- Do not push, tag, or publish v0.1.2 until the deployment gate in Task 6 receives explicit user approval.

## File map

- Create: **docs/VOICE-PROVIDER-SETUP.md**
- Create: **src/ugc_video/setup_wizard.py**
- Create: **tests/providers/test_voice_setup.py**
- Create: **tests/pipeline/test_setup_wizard.py**
- Modify: **README.md**
- Modify: **docs/SUBSCRIPTIONS.md**
- Modify: **docs/RELEASE-CHECKLIST.md**
- Modify: **src/ugc_video/cli.py**
- Modify: **src/ugc_video/providers/voice_setup.py**
- Modify: **src/ugc_video/providers/fish.py**
- Modify: **src/ugc_video/providers/elevenlabs.py**
- Modify: **tests/student/test_docs.py**
- Modify: **tests/providers/test_fish.py**
- Modify: **tests/providers/test_elevenlabs.py**
- Modify: **tests/pipeline/test_cli.py**
- Modify: **tests/foundation/test_package.py**
- Modify: **tests/release/test_release_gate.py**
- Modify: **src/ugc_video/__init__.py**
- Modify: **pyproject.toml**
- Modify mechanically with uv: **uv.lock**
- Modify: **CHANGELOG.md**

### Task 1: Add the child-simple provider guide and documentation contracts

**Files:**

- Create: **docs/VOICE-PROVIDER-SETUP.md**
- Modify: **README.md**
- Modify: **docs/SUBSCRIPTIONS.md**
- Modify: **tests/student/test_docs.py**

- [ ] **Step 1: Add failing guide-contract tests**

Append these tests to **tests/student/test_docs.py**:

~~~python
def test_readme_links_the_voice_provider_walkthrough() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "[Fish Audio and ElevenLabs setup](docs/VOICE-PROVIDER-SETUP.md)" in readme


def test_voice_provider_guide_is_complete_and_safe() -> None:
    guide = Path("docs/VOICE-PROVIDER-SETUP.md").read_text(encoding="utf-8")
    for text in [
        "Last verified: July 13, 2026",
        "https://fish.audio/app/api-keys/",
        "Bookmark",
        "Developers",
        "API Keys",
        "Text to Speech",
        "small credit limit",
        "uv run ugc-video setup",
        "Choose a voice number",
        "PASS Fish Audio",
        "SKIP ElevenLabs",
        "Library/Application Support/ugc-video/secrets.env",
        ".local/share/ugc-video/secrets.env",
        "Delete the exposed key",
        "create a replacement",
    ]:
        assert text in guide
    for unsafe_flag in ["--fish-key", "--elevenlabs-key", "--xai-key"]:
        assert unsafe_flag not in guide


def test_subscriptions_links_the_voice_provider_walkthrough() -> None:
    subscriptions = Path("docs/SUBSCRIPTIONS.md").read_text(encoding="utf-8")
    assert "[setup walkthrough](VOICE-PROVIDER-SETUP.md)" in subscriptions
~~~

- [ ] **Step 2: Run the documentation tests and confirm RED**

Run:

~~~bash
uv run pytest tests/student/test_docs.py -q
~~~

Expected: three new tests fail because the guide and links do not exist.

- [ ] **Step 3: Create the complete walkthrough**

Create **docs/VOICE-PROVIDER-SETUP.md** with this content:

~~~~markdown
# Set up Fish Audio and ElevenLabs voices

Last verified: July 13, 2026. Provider screens can change. Use the official links on this page if a button has moved.

## What you are setting up

Fish Audio makes the voice for your video. It is the primary voice service.

ElevenLabs is an optional backup. You may skip it.

You will make your own API keys on the provider websites. Then one command will store them safely, show your voice names, and let you choose by number. You will never need to find or type a voice ID.

Use only voices you own or have permission to use. Do not clone or imitate a real person without documented permission.

## Part 1: Make a Fish Audio key

1. Open [Fish Audio](https://fish.audio/).
2. Create an account or sign in.
3. Open the official [Fish Audio API Keys page](https://fish.audio/app/api-keys/).
4. Choose **Create API Key**.
5. Name the key **ugc-video-student-kit**.
6. Create the key.
7. Copy the key.
8. Keep this browser tab open until the terminal says **READY**.

**What you should see:** Fish Audio shows a new key that you can copy.

Do not paste the key into chat, a document, your code, or a screenshot.

## Part 2: Bookmark a Fish Audio voice

1. Open the Fish Audio voice library.
2. Choose a voice you are allowed to use.
3. Open that voice.
4. Choose **Bookmark**, or choose the bookmark or heart icon shown by Fish Audio.
5. Bookmark at least one voice.

**What you should see:** the voice is marked as saved or bookmarked in your Fish Audio account.

The setup command only shows your bookmarked Fish Audio voices. If you bookmark none, there is nothing to choose.

## Part 3: Make a safer ElevenLabs key

ElevenLabs is optional. Skip this part if you only want Fish Audio.

1. Open [ElevenLabs](https://elevenlabs.io/).
2. Create an account or sign in.
3. Open **Developers**.
4. Open **API Keys**.
5. Choose **Create API Key**.
6. Name the key **ugc-video-student-kit**.
7. Restrict the key to **Text to Speech**.
8. Set a small credit limit.
9. Create the key.
10. Copy the key now. ElevenLabs may show the full key only once.
11. Keep this browser tab open until the terminal says **READY**.

**What you should see:** ElevenLabs shows a new restricted key that you can copy.

See the official [ElevenLabs API-key guide](https://elevenlabs.io/docs/overview/administration/workspaces/api-keys) if the menu has moved.

## Part 4: Run one setup command

Open the repository folder in Terminal on a Mac, or open the repository folder inside WSL2 Ubuntu on Windows.

Run:

~~~bash
uv run ugc-video setup
~~~

The command asks for three keys:

1. Paste the Fish Audio key, then press **Enter**.
2. Paste the ElevenLabs key, then press **Enter**. Press **Enter** without typing anything if you are skipping ElevenLabs.
3. Paste an xAI API key, then press **Enter**. Press **Enter** without typing anything to use guided Grok.

Your typing is hidden. The screen may look blank while you paste a key. That is normal.

**What you should see:** the command starts loading voice names. It never prints any key back to you.

## Part 5: Pick voices by number

The command prints names like this:

~~~text
Fish Audio bookmarked voices:
1. Warm Narrator
2. Friendly Guide
Choose a voice number:
~~~

Type the number beside the voice you want. Then press **Enter**.

If ElevenLabs is configured, choose its fallback voice the same way.

On a later setup run, press **Enter** at a voice question to keep the saved choice. The command shows the saved voice name, never its private ID.

**What you should see:** your chosen names remain visible and no long voice IDs appear.

## Part 6: Check that it worked

A Fish-only setup ends like this:

~~~text
PASS Fish Audio: key accepted; voice selected
SKIP ElevenLabs: optional fallback was not configured
SKIP xAI API: guided Grok mode will be used
READY Voice setup is complete
~~~

A setup with the fallback ends like this:

~~~text
PASS Fish Audio: key accepted; voice selected
PASS ElevenLabs: key accepted; fallback voice selected
SKIP xAI API: guided Grok mode will be used
READY Voice setup is complete
~~~

Then run:

~~~bash
uv run ugc-video doctor --full
~~~

## If you see FAIL

Read the one action printed after **FAIL**.

- **Fish Audio key was not accepted:** create a replacement key and run setup again.
- **No bookmarked Fish Audio voices:** bookmark a voice and run setup again.
- **Fish Audio could not be reached:** wait a few minutes and run setup again.
- **ElevenLabs key was not accepted:** create a replacement key and run setup again.
- **No ElevenLabs voices:** add a voice and run setup again.
- **Wrong voice number:** enter one of the numbers shown. The command stops after three wrong tries.

A failed rerun does not erase a saved key or saved voice choice.

## Keep your keys safe

The command stores keys outside this Git repository:

- macOS: **~/Library/Application Support/ugc-video/secrets.env**
- WSL2 Ubuntu: **~/.local/share/ugc-video/secrets.env**

Voice choices go in **config.toml** in the same private application folder. Do not edit either file by hand.

Never put a key in:

- a Codex or Grok prompt;
- Git or GitHub;
- a screenshot or screen recording;
- course chat, email, or shared documents;
- source code or project files.

If a key is exposed:

1. Delete the exposed key on the provider website.
2. Choose **Create API Key** and create a replacement.
3. Run **uv run ugc-video setup** again.
4. Paste the replacement into the hidden prompt.

Fish Audio also documents [API-key safety in its quick start](https://docs.fish.audio/developer-guide/getting-started/quickstart). Read [Accounts, subscriptions, and usage](SUBSCRIPTIONS.md) before publishing commercial work.
~~~~

- [ ] **Step 4: Add the short entry-point links**

In **README.md**, add this sentence immediately below the Configure your own accounts heading and before the command block:

~~~markdown
Follow the [Fish Audio and ElevenLabs setup](docs/VOICE-PROVIDER-SETUP.md) walkthrough to create restricted keys, choose voices by name, and store everything safely.
~~~

In **docs/SUBSCRIPTIONS.md**, add this sentence after the paragraph explaining that ElevenLabs is optional:

~~~markdown
Use the [setup walkthrough](VOICE-PROVIDER-SETUP.md) to create restricted personal keys and choose authorized voices without copying provider IDs.
~~~

- [ ] **Step 5: Run the documentation tests and confirm GREEN**

Run:

~~~bash
uv run pytest tests/student/test_docs.py -q
~~~

Expected: all documentation contract tests pass.

- [ ] **Step 6: Commit the documentation increment**

Run:

~~~bash
git add README.md docs/VOICE-PROVIDER-SETUP.md docs/SUBSCRIPTIONS.md tests/student/test_docs.py
git diff --cached --check
git commit -m "docs: add guided voice provider setup"
~~~

Expected: one documentation-only commit; no API key examples or provider IDs are staged.

### Task 2: Make provider lookup and voice choice state explicit

**Files:**

- Create: **tests/providers/test_voice_setup.py**
- Modify: **tests/providers/test_fish.py**
- Modify: **tests/providers/test_elevenlabs.py**
- Modify: **src/ugc_video/providers/voice_setup.py**
- Modify: **src/ugc_video/providers/fish.py**
- Modify: **src/ugc_video/providers/elevenlabs.py**

- [ ] **Step 1: Add failing voice-selection tests**

Create **tests/providers/test_voice_setup.py**:

~~~python
from ugc_video.config import AppConfig
from ugc_video.domain import FailureKind
from ugc_video.providers.base import ProviderError
from ugc_video.providers.voice_setup import choose_voice, configure_voice_ids


class FakeVoiceProvider:
    def __init__(
        self,
        voices: dict[str, str] | None = None,
        failure: ProviderError | None = None,
    ) -> None:
        self.voices = voices or {}
        self.failure = failure

    def list_voices(self) -> dict[str, str]:
        if self.failure:
            raise self.failure
        return self.voices


def test_blank_choice_keeps_saved_voice_without_exposing_its_id() -> None:
    output: list[str] = []
    chosen = choose_voice(
        "Fish Audio bookmarked",
        {"fish-private-id": "Warm Narrator"},
        input_fn=lambda _: "",
        output_fn=output.append,
        current_id="fish-private-id",
    )
    rendered = "\n".join(output)
    assert chosen == "fish-private-id"
    assert "Current choice: Warm Narrator" in rendered
    assert "fish-private-id" not in rendered


def test_configure_voice_ids_returns_selection_readiness() -> None:
    answers = iter(["2", "1"])
    result = configure_voice_ids(
        AppConfig(),
        FakeVoiceProvider({"fish-a": "Calm", "fish-b": "Warm"}),
        FakeVoiceProvider({"eleven-a": "Clear"}),
        fish_configured=True,
        elevenlabs_configured=True,
        input_fn=lambda _: next(answers),
        output_fn=lambda _: None,
    )
    assert result.config.fish_voice_id == "fish-b"
    assert result.config.elevenlabs_voice_id == "eleven-a"
    assert result.fish.selected_is_available is True
    assert result.elevenlabs.selected_is_available is True


def test_lookup_failure_preserves_existing_choice_and_kind() -> None:
    existing = AppConfig(fish_voice_id="saved-fish")
    result = configure_voice_ids(
        existing,
        FakeVoiceProvider(
            failure=ProviderError(FailureKind.TRANSIENT, "private network detail")
        ),
        FakeVoiceProvider(),
        fish_configured=True,
        elevenlabs_configured=False,
        input_fn=lambda _: "",
        output_fn=lambda _: None,
    )
    assert result.config.fish_voice_id == "saved-fish"
    assert result.fish.failure == FailureKind.TRANSIENT
    assert result.fish.selected_is_available is False
~~~

- [ ] **Step 2: Add failing provider error-normalization tests**

Append to **tests/providers/test_fish.py**:

~~~python
@respx.mock
def test_voice_lookup_normalizes_network_failure() -> None:
    respx.get("https://api.fish.audio/model").mock(
        side_effect=httpx.ConnectError("private endpoint detail")
    )
    provider = FishAudioProvider("secret")
    with pytest.raises(ProviderError) as captured:
        provider.list_voices()
    assert captured.value.kind == FailureKind.TRANSIENT
    assert "private endpoint detail" not in str(captured.value)
~~~

Update the import block at the top of **tests/providers/test_elevenlabs.py** to include pytest and the
error types:

~~~python
from pathlib import Path
from types import SimpleNamespace

import pytest

from ugc_video.domain import FailureKind, VoiceRequest
from ugc_video.providers.base import ProviderError
from ugc_video.providers.elevenlabs import ElevenLabsProvider
~~~

Then append:

~~~python


class FailingVoiceClient:
    def __init__(self, error: Exception) -> None:
        self.voices = SimpleNamespace(get_all=lambda: (_ for _ in ()).throw(error))


@pytest.mark.parametrize(
    ("error", "expected_kind"),
    [
        (RuntimeError("401 unauthorized"), FailureKind.AUTHENTICATION),
        (TimeoutError("private endpoint detail"), FailureKind.TRANSIENT),
    ],
)
def test_voice_lookup_normalizes_sdk_failures(
    error: Exception, expected_kind: FailureKind
) -> None:
    provider = ElevenLabsProvider("secret", client=FailingVoiceClient(error))
    with pytest.raises(ProviderError) as captured:
        provider.list_voices()
    assert captured.value.kind == expected_kind
    assert "private endpoint detail" not in str(captured.value)
~~~

- [ ] **Step 3: Run the focused tests and confirm RED**

Run:

~~~bash
uv run pytest tests/providers/test_voice_setup.py tests/providers/test_fish.py tests/providers/test_elevenlabs.py -q
~~~

Expected: failures identify the missing structured result, saved-choice behavior, and transient error normalization.

- [ ] **Step 4: Implement structured voice selection**

Replace **src/ugc_video/providers/voice_setup.py** with:

~~~python
from collections.abc import Callable
from dataclasses import dataclass

from ugc_video.config import AppConfig
from ugc_video.domain import FailureKind
from ugc_video.providers.base import ProviderError, VoiceProvider


@dataclass(frozen=True)
class ProviderVoiceSelection:
    configured: bool
    selected_id: str
    voice_count: int
    selected_is_available: bool
    failure: FailureKind | None = None


@dataclass(frozen=True)
class VoiceSetupResult:
    config: AppConfig
    fish: ProviderVoiceSelection
    elevenlabs: ProviderVoiceSelection


def choose_voice(
    label: str,
    voices: dict[str, str],
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    current_id: str = "",
) -> str:
    if not voices:
        return current_id
    ordered = sorted(voices.items(), key=lambda item: (item[1].casefold(), item[0]))
    output_fn(f"{label} voices:")
    for index, (_, title) in enumerate(ordered, start=1):
        output_fn(f"{index}. {title}")
    if current_id:
        current_title = voices.get(current_id)
        if current_title:
            output_fn(f"Current choice: {current_title}")
        else:
            output_fn("A saved choice is no longer available.")
    prompt = (
        "Choose a voice number, or press Enter to keep the saved choice: "
        if current_id
        else "Choose a voice number: "
    )
    for _ in range(3):
        raw = input_fn(prompt).strip()
        if not raw and current_id:
            return current_id
        if raw.isdigit() and 1 <= int(raw) <= len(ordered):
            return ordered[int(raw) - 1][0]
        output_fn("Enter one of the displayed voice numbers.")
    raise ValueError(f"Too many invalid {label} voice selections")


def _select_provider_voice(
    label: str,
    current_id: str,
    provider: VoiceProvider,
    configured: bool,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> ProviderVoiceSelection:
    if not configured:
        return ProviderVoiceSelection(False, current_id, 0, False)
    try:
        voices = provider.list_voices()
    except ProviderError as exc:
        return ProviderVoiceSelection(True, current_id, 0, False, exc.kind)
    if not voices:
        return ProviderVoiceSelection(True, current_id, 0, False)
    selected_id = choose_voice(
        label,
        voices,
        input_fn=input_fn,
        output_fn=output_fn,
        current_id=current_id,
    )
    return ProviderVoiceSelection(
        configured=True,
        selected_id=selected_id,
        voice_count=len(voices),
        selected_is_available=selected_id in voices,
    )


def configure_voice_ids(
    config: AppConfig,
    fish: VoiceProvider,
    elevenlabs: VoiceProvider,
    fish_configured: bool,
    elevenlabs_configured: bool,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> VoiceSetupResult:
    fish_selection = _select_provider_voice(
        "Fish Audio bookmarked",
        config.fish_voice_id,
        fish,
        fish_configured,
        input_fn,
        output_fn,
    )
    elevenlabs_selection = _select_provider_voice(
        "ElevenLabs",
        config.elevenlabs_voice_id,
        elevenlabs,
        elevenlabs_configured,
        input_fn,
        output_fn,
    )
    updated = config.model_copy(
        update={
            "fish_voice_id": fish_selection.selected_id,
            "elevenlabs_voice_id": elevenlabs_selection.selected_id,
        }
    )
    return VoiceSetupResult(updated, fish_selection, elevenlabs_selection)
~~~

- [ ] **Step 5: Normalize Fish Audio transport failures**

In **FishAudioProvider.bookmarked_voices** in **src/ugc_video/providers/fish.py**, wrap the GET:

~~~python
            try:
                response = self.client.get(
                    f"{self.base_url}/model",
                    params={"page_size": 100, "page_number": page},
                    headers=self.headers,
                )
            except httpx.HTTPError as exc:
                raise ProviderError(
                    FailureKind.TRANSIENT, "Fish Audio voice lookup failed"
                ) from exc
~~~

Keep the existing HTTP status mapping and pagination logic immediately after this block.

- [ ] **Step 6: Distinguish ElevenLabs authentication from transport failures**

Add this helper near the top of **src/ugc_video/providers/elevenlabs.py**:

~~~python
def _failure_kind(error: Exception) -> FailureKind:
    message = f"{type(error).__name__}: {error}".lower()
    if any(marker in message for marker in ("401", "403", "unauthorized", "forbidden")):
        return FailureKind.AUTHENTICATION
    if "quota" in message or "credit" in message:
        return FailureKind.QUOTA
    if "policy" in message:
        return FailureKind.POLICY
    return FailureKind.TRANSIENT
~~~

Change the list-voices exception branch to:

~~~python
        except Exception as exc:
            raise ProviderError(
                _failure_kind(exc), "ElevenLabs voice lookup failed"
            ) from exc
~~~

Change the synthesize exception branch to use the same helper:

~~~python
        except Exception as exc:
            raise ProviderError(
                _failure_kind(exc),
                f"ElevenLabs generation failed: {type(exc).__name__}",
            ) from exc
~~~

- [ ] **Step 7: Run focused tests, Ruff, and mypy**

Run:

~~~bash
uv run pytest tests/providers/test_voice_setup.py tests/providers/test_fish.py tests/providers/test_elevenlabs.py tests/pipeline/test_cli.py -q
uv run ruff check src/ugc_video/providers tests/providers tests/pipeline/test_cli.py
uv run mypy src
~~~

Expected: all commands pass; no test makes a live provider request.

- [ ] **Step 8: Commit the provider-selection increment**

Run:

~~~bash
git add src/ugc_video/providers/voice_setup.py src/ugc_video/providers/fish.py src/ugc_video/providers/elevenlabs.py tests/providers/test_voice_setup.py tests/providers/test_fish.py tests/providers/test_elevenlabs.py
git diff --cached --check
git commit -m "feat: add safe provider voice selection"
~~~

### Task 3: Build the safe, injectable setup wizard

**Files:**

- Create: **tests/pipeline/test_setup_wizard.py**
- Create: **src/ugc_video/setup_wizard.py**

- [ ] **Step 1: Add failing happy-path and optional-provider tests**

Create **tests/pipeline/test_setup_wizard.py** with these imports, fakes, and initial tests:

~~~python
import os
import stat
from pathlib import Path

import pytest

from ugc_video.config import AppConfig, load_config, save_config
from ugc_video.domain import FailureKind, ProviderHealth
from ugc_video.paths import AppPaths
from ugc_video.providers.base import ProviderError
from ugc_video.secrets import read_secrets, write_secret
from ugc_video.setup_wizard import run_setup_wizard


class FakeVoiceProvider:
    def __init__(
        self,
        voices: dict[str, str] | None = None,
        failure: ProviderError | None = None,
    ) -> None:
        self.voices = voices or {}
        self.failure = failure

    def list_voices(self) -> dict[str, str]:
        if self.failure:
            raise self.failure
        return self.voices


def healthy(_: dict[str, str], name: str) -> ProviderHealth:
    return ProviderHealth(provider=name, ok=True, detail="available")


def test_success_stores_keys_selects_ids_and_prints_names_only(tmp_path: Path) -> None:
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path / "home")})
    answers = iter(["2", "1"])
    output: list[str] = []
    exit_code = run_setup_wizard(
        paths,
        fish_key="fish-example-value",
        elevenlabs_key="eleven-example-value",
        xai_key="",
        provider_builder=lambda _: (
            FakeVoiceProvider({"fish-private-a": "Calm", "fish-private-b": "Warm"}),
            FakeVoiceProvider({"eleven-private-a": "Clear"}),
        ),
        health_checker=healthy,
        input_fn=lambda _: next(answers),
        output_fn=output.append,
    )
    rendered = "\n".join(output)
    assert exit_code == 0
    assert read_secrets(paths.secrets) == {
        "ELEVENLABS_API_KEY": "eleven-example-value",
        "FISH_AUDIO_API_KEY": "fish-example-value",
    }
    config = load_config(paths.config)
    assert config.fish_voice_id == "fish-private-b"
    assert config.elevenlabs_voice_id == "eleven-private-a"
    assert "2. Warm" in rendered
    assert "1. Clear" in rendered
    assert "PASS Fish Audio: key accepted; voice selected" in rendered
    assert "PASS ElevenLabs: key accepted; fallback voice selected" in rendered
    assert "SKIP xAI API: guided Grok mode will be used" in rendered
    assert "READY Voice setup is complete" in rendered
    for private_value in [
        "fish-example-value",
        "eleven-example-value",
        "fish-private-a",
        "fish-private-b",
        "eleven-private-a",
    ]:
        assert private_value not in rendered
    if os.name != "nt":
        assert stat.S_IMODE(paths.secrets.stat().st_mode) == 0o600


def test_blank_elevenlabs_key_is_an_explicit_optional_skip(tmp_path: Path) -> None:
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path / "home")})
    output: list[str] = []
    exit_code = run_setup_wizard(
        paths,
        fish_key="fish-example-value",
        elevenlabs_key="",
        xai_key="",
        provider_builder=lambda _: (
            FakeVoiceProvider({"fish-private": "Warm"}),
            FakeVoiceProvider(),
        ),
        health_checker=healthy,
        input_fn=lambda _: "1",
        output_fn=output.append,
    )
    rendered = "\n".join(output)
    assert exit_code == 0
    assert "SKIP ElevenLabs: optional fallback was not configured" in rendered
    assert "READY Voice setup is complete" in rendered
~~~

- [ ] **Step 2: Add failing recovery and idempotence tests**

Append to **tests/pipeline/test_setup_wizard.py**:

~~~python
@pytest.mark.parametrize(
    ("provider", "expected_message"),
    [
        (
            FakeVoiceProvider(
                failure=ProviderError(FailureKind.AUTHENTICATION, "private auth detail")
            ),
            "FAIL Fish Audio: key was not accepted; create a replacement key and rerun setup",
        ),
        (
            FakeVoiceProvider(),
            "FAIL Fish Audio: no bookmarked voices found; bookmark a voice and rerun setup",
        ),
        (
            FakeVoiceProvider(
                failure=ProviderError(FailureKind.TRANSIENT, "private endpoint detail")
            ),
            "FAIL Fish Audio: service could not be reached; wait and rerun setup",
        ),
    ],
)
def test_fish_failure_is_actionable_and_preserves_existing_state(
    tmp_path: Path,
    provider: FakeVoiceProvider,
    expected_message: str,
) -> None:
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path / "home")})
    write_secret(paths.secrets, "FISH_AUDIO_API_KEY", "saved-example-value")
    save_config(paths.config, AppConfig(fish_voice_id="saved-private-id"))
    output: list[str] = []
    exit_code = run_setup_wizard(
        paths,
        fish_key="",
        elevenlabs_key="",
        xai_key="",
        provider_builder=lambda _: (provider, FakeVoiceProvider()),
        health_checker=healthy,
        input_fn=lambda _: "",
        output_fn=output.append,
    )
    rendered = "\n".join(output)
    assert exit_code == 2
    assert expected_message in rendered
    assert "NOT READY Voice setup needs attention" in rendered
    assert "private auth detail" not in rendered
    assert "private endpoint detail" not in rendered
    assert "saved-example-value" not in rendered
    assert "saved-private-id" not in rendered
    assert read_secrets(paths.secrets)["FISH_AUDIO_API_KEY"] == "saved-example-value"
    assert load_config(paths.config).fish_voice_id == "saved-private-id"


def test_blank_rerun_preserves_keys_and_voice_choices(tmp_path: Path) -> None:
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path / "home")})
    write_secret(paths.secrets, "FISH_AUDIO_API_KEY", "saved-fish-value")
    write_secret(paths.secrets, "ELEVENLABS_API_KEY", "saved-eleven-value")
    save_config(
        paths.config,
        AppConfig(
            fish_voice_id="saved-fish-id",
            elevenlabs_voice_id="saved-eleven-id",
        ),
    )
    answers = iter(["", ""])
    output: list[str] = []
    exit_code = run_setup_wizard(
        paths,
        fish_key="",
        elevenlabs_key="",
        xai_key="",
        provider_builder=lambda _: (
            FakeVoiceProvider({"saved-fish-id": "Warm"}),
            FakeVoiceProvider({"saved-eleven-id": "Clear"}),
        ),
        health_checker=healthy,
        input_fn=lambda _: next(answers),
        output_fn=output.append,
    )
    assert exit_code == 0
    assert read_secrets(paths.secrets) == {
        "ELEVENLABS_API_KEY": "saved-eleven-value",
        "FISH_AUDIO_API_KEY": "saved-fish-value",
    }
    config = load_config(paths.config)
    assert config.fish_voice_id == "saved-fish-id"
    assert config.elevenlabs_voice_id == "saved-eleven-id"
    rendered = "\n".join(output)
    assert "Current choice: Warm" in rendered
    assert "Current choice: Clear" in rendered
    assert "saved-fish-id" not in rendered
    assert "saved-eleven-id" not in rendered


def test_three_invalid_voice_choices_exit_two_without_replacing_config(
    tmp_path: Path,
) -> None:
    paths = AppPaths.from_environment({"UGC_VIDEO_HOME": str(tmp_path / "home")})
    write_secret(paths.secrets, "FISH_AUDIO_API_KEY", "saved-fish-value")
    save_config(paths.config, AppConfig(fish_voice_id="saved-fish-id"))
    answers = iter(["9", "word", "0"])
    output: list[str] = []
    exit_code = run_setup_wizard(
        paths,
        fish_key="",
        elevenlabs_key="",
        xai_key="",
        provider_builder=lambda _: (
            FakeVoiceProvider({"new-private-id": "New Voice"}),
            FakeVoiceProvider(),
        ),
        health_checker=healthy,
        input_fn=lambda _: next(answers),
        output_fn=output.append,
    )
    assert exit_code == 2
    assert load_config(paths.config).fish_voice_id == "saved-fish-id"
    assert "\n".join(output).count("Enter one of the displayed voice numbers.") == 3
    assert "FAIL Voice selection: too many invalid choices; rerun setup" in "\n".join(output)
~~~

- [ ] **Step 3: Run the wizard tests and confirm RED**

Run:

~~~bash
uv run pytest tests/pipeline/test_setup_wizard.py -q
~~~

Expected: collection fails because **ugc_video.setup_wizard** does not exist.

- [ ] **Step 4: Implement the complete workflow module**

Create **src/ugc_video/setup_wizard.py**:

~~~python
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ugc_video.config import load_config, save_config
from ugc_video.domain import FailureKind, ProviderHealth
from ugc_video.paths import AppPaths
from ugc_video.pipeline.services import build_voice_providers, provider_health
from ugc_video.providers.base import VoiceProvider
from ugc_video.providers.voice_setup import (
    ProviderVoiceSelection,
    configure_voice_ids,
)
from ugc_video.secrets import read_secrets, write_secret

ProviderBuilder = Callable[[dict[str, str]], tuple[VoiceProvider, VoiceProvider]]
HealthChecker = Callable[[dict[str, str], str], ProviderHealth]
InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]
StatusState = Literal["PASS", "SKIP", "FAIL"]


@dataclass(frozen=True)
class SetupStatus:
    state: StatusState
    provider: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.state != "FAIL"

    def render(self) -> str:
        return f"{self.state} {self.provider}: {self.detail}"


def _selection_failure_detail(
    provider_name: str,
    selection: ProviderVoiceSelection,
) -> str:
    if selection.failure == FailureKind.AUTHENTICATION:
        return "key was not accepted; create a replacement key and rerun setup"
    if selection.failure in {FailureKind.TRANSIENT, FailureKind.RATE_LIMIT}:
        return "service could not be reached; wait and rerun setup"
    if selection.failure == FailureKind.QUOTA:
        return "account has no available quota; check the provider plan and rerun setup"
    if selection.failure is not None:
        return "voice list could not be loaded; check the provider account and rerun setup"
    if selection.voice_count == 0:
        if provider_name == "fish":
            return "no bookmarked voices found; bookmark a voice and rerun setup"
        return "no available voices found; add a voice and rerun setup"
    return "saved voice is no longer available; choose a displayed voice and rerun setup"


def _checked_health(
    checker: HealthChecker,
    secrets: dict[str, str],
    provider_name: str,
) -> ProviderHealth:
    try:
        return checker(secrets, provider_name)
    except Exception:
        return ProviderHealth(
            provider=provider_name,
            ok=False,
            detail="provider readiness check unavailable",
        )


def _health_failure_detail(health: ProviderHealth) -> str:
    detail = health.detail.lower()
    if any(marker in detail for marker in ("401", "403", "auth", "permission")):
        return "key was not accepted; create a replacement key and rerun setup"
    if "quota" in detail or "credit" in detail:
        return "account has no available quota; check the provider plan and rerun setup"
    return "service could not be reached; wait and rerun setup"


def _voice_status(
    label: str,
    provider_name: str,
    secret_name: str,
    required: bool,
    pass_detail: str,
    secrets: dict[str, str],
    selection: ProviderVoiceSelection,
    checker: HealthChecker,
) -> SetupStatus:
    if not secrets.get(secret_name):
        if required:
            return SetupStatus(
                "FAIL",
                label,
                "API key is required; create a key and rerun setup",
            )
        return SetupStatus("SKIP", label, "optional fallback was not configured")
    if selection.failure is not None:
        return SetupStatus(
            "FAIL",
            label,
            _selection_failure_detail(provider_name, selection),
        )
    if selection.voice_count == 0 or not selection.selected_is_available:
        return SetupStatus(
            "FAIL",
            label,
            _selection_failure_detail(provider_name, selection),
        )
    health = _checked_health(checker, secrets, provider_name)
    if not health.ok:
        return SetupStatus("FAIL", label, _health_failure_detail(health))
    return SetupStatus("PASS", label, pass_detail)


def _grok_status(
    secrets: dict[str, str],
    checker: HealthChecker,
) -> SetupStatus:
    if not secrets.get("XAI_API_KEY"):
        return SetupStatus("SKIP", "xAI API", "guided Grok mode will be used")
    health = _checked_health(checker, secrets, "grok")
    if health.ok:
        return SetupStatus("PASS", "xAI API", "automatic Grok mode is configured")
    return SetupStatus(
        "FAIL",
        "xAI API",
        "key check failed; replace the key or leave it blank for guided Grok",
    )


def run_setup_wizard(
    paths: AppPaths,
    fish_key: str,
    elevenlabs_key: str,
    xai_key: str,
    provider_builder: ProviderBuilder | None = None,
    health_checker: HealthChecker | None = None,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> int:
    for name, value in (
        ("FISH_AUDIO_API_KEY", fish_key),
        ("ELEVENLABS_API_KEY", elevenlabs_key),
        ("XAI_API_KEY", xai_key),
    ):
        if value:
            write_secret(paths.secrets, name, value)

    secrets = read_secrets(paths.secrets)
    config = load_config(paths.config)
    builder = provider_builder or build_voice_providers
    checker = health_checker or provider_health
    fish, elevenlabs = builder(secrets)

    try:
        voice_setup = configure_voice_ids(
            config,
            fish,
            elevenlabs,
            fish_configured=bool(secrets.get("FISH_AUDIO_API_KEY")),
            elevenlabs_configured=bool(secrets.get("ELEVENLABS_API_KEY")),
            input_fn=input_fn,
            output_fn=output_fn,
        )
    except ValueError:
        output_fn("FAIL Voice selection: too many invalid choices; rerun setup")
        output_fn("NOT READY Voice setup needs attention")
        return 2

    save_config(paths.config, voice_setup.config)
    output_fn(f"Local configuration saved under: {paths.root}")
    statuses = [
        _voice_status(
            "Fish Audio",
            "fish",
            "FISH_AUDIO_API_KEY",
            True,
            "key accepted; voice selected",
            secrets,
            voice_setup.fish,
            checker,
        ),
        _voice_status(
            "ElevenLabs",
            "elevenlabs",
            "ELEVENLABS_API_KEY",
            False,
            "key accepted; fallback voice selected",
            secrets,
            voice_setup.elevenlabs,
            checker,
        ),
        _grok_status(secrets, checker),
    ]
    for status in statuses:
        output_fn(status.render())
    if all(status.ok for status in statuses):
        output_fn("READY Voice setup is complete")
        return 0
    output_fn("NOT READY Voice setup needs attention")
    return 2
~~~

- [ ] **Step 5: Run the wizard suite and confirm GREEN**

Run:

~~~bash
uv run pytest tests/pipeline/test_setup_wizard.py tests/providers/test_voice_setup.py -q
uv run ruff check src/ugc_video/setup_wizard.py tests/pipeline/test_setup_wizard.py
uv run mypy src
~~~

Expected: the happy path, Fish-only path, bounded invalid input, failure mapping, mode 0600, redaction, and safe rerun tests all pass.

- [ ] **Step 6: Commit the workflow increment**

Run:

~~~bash
git add src/ugc_video/setup_wizard.py tests/pipeline/test_setup_wizard.py
git diff --cached --check
git commit -m "feat: add completed voice setup wizard"
~~~

### Task 4: Wire the hidden Typer prompts to the wizard

**Files:**

- Modify: **tests/pipeline/test_cli.py**
- Modify: **src/ugc_video/cli.py**

- [ ] **Step 1: Replace the credential-only CLI test with a full command test**

Add **from ugc_video.config import load_config** to **tests/pipeline/test_cli.py**, then add this fake
near the top:

~~~python
class FakeSetupVoiceProvider:
    def __init__(self, voices: dict[str, str]) -> None:
        self.voices = voices

    def list_voices(self) -> dict[str, str]:
        return self.voices
~~~

Replace **test_setup_saves_keys_only_in_local_secret_file** with:

~~~python
def test_setup_command_runs_full_wizard_without_exposing_private_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("UGC_VIDEO_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(
        "ugc_video.setup_wizard.build_voice_providers",
        lambda _: (
            FakeSetupVoiceProvider({"fish-private-id": "Warm Narrator"}),
            FakeSetupVoiceProvider({"eleven-private-id": "Clear Guide"}),
        ),
    )
    monkeypatch.setattr(
        "ugc_video.setup_wizard.provider_health",
        lambda _, name: ProviderHealth(provider=name, ok=True, detail="available"),
    )
    result = CliRunner().invoke(
        app,
        [
            "setup",
            "--fish-key",
            "fish-example-value",
            "--elevenlabs-key",
            "eleven-example-value",
            "--xai-key",
            "",
        ],
        input="1\n1\n",
    )
    assert result.exit_code == 0
    values = read_secrets(tmp_path / "home/secrets.env")
    assert set(values) == {"FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY"}
    config = load_config(tmp_path / "home/config.toml")
    assert config.fish_voice_id == "fish-private-id"
    assert config.elevenlabs_voice_id == "eleven-private-id"
    assert "Warm Narrator" in result.stdout
    assert "Clear Guide" in result.stdout
    assert "READY Voice setup is complete" in result.stdout
    for private_value in [
        "fish-example-value",
        "eleven-example-value",
        "fish-private-id",
        "eleven-private-id",
    ]:
        assert private_value not in result.stdout


def test_setup_help_does_not_advertise_command_line_key_values() -> None:
    result = CliRunner().invoke(app, ["setup", "--help"])
    assert result.exit_code == 0
    for unsafe_flag in ["--fish-key", "--elevenlabs-key", "--xai-key"]:
        assert unsafe_flag not in result.stdout
~~~

- [ ] **Step 2: Run the CLI test and confirm RED**

Run:

~~~bash
uv run pytest tests/pipeline/test_cli.py -q
~~~

Expected: the new test fails because the command saves credentials but does not list or persist voice selections.

- [ ] **Step 3: Delegate setup behavior from the CLI**

In **src/ugc_video/cli.py**:

1. Change the config import to **from ugc_video.config import load_config**.
2. Keep **from ugc_video.pipeline.services import build_services, provider_health** because the run
   and doctor commands still use those functions.
3. Change the secrets import to **from ugc_video.secrets import read_secrets**.
4. Add **from ugc_video.setup_wizard import run_setup_wizard**.
5. Replace the setup function with the code below.

Use these prompt labels and body:

~~~python
@app.command()
def setup(
    fish_key: str = typer.Option(
        "",
        "--fish-key",
        prompt="Fish Audio API key (blank keeps a saved key)",
        hide_input=True,
        hidden=True,
        show_default=False,
    ),
    elevenlabs_key: str = typer.Option(
        "",
        "--elevenlabs-key",
        prompt="ElevenLabs API key (optional; blank keeps a saved key)",
        hide_input=True,
        hidden=True,
        show_default=False,
    ),
    xai_key: str = typer.Option(
        "",
        "--xai-key",
        prompt="xAI API key (optional; blank uses guided Grok)",
        hide_input=True,
        hidden=True,
        show_default=False,
    ),
) -> None:
    paths = AppPaths.from_environment(os.environ)
    exit_code = run_setup_wizard(
        paths,
        fish_key=fish_key,
        elevenlabs_key=elevenlabs_key,
        xai_key=xai_key,
        output_fn=typer.echo,
    )
    if exit_code:
        raise typer.Exit(exit_code)
~~~

The flags remain for backward compatibility and automated tests, but no student documentation may recommend putting keys on the command line.

- [ ] **Step 4: Run CLI, wizard, doctor, and secret-storage tests**

Run:

~~~bash
uv run pytest tests/pipeline/test_cli.py tests/pipeline/test_setup_wizard.py tests/foundation/test_secrets.py tests/foundation/test_doctor_cli.py -q
uv run ruff check src/ugc_video/cli.py src/ugc_video/setup_wizard.py tests/pipeline
uv run mypy src
~~~

Expected: all commands pass, including exit code 2 for incomplete setup and zero for Fish-only or Fish-plus-ElevenLabs readiness.

- [ ] **Step 5: Commit the CLI integration**

Run:

~~~bash
git add src/ugc_video/cli.py tests/pipeline/test_cli.py
git diff --cached --check
git commit -m "feat: connect setup command to voice wizard"
~~~

### Task 5: Prepare v0.1.2 metadata and release evidence

**Files:**

- Modify: **tests/foundation/test_package.py**
- Modify: **tests/release/test_release_gate.py**
- Modify: **src/ugc_video/__init__.py**
- Modify: **pyproject.toml**
- Modify mechanically: **uv.lock**
- Modify: **CHANGELOG.md**
- Modify: **docs/RELEASE-CHECKLIST.md**

- [ ] **Step 1: Make the version and release-checklist expectations fail first**

In **tests/foundation/test_package.py**, change both expected version strings from **0.1.1** to **0.1.2**.

Append to **tests/release/test_release_gate.py**:

~~~python
def test_release_checklist_covers_the_completed_voice_wizard() -> None:
    checklist = Path("docs/RELEASE-CHECKLIST.md").read_text(encoding="utf-8")
    for text in [
        "Voice setup wizard fake-provider tests",
        "hidden prompts and safe rerun",
        "lists bookmarked voice names",
        "lists available fallback voice names",
        "User approved deployment of v0.1.2",
    ]:
        assert text in checklist
~~~

Run:

~~~bash
uv run pytest tests/foundation/test_package.py tests/release/test_release_gate.py -q
~~~

Expected: failures show the package is still 0.1.1 and the release checklist lacks the new evidence.

- [ ] **Step 2: Update package metadata to 0.1.2**

Set:

~~~python
# src/ugc_video/__init__.py
__version__ = "0.1.2"
~~~

Set the project version in **pyproject.toml**:

~~~toml
version = "0.1.2"
~~~

Regenerate only the lockfile metadata:

~~~bash
uv lock
~~~

Verify:

~~~bash
rg -n '0\.1\.[0-9]+' src/ugc_video/__init__.py pyproject.toml uv.lock tests/foundation/test_package.py
~~~

Expected: the package entry, lockfile root package, CLI test, and Python module all agree on 0.1.2; dependency versions change only if uv requires a compatible lock refresh.

- [ ] **Step 3: Add the v0.1.2 changelog entry**

Insert this section at the top of **CHANGELOG.md**, below the title:

~~~markdown
## 0.1.2 - 2026-07-13

- Add a child-simple Fish Audio and optional ElevenLabs key-and-voice walkthrough.
- Complete the setup wizard with hidden key storage, numbered voice names, saved provider IDs, and readiness checks.
- Preserve saved credentials and voice choices across blank or failed reruns.
- Normalize provider lookup failures without exposing vendor details, keys, or voice IDs.
~~~

- [ ] **Step 4: Extend and reset the release checklist for v0.1.2**

Add under **Automated evidence** in **docs/RELEASE-CHECKLIST.md**:

~~~markdown
- [ ] Voice setup wizard fake-provider tests pass without live cloud calls.
~~~

Add under **Supported machines**:

~~~markdown
- [ ] Voice setup wizard hidden prompts and safe rerun pass on Apple Silicon and Windows 11/WSL2.
~~~

Add under **Credentialed smoke tests**:

~~~markdown
- [ ] Fish Audio setup wizard lists bookmarked voice names and saves a selected voice.
- [ ] ElevenLabs setup wizard lists available fallback voice names and saves a selected voice.
~~~

Replace the prior generic deployment approval line with:

~~~markdown
- [ ] User approved deployment of v0.1.2.
~~~

Do not check credentialed or clean-machine items without direct sanitized evidence. Never record a key, request header, private voice ID, or private media path as evidence.

- [ ] **Step 5: Run focused release tests and package checks**

Run:

~~~bash
uv run pytest tests/foundation/test_package.py tests/release/test_release_gate.py -q
uv run ugc-video version
uv lock --check
uv build
~~~

Expected:

- both focused test files pass;
- the CLI prints **ugc-video 0.1.2**;
- the lockfile is current;
- wheel and source distribution build successfully.

- [ ] **Step 6: Commit the release-preparation increment**

Run:

~~~bash
git add src/ugc_video/__init__.py pyproject.toml uv.lock CHANGELOG.md docs/RELEASE-CHECKLIST.md tests/foundation/test_package.py tests/release/test_release_gate.py
git diff --cached --check
git commit -m "chore: prepare voice setup release"
~~~

### Task 6: Verify locally, review security, and stop at the deployment gate

**Files:**

- Verify all changed files
- Update only after explicit deployment approval: **docs/RELEASE-CHECKLIST.md**

- [ ] **Step 1: Inspect the complete change set before claiming completion**

Run:

~~~bash
git status --short --branch
git log --oneline --decorate origin/main..HEAD
git diff origin/main...HEAD --stat
git diff origin/main...HEAD -- README.md docs src tests pyproject.toml CHANGELOG.md
git diff --check origin/main...HEAD
~~~

Expected: only the approved spec, plan, guide, setup implementation, tests, and v0.1.2 metadata differ from origin/main. No credential, media, auth file, unrelated edit, or generated build artifact is tracked.

- [ ] **Step 2: Run the repository-required fast doctor**

Run:

~~~bash
uv run ugc-video doctor --fast
~~~

Expected: non-billable local capability checks complete without exposing credentials. Record any environment-only limitation separately from a code failure.

- [ ] **Step 3: Run all automated Python and static checks**

Run:

~~~bash
uv sync --frozen --extra dev
uv run pytest -q
uv run ruff check .
uv run mypy src
~~~

Expected: all tests pass on the local supported Python version; Ruff and strict mypy report no errors.

- [ ] **Step 4: Run Remotion, platform-script, package, and offline-demo checks**

Run:

~~~bash
npm ci --prefix remotion
npm --prefix remotion run typecheck
bash -n setup-macos.sh scripts/*.sh START-HERE-MAC.command
uv run ugc-video demo --offline-fixtures
uv build
~~~

If PowerShell is installed locally, also run:

~~~bash
pwsh -NoProfile -File tests/platform/Test-WindowsScripts.ps1
~~~

Expected: Remotion typecheck, shell syntax, available PowerShell contracts, offline demo, and package build pass without cloud calls.

- [ ] **Step 5: Run both secret scans**

Run:

~~~bash
gitleaks version
scripts/check-secrets.sh
git ls-files | rg '(^|/)(\.env|secrets\.env|auth\.json)$|\.(mp3|wav|opus|mp4|mov)$'
~~~

Expected:

- Gitleaks history and worktree scans report no leaks.
- The final tracked-file search returns no matches and therefore exits 1.
- Synthetic values appear only in isolated tests and never resemble a real vendor credential.

- [ ] **Step 6: Run the full local acceptance script**

Run:

~~~bash
scripts/acceptance.sh
~~~

Expected: pytest, Ruff, mypy, Gitleaks, shell syntax, full doctor, and offline demo all pass. If a local model or executable prerequisite is missing, install or repair only the documented project-owned prerequisite, then rerun the failed gate once.

- [ ] **Step 7: Review acceptance criteria against evidence**

Confirm all of the following from test output and the final diff:

- The guide never teaches command-line key flags or manual secret-file editing.
- The setup command shows provider voice names and accepts numbered choices.
- No normal output includes a submitted key or full voice ID.
- Blank reruns keep saved credentials and selections.
- Authentication, empty voice lists, transport failures, and invalid menu choices each yield one concrete action.
- Fish Audio is required; unconfigured ElevenLabs and xAI remain explicit SKIP states.
- Exit code is zero only when Fish and every elected optional provider pass.
- Tests and CI contain no live provider calls.
- v0.1.2 metadata is consistent.

- [ ] **Step 8: Commit this implementation plan if it is not already committed**

Run:

~~~bash
git add docs/superpowers/plans/2026-07-13-voice-provider-onboarding.md
git diff --cached --check
git commit -m "docs: plan guided voice provider onboarding"
~~~

Skip this step only if the plan is already present in an earlier local commit.

- [ ] **Step 9: Stop and request the deployment decision**

Report:

- the local commit list;
- exact automated verification results;
- whether Apple Silicon and Windows 11/WSL2 clean-machine checks were performed;
- whether credentialed Fish Audio and ElevenLabs smoke tests were performed;
- any unchecked release-checklist items;
- rollback target **v0.1.1**.

Ask for explicit approval to push main and publish **v0.1.2**. If a clean-machine or credentialed check is still unchecked, request an explicit waiver for that named limitation. Do not interpret design approval or implementation approval as deployment approval.

- [ ] **Step 10: After explicit approval, record the gate and push main**

Change this line in **docs/RELEASE-CHECKLIST.md**:

~~~markdown
- [x] User approved deployment of v0.1.2.
~~~

Then run:

~~~bash
uv run pytest tests/release/test_release_gate.py tests/student/test_docs.py -q
git add docs/RELEASE-CHECKLIST.md
git diff --cached --check
git commit -m "docs: record v0.1.2 deployment approval"
git push origin main
RUN_ID=$(gh run list --branch main --workflow quality.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$RUN_ID" --exit-status
~~~

Expected: origin/main reaches the reviewed local commit and every quality job passes.

- [ ] **Step 11: Tag and publish v0.1.2**

Only after the main-branch quality run is green, run:

~~~bash
git tag -a v0.1.2 -m "ugc-video-student-kit v0.1.2"
git push origin v0.1.2
TAG_RUN_ID=$(gh run list --branch v0.1.2 --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$TAG_RUN_ID" --exit-status
gh release create v0.1.2 --verify-tag --generate-notes --title "UGC Video Student Kit v0.1.2"
~~~

Expected: the annotated tag resolves to the green main commit, the tag release-check passes, and the public release is created only after those checks.

- [ ] **Step 12: Verify publication and rollback artifacts**

Run:

~~~bash
gh release view v0.1.2
gh release view v0.1.1
git ls-remote --tags origin v0.1.2 v0.1.1
git status --short --branch
~~~

Expected: both v0.1.2 and rollback target v0.1.1 remain available, remote tag references resolve, and the local tree is clean and synchronized.
