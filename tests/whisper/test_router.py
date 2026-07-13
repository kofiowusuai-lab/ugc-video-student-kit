from ugc_video.whisper import Transcript, WhisperRouter
def test_router_falls_back():
    result=WhisperRouter([lambda _: (_ for _ in ()).throw(RuntimeError("bad")), lambda _: Transcript("hello", "second")]).transcribe("x")
    assert result.backend == "second"
