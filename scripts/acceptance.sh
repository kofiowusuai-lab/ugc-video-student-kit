#!/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
uv sync --frozen --extra dev
uv run pytest -q
uv run ruff check .
uv run mypy src
gitleaks version >/dev/null
scripts/check-secrets.sh
bash -n setup-macos.sh scripts/*.sh START-HERE-MAC.command
uv run ugc-video doctor --full
uv run ugc-video demo --offline-fixtures
