from pathlib import Path

from ugc_video.render.finish import finish_video


def test_finish_uses_vertical_safe_audio_and_atomic_output(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    animation = tmp_path / "animation.mp4"
    voice = tmp_path / "voice.wav"
    destination = tmp_path / "final.mp4"
    animation.write_bytes(b"video")
    voice.write_bytes(b"audio")

    def runner(command: list[str]) -> None:
        commands.append(command)
        Path(command[-1]).write_bytes(b"final")

    finish_video(animation, voice, destination, runner=runner)
    assert destination.read_bytes() == b"final"
    assert "loudnorm=I=-16:LRA=11:TP=-1.5" in commands[0]
    assert any(
        "scale=1080:1920:force_original_aspect_ratio=decrease" in item for item in commands[0]
    )
