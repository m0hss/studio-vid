# Fixbyte Studio — "Your Name Here" (HyperFrames source)

- `index.html` — the whole film on one GSAP timeline (scenes A–F, see `STORYBOARD.md`)
- `assets/designs/` — live Fixbyte design demos captured at 1.5×, one frame per keystroke (`<id>_orig|sel|tNN.webp`)
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
```
