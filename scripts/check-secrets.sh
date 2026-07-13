#!/bin/bash
set -Eeuo pipefail
gitleaks git --no-banner --redact
gitleaks dir . --no-banner --redact
if git ls-files | grep -E '(^|/)(\.env|secrets\.env|auth\.json)$|\.(mp3|wav|opus|mp4|mov)$' >/dev/null; then
  echo "Tracked secret or generated-media file detected." >&2
  exit 1
fi
