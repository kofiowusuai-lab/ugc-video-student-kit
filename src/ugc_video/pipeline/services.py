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
from ugc_video.progress import ProgressReporter
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
    fish: VoiceProvider = (
        FishAudioProvider(secrets["FISH_AUDIO_API_KEY"])
        if secrets.get("FISH_AUDIO_API_KEY")
        else MissingVoiceProvider("fish", "FISH_AUDIO_API_KEY")
    )
    eleven: VoiceProvider = (
        ElevenLabsProvider(secrets["ELEVENLABS_API_KEY"])
        if secrets.get("ELEVENLABS_API_KEY")
        else MissingVoiceProvider("elevenlabs", "ELEVENLABS_API_KEY")
    )
    return fish, eleven


def provider_health(secrets: dict[str, str], name: str) -> ProviderHealth:
    fish, eleven = build_voice_providers(secrets)
    if name == "fish":
        return fish.health()
    if name == "elevenlabs":
        return eleven.health()
    if name == "grok":
        return ProviderHealth(
            provider="grok",
            ok=True,
            detail="xAI API key configured"
            if secrets.get("XAI_API_KEY")
            else "guided Grok mode available",
        )
    raise ValueError("provider must be fish, elevenlabs, or grok")


def build_services(
    config: AppConfig,
    secrets: dict[str, str],
    project: ProjectPaths,
    reporter: ProgressReporter | None = None,
) -> PipelineServices:
    fish, eleven = build_voice_providers(secrets)
    router = VoiceRouter(fish, eleven, RetryPolicy(max_attempts=3))
    guided = GuidedGrokProvider(project.root / "work/grok-handoff.json")
    api = (
        GrokApiProvider(
            secrets["XAI_API_KEY"],
            progress=(lambda message: reporter.update("animation", message))
            if reporter
            else (lambda message: None),
        )
        if secrets.get("XAI_API_KEY")
        else None
    )

    def animate(script: str, still: Path, output: Path) -> dict[str, object]:
        prompt = (
            "Animate this adult UGC spokesperson with restrained natural movement, realistic blinking, and conversational mouth movement. Keep identity, clothing, camera, and background stable. She says exactly: "
            + script
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
        if api is None:
            raise ProviderError(FailureKind.AUTHENTICATION, "XAI_API_KEY is missing")
        result = api.animate(request)
        return {
            "provider": result.provider,
            "model": result.model,
            "request_id": result.request_id,
            "usage": result.usage,
        }

    def voice(script: str, output: Path) -> dict[str, object]:
        result = router.synthesize(
            config.voice_provider,
            VoiceRequest(
                text=script,
                voice_id=config.fish_voice_id,
                model=config.fish_model,
                destination=output,
            ),
            VoiceRequest(
                text=script,
                voice_id=config.elevenlabs_voice_id,
                model=config.elevenlabs_model,
                destination=output,
            ),
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
            load_backends(), wav, config.whisper_language, expected_text=expected
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
