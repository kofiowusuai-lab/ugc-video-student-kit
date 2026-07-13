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
