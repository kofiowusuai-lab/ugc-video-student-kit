import json
from typing import Optional
from ugc_video.capabilities import discover
def run(*, full: bool=False, as_json: bool=False, provider: Optional[str]=None) -> int:
    report={"capabilities":discover(), "provider":provider, "mode":"full" if full else "fast"}
    if as_json: print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for k,v in report["capabilities"].items(): print(f"{k}: {v or 'missing'}")
    return 0
