import httpx

from ugc_video.domain import FailureKind, ProviderHealth, VoiceRequest, VoiceResult
from ugc_video.providers.base import ProviderError


class FishAudioProvider:
    name = "fish"

    def __init__(self, api_key: str, base_url: str = "https://api.fish.audio", client: httpx.Client | None = None) -> None:
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
            kind = FailureKind.POLICY if "policy" in response.text.lower() else FailureKind.CONFIGURATION
        raise ProviderError(kind, f"Fish Audio request failed with HTTP {response.status_code}")

    def bookmarked_voices(self) -> dict[str, str]:
        voices: dict[str, str] = {}
        for page in range(1, 101):
            response = self.client.get(f"{self.base_url}/model", params={"page_size": 100, "page_number": page}, headers=self.headers)
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
        response = self.client.post(f"{self.base_url}/v1/tts", headers={**self.headers, "Content-Type": "application/json", "model": request.model}, json={"text": request.text, "reference_id": request.voice_id, "format": "mp3"})
        if response.is_error:
            self._raise(response)
        if not response.content:
            raise ProviderError(FailureKind.TRANSIENT, "Fish Audio returned empty audio")
        request.destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = request.destination.with_suffix(request.destination.suffix + ".part")
        temporary.write_bytes(response.content)
        temporary.replace(request.destination)
        return VoiceResult(provider=self.name, model=request.model, voice_id=request.voice_id, audio_path=request.destination)
