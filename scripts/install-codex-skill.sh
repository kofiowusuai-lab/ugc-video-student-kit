#!/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/codex-skills/ugc-video-producer"
DESTINATION="${CODEX_HOME:-$HOME/.codex}/skills/ugc-video-producer"
mkdir -p "$(dirname "$DESTINATION")"
rm -rf -- "$DESTINATION"
cp -R "$SOURCE" "$DESTINATION"
echo "Installed Codex skill: $DESTINATION"
