#!/bin/bash
set -Eeuo pipefail
OUT="${1:?output directory required}"
mkdir -p "$OUT"
ffmpeg -y -loglevel error -f lavfi -i color=c=0x334455:s=1080x1920:d=2:r=30 \
  -f lavfi -i sine=frequency=440:duration=2 -shortest -c:v libx264 -pix_fmt yuv420p \
  -c:a aac "$OUT/animation.mp4"
ffmpeg -y -loglevel error -f lavfi -i sine=frequency=220:duration=2 \
  -ac 1 -ar 44100 "$OUT/voice.wav"
