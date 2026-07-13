import re
from collections.abc import Iterable

_PATTERNS = (
    re.compile(r"(?i)(authorization:\s*bearer\s+)\S+"),
    re.compile(r"(?i)(xi-api-key[:=]\s*)\S+"),
    re.compile(r"(?i)((?:FISH_AUDIO|ELEVENLABS|XAI)_API_KEY=)\S+"),
    re.compile(r"(?i)(api[_-]?key[=: ]+)\S+"),
)


def redact(message: str, secrets: Iterable[str] = ()) -> str:
    safe = str(message)
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, "[REDACTED]")
    for pattern in _PATTERNS:
        safe = pattern.sub(r"\1[REDACTED]", safe)
    return safe
