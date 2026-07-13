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
