#!/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! grep -qi microsoft /proc/sys/kernel/osrelease; then
  echo "This Linux installer is supported inside Windows 11 WSL2 only." >&2
  exit 64
fi

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  build-essential cmake curl espeak-ng ffmpeg git git-lfs jq libsndfile1 \
  python3 python3-venv rubberband-cli

if ! command -v node >/dev/null 2>&1 || [[ "$(node --version)" != v22.* ]]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv python install 3.11

if ! command -v whisper-cli >/dev/null 2>&1; then
  BUILD_ROOT="$HOME/.cache/ugc-video/whisper.cpp"
  mkdir -p "$(dirname "$BUILD_ROOT")"
  if [[ ! -d "$BUILD_ROOT/.git" ]]; then
    git clone --branch v1.7.6 --depth 1 https://github.com/ggerganov/whisper.cpp.git "$BUILD_ROOT"
  fi
  cmake -S "$BUILD_ROOT" -B "$BUILD_ROOT/build" -DWHISPER_BUILD_EXAMPLES=ON
  cmake --build "$BUILD_ROOT/build" --config Release -j2
  sudo install -m 0755 "$BUILD_ROOT/build/bin/whisper-cli" /usr/local/bin/whisper-cli
fi

sudo npm install --global @openai/codex
if ! command -v grok >/dev/null 2>&1; then
  curl -fsSL https://x.ai/cli/install.sh | bash
  export PATH="$HOME/.grok/bin:$PATH"
fi

cd "$ROOT"
uv sync --frozen --python 3.11 --extra dev --extra wsl-whisper
"$ROOT/scripts/install-codex-skill.sh"
if [[ -f "$ROOT/remotion/package.json" ]]; then
  npm install --prefix "$ROOT/remotion"
fi
./scripts/download-models.sh
uv run ugc-video doctor --fast
echo "WSL2 installation is ready. Run: uv run ugc-video setup"
