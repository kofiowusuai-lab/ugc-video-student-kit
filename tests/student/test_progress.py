import io

from ugc_video.progress import ProgressReporter


def test_progress_reports_elapsed_stage_without_secret() -> None:
    stream = io.StringIO()
    times = iter([10.0, 10.0, 12.5])
    reporter = ProgressReporter(stream=stream, clock=lambda: next(times), secrets=["secret-123"])
    reporter.start("voice", "using secret-123")
    reporter.update("voice", "waiting")
    output = stream.getvalue()
    assert "[0.00s] voice: using [REDACTED]" in output
    assert "[2.50s] voice: waiting" in output
    assert "secret-123" not in output
