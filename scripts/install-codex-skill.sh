#!/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"

install_skill() {
  local skill_name="$1"
  local source="$ROOT/codex-skills/$skill_name"
  local destination="$SKILLS_ROOT/$skill_name"

  if [[ ! -f "$source/SKILL.md" ]]; then
    echo "Bundled Codex skill is missing: $source" >&2
    exit 66
  fi

  mkdir -p "$SKILLS_ROOT"
  rm -rf -- "$destination"
  cp -R "$source" "$destination"
  echo "Installed Codex skill: $destination"
}

for skill_name in ugc-video-producer killer-script-system; do
  install_skill "$skill_name"
done
