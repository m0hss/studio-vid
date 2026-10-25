#!/usr/bin/env bash
# Master assets/audio/mix_raw.wav -> assets/audio/mix.wav: static gain to ~-14 LUFS + brickwall limiter (keeps the
# build-to-drop dynamics; avoids loudnorm's dynamic mode). Prints EBU R128 summary.
set -euo pipefail
cd "$(dirname "$0")/.."
FF=../.tools/ffmpeg
IN=${IN:-assets/audio/mix_raw.wav}; OUT=${OUT:-assets/audio/mix.wav}
GAIN=${GAIN:-5.7}
$FF -v error -y -i $IN -af "aresample=192000,volume=${GAIN}dB,alimiter=limit=0.79:attack=3:release=60:level=false,aresample=48000" -c:a pcm_s16le $OUT
$FF -hide_banner -i $OUT -af ebur128=peak=true -f null - 2>&1 | grep -A20 Summary | grep -E 'I:|LRA:|Peak:'
