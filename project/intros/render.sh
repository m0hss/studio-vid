#!/usr/bin/env bash
# Render the five intro pitches (SFX only, no music) to ../out/intros/.
# Each intro folder symlinks ../../assets and ../_shared, so it renders as a standalone HyperFrames project.
# HYPERFRAMES_BROWSER_PATH may point at a local Chrome headless shell (see `npx hyperframes doctor`).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/build_intro_sfx.py
mkdir -p ../out/intros
for d in intros/0*/; do
  name=$(basename "$d")
  npx hyperframes lint "$d"
  npx hyperframes render "$d" --quality delivery --fps 30 -o "../out/intros/$name.mp4"
done
