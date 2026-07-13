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
