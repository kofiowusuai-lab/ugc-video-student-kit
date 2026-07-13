import re
def redact(value: str) -> str:
    return re.sub(r'(?i)(sk-|api[_-]?key[=: ]+)[A-Za-z0-9_-]{8,}', r'\1[REDACTED]', value)
