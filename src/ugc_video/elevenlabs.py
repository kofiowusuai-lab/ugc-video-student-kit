import httpx


class ElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self, api_key: str, base_url: str = "https://api.elevenlabs.io"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def synthesize(self, text: str, voice_id: str) -> bytes:
        r = httpx.post(
            f"{self.base_url}/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": self.api_key},
            json={"text": text},
            timeout=60,
        )
        r.raise_for_status()
        return r.content
