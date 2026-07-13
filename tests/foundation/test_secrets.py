from ugc_video.redaction import redact


def test_redacts_api_key():
    assert "[REDACTED]" in redact("api_key=abcdefghijklmnop")
