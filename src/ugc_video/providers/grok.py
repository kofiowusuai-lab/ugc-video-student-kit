import base64
import json
import time
from collections.abc import Callable
from pathlib import Path

import httpx

from ugc_video.domain import AnimationRequest, AnimationResult, FailureKind
from ugc_video.providers.base import ProviderError


class GrokApiProvider:
    name = "grok-api"

    def __init__(self, api_key: str, client: httpx.Client | None = None, sleep: Callable[[float], None] = time.sleep, max_polls: int = 120) -> None:
        self._api_key = api_key
        self.client = client or httpx.Client(timeout=90)
        self.sleep = sleep
        self.max_polls = max_polls

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def animate(self, request: AnimationRequest) -> AnimationResult:
        mime = "image/png" if request.image_path.suffix.lower() == ".png" else "image/jpeg"
        encoded = base64.b64encode(request.image_path.read_bytes()).decode("ascii")
        response = self.client.post("https://api.x.ai/v1/videos/generations", headers=self.headers, json={"model": "grok-imagine-video", "prompt": request.prompt, "image": {"url": f"data:{mime};base64,{encoded}"}, "duration": request.duration_seconds, "aspect_ratio": request.aspect_ratio, "resolution": request.resolution})
        if response.is_error:
            self._raise(response)
        request_id = str(response.json()["request_id"])
        for _ in range(self.max_polls):
            poll = self.client.get(f"https://api.x.ai/v1/videos/{request_id}", headers={"Authorization": f"Bearer {self._api_key}"})
            if poll.is_error:
                self._raise(poll)
            payload = poll.json()
            if payload.get("status") == "done":
                media = self.client.get(payload["video"]["url"])
                media.raise_for_status()
                request.destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = request.destination.with_suffix(".part")
                temporary.write_bytes(media.content)
                temporary.replace(request.destination)
                return AnimationResult(provider=self.name, model=str(payload.get("model", "grok-imagine-video")), video_path=request.destination, request_id=request_id, usage=payload.get("usage", {}))
            if payload.get("status") in {"failed", "expired"}:
                raise ProviderError(FailureKind.TRANSIENT, f"Grok video request {payload['status']}")
            self.sleep(5)
        raise ProviderError(FailureKind.TRANSIENT, "Grok video polling timed out")

    def _raise(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            kind = FailureKind.AUTHENTICATION
        elif response.status_code == 429:
            kind = FailureKind.RATE_LIMIT
        elif response.status_code >= 500:
            kind = FailureKind.TRANSIENT
        else:
            kind = FailureKind.CONFIGURATION
        raise ProviderError(kind, f"Grok request failed with HTTP {response.status_code}")


class GuidedGrokProvider:
    name = "grok-guided"

    def __init__(self, handoff_path: Path) -> None:
        self.handoff_path = handoff_path

    def prepare(self, request: AnimationRequest) -> Path:
        self.handoff_path.parent.mkdir(parents=True, exist_ok=True)
        self.handoff_path.write_text(json.dumps({"image": str(request.image_path.resolve()), "prompt": request.prompt, "destination": str(request.destination.resolve()), "durationSeconds": request.duration_seconds, "aspectRatio": request.aspect_ratio, "resolution": request.resolution}, indent=2) + "\n", encoding="utf-8")
        return self.handoff_path
