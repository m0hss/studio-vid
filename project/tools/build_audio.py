"""Build the film's mixed soundtrack: music excerpt + synthesized sound design.

Usage: python3 tools/build_audio.py   (from ./project)
Writes assets/audio/mix_raw.wav (unmastered); master with tools/master_audio.sh.
"""
import subprocess, os, wave
import numpy as np

SR = 48000
DUR = 30.0
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FFMPEG = os.path.join(ROOT, "..", ".tools", "ffmpeg")
MUSIC = os.path.join(ROOT, "..", "assets", "music", "gs4u_syntheticwarpath.mp3")
OUT = os.path.join(ROOT, "assets", "audio", "mix_raw.wav")
rng = np.random.default_rng(7)


def decode(start, dur):
    cmd = [FFMPEG, "-v", "error", "-ss", f"{start:.4f}", "-t", f"{dur:.4f}", "-i", MUSIC,
           "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def ramp(n, kind="in"):
    x = np.linspace(0, 1, n)
    c = np.sin(x * np.pi / 2) ** 2
    return c if kind == "in" else c[::-1]


# ---------------------------------------------------------------- music
N = int(DUR * SR)
music = np.zeros((N, 2), np.float32)
XF = int(0.012 * SR)  # splice crossfade
SPLICE = 28.0
a = decode(135.955, SPLICE + 0.05)       # breakdown -> build -> riser -> drop
b = decode(191.955 - 0.012, 2.2)          # drop -> outro release
na = int(SPLICE * SR)
music[:na] = a[:na]
music[na - XF:na] *= ramp(XF, "out")[:, None]
seg = b[: N - na + XF]
seg[:XF] *= ramp(XF, "in")[:, None]
music[na - XF: na - XF + len(seg)] += seg
# fade in / fade out
fi = int(0.25 * SR)
music[:fi] *= ramp(fi, "in")[:, None]
f0, f1 = int(28.6 * SR), N
music[f0:f1] *= (np.cos(np.linspace(0, np.pi / 2, f1 - f0)) ** 2.2)[:, None]

# ---------------------------------------------------------------- sfx
sfx = np.zeros((N, 2), np.float32)


def place(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
    j = min(N, i + len(sig))
    sfx[i:j] += sig[: j - i] * gain


def onepole_lp(x, fc):
    """time-varying one-pole lowpass; fc can be array"""
    fc = np.broadcast_to(fc, x.shape)
    y = np.zeros_like(x)
    s = 0.0
    al = 1 - np.exp(-2 * np.pi * fc / SR)
    for i in range(len(x)):
        s += al[i] * (x[i] - s)
        y[i] = s
    return y


def tick(pitch=1.0):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    click = np.sin(2 * np.pi * 2600 * pitch * t) * np.exp(-t * 140)
    noise = rng.standard_normal(n) * np.exp(-t * 400)
    noise = noise - onepole_lp(noise, 2500.0)  # highpass-ish
    body = np.sin(2 * np.pi * 420 * pitch * t) * np.exp(-t * 90) * 0.5
    return (click * 0.35 + noise * 0.25 + body * 0.4).astype(np.float32)


def blip(f0=900, f1=1500, d=0.09):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = np.linspace(f0, f1, n)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.6 * np.exp(-t * 18)
    return (np.sin(ph) * env * 0.5).astype(np.float32)


def whoosh(d, f_start=400, f_peak=4500, f_end=900, peak_at=0.7):
    n = int(d * SR)
    x = rng.standard_normal(n).astype(np.float32)
    u = np.linspace(0, 1, n)
    fc = np.where(u < peak_at, f_start + (f_peak - f_start) * (u / peak_at) ** 2,
                  f_peak + (f_end - f_peak) * ((u - peak_at) / (1 - peak_at)))
    y = onepole_lp(onepole_lp(x, fc), fc * 1.3)
    env = np.where(u < peak_at, (u / peak_at) ** 2.2, (1 - (u - peak_at) / (1 - peak_at)) ** 1.6)
    y = y * env
    y /= np.max(np.abs(y)) + 1e-9
    # stereo movement
    pan = np.linspace(-0.6, 0.6, n)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([y * l, y * r], 1).astype(np.float32)


def chime():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f, dt, g in [(1318.5, 0.0, 0.5), (1975.5, 0.09, 0.42)]:
        k = int(dt * SR)
        tt = t[: n - k]
        s[k:] += g * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7) * (1 - np.exp(-tt * 400))
        s[k:] += g * 0.2 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 12)
    return (s * 0.5).astype(np.float32)


def reveal_hit():
    n = int(2.6 * SR)
    t = np.arange(n) / SR
    f = 38 + 30 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6) * (1 - np.exp(-t * 300))
    nz = rng.standard_normal(n)
    nz = nz - onepole_lp(nz, 3000.0)
    crash = nz * np.exp(-t * 2.4) * 0.22
    shimmer = sum(np.sin(2 * np.pi * fr * t + p) for fr, p in [(3520, 0), (4186, 1), (5274, 2)])
    shimmer = shimmer * np.exp(-t * 1.3) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)) * 0.03
    m = sub * 0.85 + crash + shimmer
    st = np.stack([m, m], 1)
    # decorrelate crash a little for width
    st[:, 1] += (np.roll(crash, 240) - crash) * 0.5
    return st.astype(np.float32)


def reverse_swell(d=0.42):
    n = int(d * SR)
    u = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    y = onepole_lp(x, 600 + 7000 * u ** 2)
    y = y * u ** 3
    y[-int(0.006 * SR):] *= np.linspace(1, 0, int(0.006 * SR))
    y /= np.max(np.abs(y)) + 1e-9
    return y.astype(np.float32)


# --- opening: rosas.com typed into the address bar (as tools/build_intro_sfx.py, intro 2)
for k in range(9):
    place(tick(1.0 + rng.uniform(-0.08, 0.08)), 0.42 + k * 0.085, rng.uniform(-0.1, 0.1), 0.34 + rng.uniform(-0.05, 0.05))
place(tick(0.7), 1.35, 0, 0.55)                                   # enter
place(whoosh(0.9, 2400, 2600, 300, 0.1), 1.4, 0, 0.08)            # pull back to the window
place(blip(420, 300, 0.28), 2.5, 0, 0.3)                          # 404
place(tick(1.15), 5.9, 0, 0.3)                                    # reload
place(whoosh(1.3, 300, 3200, 900, 0.85), 6.3, 0, 0.1)             # push in on the address
# select-all, then teal flood
place(blip(800, 1600, 0.12), 6.75, 0, 0.28)
place(whoosh(0.40, 500, 4200, 1200, 0.85), 7.6, 0, 0.22)

# typing: (select time, delete time, first letter time, step, count, pan)
TYPE = [
    (8.45, 8.75, 8.95, 0.090, 6, 0.0),      # Rosa's       (Foodee)
    (10.85, 11.05, 11.15, 0.050, 11, -0.2), # MAISON NOOR  (Cantara)
    (13.55, 13.80, 13.92, 0.065, 12, 0.0),  # AZUR VOYAGES (Dar Al Khalily)
]
for sel, dele, first, step, cnt, pan in TYPE:
    place(blip(900, 1500, 0.09), sel, pan, 0.22)
    place(tick(0.8), dele, pan, 0.42)
    for k in range(cnt):
        place(tick(1.0 + rng.uniform(-0.08, 0.08)), first + k * step, pan + rng.uniform(-0.1, 0.1),
              0.34 + rng.uniform(-0.05, 0.05))

# pushes between designs
place(whoosh(0.34, 400, 3800, 900, 0.7), 10.22, 0, 0.18)
# Cantara: pull back from the macro on the 12.0 hit
place(whoosh(0.55, 3200, 3600, 350, 0.12), 11.98, 0, 0.15)
place(whoosh(0.34, 400, 3800, 900, 0.7), 12.92, 0, 0.18)
# pull back into the wall
place(whoosh(0.70, 2400, 3000, 300, 0.25), 15.72, 0, 0.19)
# wall -> offer
place(whoosh(0.40, 300, 2600, 500, 0.6), 19.22, 0, 0.13)
place(chime(), 19.88, 0.2, 0.32)
place(tick(1.2), 20.55, 0.3, 0.22)
place(tick(1.3), 20.95, 0.35, 0.22)
# into the drop
place(reverse_swell(0.40), 23.58, 0, 0.16)
place(reveal_hit(), 24.0, 0, 0.55)
place(tick(1.1), 25.40, 0, 0.18)

mix = music + sfx
peak = np.max(np.abs(mix))
print(f"raw peak {20*np.log10(peak):.2f} dBFS")
mix = mix / max(peak, 1e-9) * 0.7
pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", OUT, len(pcm) / SR, "s")
