#!/usr/bin/env bash
# Mix assets/audio/vo.wav (tools/build_voice.py) over assets/audio/mix_raw.wav (tools/build_audio.py):
# music + SFX duck under the voice, then the same static gain + limiter as master_audio.sh.
# Writes assets/audio/mix_vo.wav (mix.wav, the voiceless master, is left alone). Prints EBU R128 summary.
set -euo pipefail
cd "$(dirname "$0")/.."
FF=../.tools/ffmpeg
BED=assets/audio/mix_raw.wav; VO=assets/audio/vo.wav; OUT=assets/audio/mix_vo.wav
GAIN=${GAIN:-5.5}
$FF -v error -y -i $BED -i $VO -filter_complex "
  [1]volume=0.80,asplit=2[vo][key];
  [0][key]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350:makeup=1[bed];
  [bed][vo]amix=inputs=2:normalize=0,aresample=192000,volume=${GAIN}dB,alimiter=limit=0.79:attack=3:release=60:level=false,aresample=48000" \
  -c:a pcm_s16le $OUT
$FF -hide_banner -i $OUT -af ebur128=peak=true -f null - 2>&1 | grep -A20 Summary | grep -E 'I:|LRA:|Peak:'
