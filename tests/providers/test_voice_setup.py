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
