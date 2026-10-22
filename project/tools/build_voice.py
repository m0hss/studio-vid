"""Voice-over for the film: Kokoro TTS (am_michael) reading the on-screen lines, placed on the film's timeline.

Usage (from ./project, inside the venv):
  python3 -m venv .venv && .venv/bin/pip install kokoro-onnx soundfile
  model files in .cache/kokoro/ (kokoro-v1.0.onnx, voices-v1.0.bin from the kokoro-onnx releases)
  .venv/bin/python tools/build_voice.py
Writes assets/audio/vo.wav (30 s, 48 kHz stereo, voice only); mix it with tools/mix_voice.sh.
"""
import os
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

SR = 48000
DUR = 30.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, ".cache", "kokoro")
OUT = os.path.join(ROOT, "assets", "audio", "vo.wav")
VOICE = "am_michael"

# (start in film seconds, latest end, text): each line sits inside the scene that shows it
LINES = [
    (3.70, 7.40, "Rosa's has been open for years. Online, it doesn't exist."),
    (16.50, 19.10, "Real designs. Built in your name."),
    (19.40, 23.30, "Free seventy-two hour live preview, on WhatsApp. No card needed."),
    (24.35, 29.00, "Fixbyte Studio. Try it free."),
]

kokoro = Kokoro(os.path.join(MODEL, "kokoro-v1.0.onnx"), os.path.join(MODEL, "voices-v1.0.bin"))
track = np.zeros(int(DUR * SR), np.float32)
for start, end, text in LINES:
    speed = 1.0
    while True:
        y, sr = kokoro.create(text, voice=VOICE, speed=speed, lang="en-us")
        # trim leading/trailing silence so the line starts on its cue
        nz = np.flatnonzero(np.abs(y) > 0.01)
        y = y[max(nz[0] - int(0.02 * sr), 0): nz[-1] + int(0.08 * sr)]
        if start + len(y) / sr <= end or speed >= 1.25:
            break
        speed += 0.05   # speed up a touch until the line fits its scene
    y = np.interp(np.arange(int(len(y) * SR / sr)) * sr / SR, np.arange(len(y)), y).astype(np.float32)
    i = int(start * SR)
    track[i:i + len(y)] += y[: len(track) - i]
    print(f"{start:6.2f}-{start + len(y) / SR:6.2f}s (≤{end}) speed {speed:.2f}  {text}")

track /= max(np.max(np.abs(track)), 1e-9) / 0.9
sf.write(OUT, np.stack([track, track], 1), SR, subtype="PCM_16")
print("wrote", OUT)
