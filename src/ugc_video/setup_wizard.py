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
