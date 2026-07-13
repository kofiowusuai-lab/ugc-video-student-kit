import httpx
class FishAudioProvider:
    name = "fish"
    def __init__(self, api_key: str, base_url: str = "https://api.fish.audio"): self.api_key=api_key; self.base_url=base_url.rstrip('/')
    def synthesize(self, text: str, voice_id: str) -> bytes:
        r=httpx.post(self.base_url+"/v1/tts", headers={"Authorization":f"Bearer {self.api_key}","model":voice_id,"Content-Type":"application/json"}, json={"text":text}, timeout=60); r.raise_for_status(); return r.content
