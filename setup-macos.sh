#!/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This installer supports Apple Silicon macOS only. Contact the instructor for alternatives." >&2
  exit 64
fi

MEMORY_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
if (( MEMORY_GB < 16 )); then
  echo "Warning: 16 GB RAM is recommended; detected ${MEMORY_GB} GB." >&2
fi
FREE_KB=$(df -Pk "$HOME" | awk 'NR==2 {print $4}')
if (( FREE_KB < 15728640 )); then
  echo "At least 15 GB free storage is required for setup and video outputs." >&2
  exit 64
fi

if ! command -v brew >/dev/null 2>&1; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

brew install git git-lfs node@22 python@3.11 ffmpeg rubberband uv whisper-cpp
brew link --overwrite node@22
npm install --global @openai/codex

if ! command -v grok >/dev/null 2>&1; then
  curl -fsSL https://x.ai/cli/install.sh | bash
fi
export PATH="$HOME/.grok/bin:$PATH"

cd "$ROOT"
uv sync --frozen --python 3.11 --extra dev --extra mac-whisper
if [[ -f "$ROOT/remotion/package.json" ]]; then
  npm install --prefix "$ROOT/remotion"
fi
"$ROOT/scripts/download-models.sh"
uv run ugc-video doctor --fast

echo "Local installation is ready. Run: uv run ugc-video setup"
