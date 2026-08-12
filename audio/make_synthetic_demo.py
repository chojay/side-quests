#!/usr/bin/env python3
"""Generate synthetic demo clips for the noise monitor - no recording needed.

Builds three seeded WAV 'camera clips' with timestamped filenames:
  - one during permitted hours with hammering bursts and a saw segment
  - one before permitted hours (07:15) with hammering  -> flagged in report
  - one quiet clip (background only)                   -> zero events

Everything is generated noise; no microphone, no real audio, no people.
Run: python3 make_synthetic_demo.py && python3 noise_monitor.py \
       --input examples/demo-clips --out examples/report --weekdays-only
"""
import wave
from pathlib import Path

import numpy as np

SR = 16000
rng = np.random.default_rng(20260315)
OUT = Path(__file__).parent / "examples" / "demo-clips"
OUT.mkdir(parents=True, exist_ok=True)


def pinkish(n, level_db=-46.0):
    """Low-passed noise floor (wind/street rumble stand-in)."""
    white = rng.normal(size=n)
    kernel = np.ones(24) / 24
    x = np.convolve(white, kernel, mode="same")
    x /= (np.abs(x).max() + 1e-9)
    return x * (10 ** (level_db / 20))


def hammer_burst(x, t0, n_hits=8, level_db=-12.0):
    """Impact train: sharp decaying transients ~2/sec."""
    amp = 10 ** (level_db / 20)
    for i in range(n_hits):
        s = int((t0 + i * 0.5 + rng.uniform(-0.05, 0.05)) * SR)
        dur = int(0.09 * SR)
        if s + dur > len(x):
            break
        env = np.exp(-np.linspace(0, 9, dur))
        x[s:s + dur] += amp * env * rng.normal(size=dur)


def saw_segment(x, t0, dur_s, level_db=-16.0):
    """Broadband band-limited roar (circular saw stand-in)."""
    amp = 10 ** (level_db / 20)
    s, n = int(t0 * SR), int(dur_s * SR)
    if s + n > len(x):
        n = len(x) - s
    tone = np.sin(2 * np.pi * 130 * np.arange(n) / SR)      # motor fundamental
    x[s:s + n] += amp * (0.4 * tone + 0.6 * rng.normal(size=n))


def write(name, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print("wrote", OUT / name)


def clip(seconds):
    return pinkish(int(seconds * SR))


# 09:30, permitted hours: hammering + saw
x = clip(300)
hammer_burst(x, 40); hammer_burst(x, 95, n_hits=12)
saw_segment(x, 170, 35)
write("20260316_093000.wav", x)

# 07:15, before permitted hours: hammering -> flagged
x = clip(240)
hammer_burst(x, 30, n_hits=10); hammer_burst(x, 150, n_hits=14, level_db=-10)
write("20260316_071500.wav", x)

# 13:00, quiet clip: background only -> zero events
write("20260316_130000.wav", clip(180))
