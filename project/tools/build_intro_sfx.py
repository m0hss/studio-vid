"""SFX-only soundtracks (no music) for the five intro pitches -> intros/<id>/sfx.wav (10 s each).
Voices are copied from build_audio.py (which decodes the music at import, so it can't be imported)."""
import os, wave
import numpy as np

SR = 48000
DUR = 10.0
N = int(DUR * SR)
ROOT = os.path.join(os.path.dirname(__file__), "..", "intros")
rng = np.random.default_rng(11)


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
    pan = np.linspace(-0.6, 0.6, n)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([y * l, y * r], 1).astype(np.float32)


def reverse_swell(d=0.42):
    n = int(d * SR)
    u = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    y = onepole_lp(x, 600 + 7000 * u ** 2)
    y = y * u ** 3
    y[-int(0.006 * SR):] *= np.linspace(1, 0, int(0.006 * SR))
    y /= np.max(np.abs(y)) + 1e-9
    return y.astype(np.float32)


# ---- new voices
def clock_tick(tock=False):
    """mechanical escapement: a bright click over a short wooden knock"""
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n) * np.exp(-t * 600)
    nz = nz - onepole_lp(nz, 3000.0)
    knock = np.sin(2 * np.pi * (900 if tock else 1150) * t) * np.exp(-t * 160)
    low = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 70)
    return (nz * 0.35 + knock * 0.4 + low * 0.35).astype(np.float32)


def neon_hum(level):
    """mains hum + tube crackle; level is a per-sample brightness curve (0..1)"""
    t = np.arange(len(level)) / SR
    hum = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(100, 0.5), (200, 0.28), (300, 0.12), (400, 0.06)])
    nz = rng.standard_normal(len(level))
    crackle = (nz - onepole_lp(nz, 4000.0)) * (rng.random(len(level)) < 0.004) * 1.4
    hiss = onepole_lp(nz, 6000.0) * 0.05
    lv = onepole_lp(level.astype(np.float64), 400.0)  # de-click the steps
    return ((hum * 0.5 + crackle + hiss) * lv).astype(np.float32)


def zap():
    """the snap of a tube striking"""
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n) * np.exp(-t * 90)
    return ((nz - onepole_lp(nz, 1500.0)) * 0.6 + np.sin(2 * np.pi * 100 * t) * np.exp(-t * 30) * 0.5).astype(np.float32)


class Track:
    def __init__(self):
        self.x = np.zeros((N, 2), np.float32)

    def place(self, sig, t, pan=0.0, gain=1.0):
        i = int(t * SR)
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
        j = min(N, i + len(sig))
        self.x[i:j] += sig[: j - i] * gain

    def typing(self, first, step, count, pan=0.0, gain=0.34):
        for k in range(count):
            self.place(tick(1.0 + rng.uniform(-0.08, 0.08)), first + k * step, pan + rng.uniform(-0.1, 0.1),
                       gain + rng.uniform(-0.05, 0.05))

    def handoff(self, flood=True):
        """7.6 flood into the Foodee design; 8.45 select, 8.75 delete, ROSA'S typed (same as the film)"""
        if flood:
            self.place(whoosh(0.40, 500, 4200, 1200, 0.85), 7.6, 0, 0.22)
        self.place(blip(900, 1500, 0.09), 8.45, 0, 0.22)
        self.place(tick(0.8), 8.75, 0, 0.42)
        self.typing(8.95, 0.09, 6)

    def write(self, name):
        peak = np.max(np.abs(self.x))
        mix = self.x / max(peak, 1e-9) * 0.89  # -1 dBFS peak
        pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
        out = os.path.join(ROOT, name, "sfx.wav")
        with wave.open(out, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        print("wrote", out)


# 1 · business card
a = Track()
a.place(whoosh(0.85, 250, 1800, 400, 0.45), 1.7, 0, 0.16)       # the card turns
a.place(whoosh(0.6, 300, 1400, 300, 0.4), 3.45, 0, 0.07)        # lifts
a.typing(5.95, 0.085, 8)                                          # rosas.be
a.place(blip(800, 1600, 0.12), 7.0, 0, 0.28)
a.handoff()
a.write("01-business-card")

# 2 · address bar
b = Track()
b.typing(0.42, 0.085, 9)
b.place(tick(0.7), 1.35, 0, 0.55)                                 # enter
b.place(whoosh(0.9, 2400, 2600, 300, 0.1), 1.4, 0, 0.08)          # pull back
b.place(blip(420, 300, 0.28), 2.5, 0, 0.3)                        # nothing there
b.place(tick(1.15), 5.9, 0, 0.3)                                  # reload
b.place(whoosh(1.3, 300, 3200, 900, 0.85), 6.3, 0, 0.1)
b.place(blip(800, 1600, 0.12), 6.75, 0, 0.28)
b.handoff()
b.write("02-address-bar")

# 3 · neon sign: the hum follows the sign's brightness (same flicker pairs as the page)
c = Track()
lv = np.zeros(N)
def steps(pairs, until):
    for (t0, v), (t1, _) in zip(pairs, pairs[1:] + [(until, 0)]):
        lv[int(t0 * SR):int(t1 * SR)] = v
steps([(0.25, 1), (0.31, 0.1), (0.36, 0.9), (0.44, 0.2), (0.5, 1), (0.62, 0.55), (0.66, 1), (2.2, 0.78), (2.26, 1),
       (3.0, 0.3), (3.06, 1), (3.15, 0.1), (3.22, 0.8), (3.3, 0), (3.36, 0.55), (3.45, 0)], 3.45)
for i in range(6):
    lv[int((5.0 + i * 0.1) * SR):int(8.0 * SR)] = 0.45 + i * 0.11      # each letter adds a tube
lv[int(6.6 * SR):int(8.0 * SR)] *= np.linspace(1, 1.6, int(8.0 * SR) - int(6.6 * SR))
lv[int(7.9 * SR):int(8.05 * SR)] *= np.linspace(1, 0, int(8.05 * SR) - int(7.9 * SR))
c.place(neon_hum(lv), 0, 0, 0.5)
for t in [0.25, 0.36, 0.5, 0.66, 3.06, 3.22]:
    c.place(zap(), t, rng.uniform(-0.2, 0.2), 0.35)
c.place(zap(), 3.45, 0, 0.5)                                       # dies
for k in range(13):
    c.place(tick(0.9), 4.3 + k * 0.045, 0, 0.26)                     # backspace the dead tubes
for i in range(6):
    c.place(tick(1.0), 5.0 + i * 0.1, 0, 0.3)
    c.place(zap(), 5.0 + i * 0.1, 0, 0.3)
c.place(reverse_swell(1.2), 6.75, 0, 0.18)
c.handoff(flood=False)
c.write("03-neon-sign")

# 4 · street after dark
d = Track()
d.place(whoosh(4.4, 200, 700, 200, 0.5), 0.0, 0, 0.05)             # night air, the walk
d.place(blip(800, 1600, 0.12), 4.85, 0, 0.26)
d.place(tick(0.8), 5.1, 0, 0.42)
d.typing(5.25, 0.1, 6)
d.place(tick(0.6), 5.95, 0, 0.5)                                    # light switch
d.place(zap(), 5.96, 0, 0.2)
d.place(whoosh(1.5, 300, 4000, 1200, 0.9), 6.45, 0, 0.2)           # through the window
d.handoff(flood=False)
d.write("04-street")

# 5 · 72-hour clock
e = Track()
for s in range(1, 6):
    e.place(clock_tick(s % 2 == 0), float(s), 0, 0.55)
e.place(whoosh(0.8, 400, 1600, 300, 0.4), 5.4, 0, 0.06)
for k in range(16):
    e.place(tick(1.3 + rng.uniform(-0.2, 0.2)), 6.0 + k * 0.045, rng.uniform(-0.4, 0.4), 0.16)   # scramble
e.place(tick(0.9), 6.75, 0, 0.4)                                    # lands
e.place(blip(800, 1600, 0.12), 7.05, 0, 0.28)
e.handoff()
e.write("05-clock")
