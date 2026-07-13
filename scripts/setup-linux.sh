#!/usr/bin/env bash
set -euo pipefail
echo "[ugc-video] Linux/WSL setup starting"
command -v ffmpeg >/dev/null || echo "Install ffmpeg before running production jobs"
python3 -m pip install -e '.[dev]' >/dev/null
python3 -m ugc_video.cli doctor --json
echo "[ugc-video] setup complete"
