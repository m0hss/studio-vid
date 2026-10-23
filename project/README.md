# Fixbyte Studio — "Your Name Here" (HyperFrames source)

- `index.html` — the whole film on one GSAP timeline (scenes A–F, see `STORYBOARD.md`)
- `assets/designs/` — live Fixbyte design demos captured at 1.5×, one frame per keystroke (`<id>_orig|sel|tNN.webp`)
- `reel/index.html` — the same film as a 1080×1920 reel (re-laid out; `reel/assets` links to `assets/`), using `assets/designs-phone/` (402×874 @3× captures of the mobile layouts)
- `assets/wall/` — 17 design captures for the wall · `assets/audio/mix.wav` — mastered soundtrack
- `tools/build_audio.py` + `tools/master_audio.sh` — music excerpt, splice, sound design, −14 LUFS master
- `tools/capture/` — `capture_states.mjs` (rename the live designs keystroke by keystroke) and `composite_states.py` (freeze everything but the name; writes `assets/designs/` + `meta.json`, inlined as `META` in index.html)

Fonts: Space Grotesk, Inter, JetBrains Mono (from @fontsource) and Aller Bold for the end-card lockup (Dalton Maag, supplied by the client; licence in `assets/fonts/Aller-FreeLicenceAgreement.pdf`).

FFmpeg is the static build in `../.tools` (added to PATH below).

```bash
PATH=../.tools:$PATH npx hyperframes preview          # edit in Studio
python3 tools/build_audio.py && ./tools/master_audio.sh
PATH=../.tools:$PATH npx hyperframes check .
PATH=../.tools:$PATH npx hyperframes render . --quality delivery --fps 30 -o ../out/fixbyte-studio-promo.mp4
# voice-over version (Kokoro TTS, am_michael; venv + model files in .cache/kokoro, both git-ignored)
python3 -m venv .venv && .venv/bin/pip install kokoro-onnx soundfile
.venv/bin/python tools/build_voice.py && ./tools/mix_voice.sh
PATH=../.tools:$PATH npx hyperframes render voiceover --quality delivery --fps 30 -o ../out/fixbyte-studio-promo-voiceover.mp4
# then mux the mastered mix as-is (the renderer re-levels this track)
ffmpeg -i ../out/fixbyte-studio-promo-voiceover.mp4 -i assets/audio/mix_vo.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -movflags +faststart out.mp4
# reel (1080x1920): phone captures of the three designs, same timeline and soundtrack
CHROME=<headless-shell> node tools/capture/capture_states.mjs <dir> --phone && python3 tools/capture/composite_states.py <dir> --phone
PATH=../.tools:$PATH npx hyperframes render reel --quality delivery --fps 30 -o ../out/fixbyte-studio-promo-reel.mp4
```
