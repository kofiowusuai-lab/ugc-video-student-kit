import json
from typing import Optional

from ugc_video.capabilities import discover


def run(*, full: bool = False, as_json: bool = False, provider: Optional[str] = None) -> int:
    capabilities = discover()
    report: dict[str, object] = {
        "capabilities": capabilities,
        "provider": provider,
        "mode": "full" if full else "fast",
    }
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, value in capabilities.items():
            print(f"{name}: {value or 'missing'}")
    return 0
