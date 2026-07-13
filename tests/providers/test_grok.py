from pathlib import Path

import httpx
import respx

from ugc_video.domain import AnimationRequest
from ugc_video.providers.grok import GrokApiProvider, GuidedGrokProvider


@respx.mock
def test_api_mode_persists_request_and_downloads_result(tmp_path: Path) -> None:
    image = tmp_path / "still.png"
    image.write_bytes(b"png")
    respx.post("https://api.x.ai/v1/videos/generations").mock(
        return_value=httpx.Response(200, json={"request_id": "req-1"})
    )
    respx.get("https://api.x.ai/v1/videos/req-1").mock(
        side_effect=[
            httpx.Response(200, json={"status": "pending", "progress": 25}),
            httpx.Response(
                200,
                json={
                    "status": "done",
                    "video": {"url": "https://cdn.test/video.mp4"},
                    "usage": {"cost": 1},
                },
            ),
        ]
    )
    respx.get("https://cdn.test/video.mp4").mock(return_value=httpx.Response(200, content=b"video"))
    messages: list[str] = []
    result = GrokApiProvider("xai-key", sleep=lambda _: None, progress=messages.append).animate(
        AnimationRequest(
            image_path=image, prompt="Say the exact line.", destination=tmp_path / "animation.mp4"
        )
    )
    assert result.request_id == "req-1"
    assert result.video_path.read_bytes() == b"video"
    assert any("req-1: pending, progress=25" in message for message in messages)
    assert any("req-1: done" in message for message in messages)


def test_guided_mode_writes_handoff_without_fake_output(tmp_path: Path) -> None:
    image = tmp_path / "still.png"
    image.write_bytes(b"png")
    provider = GuidedGrokProvider(tmp_path / "handoff.json")
    result = provider.prepare(
        AnimationRequest(
            image_path=image, prompt="Natural movement", destination=tmp_path / "animation.mp4"
        )
    )
    assert result == tmp_path / "handoff.json"
    assert not (tmp_path / "animation.mp4").exists()
