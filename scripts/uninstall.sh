#!/bin/bash
set -Eeuo pipefail

YES=0
if [[ "${1:-}" == "--yes" ]]; then
  YES=1
fi

ROOT="${UGC_VIDEO_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/ugc-video}"
case "$ROOT" in
  "$HOME"|"/"|"")
    echo "Refusing unsafe uninstall root: $ROOT" >&2
    exit 64
    ;;
esac

if [[ $YES -ne 1 ]]; then
  read -r -p "Remove kit-owned data at $ROOT? [y/N] " answer
  [[ "$answer" == "y" || "$answer" == "Y" ]] || exit 0
fi

rm -rf -- "$ROOT"
echo "Removed kit-owned data: $ROOT"
echo "Shared tools such as Python, Node, FFmpeg, Homebrew, WSL2, Codex, and Grok were retained."
