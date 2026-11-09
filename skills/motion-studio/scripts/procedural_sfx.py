#!/usr/bin/env python3
"""Synthesize simple, licence-free sound effects with code (seeded, deterministic).

Usage:
    python procedural_sfx.py --kind whoosh --dur 0.6 --seed 3 --out audio/sfx/whoosh1.wav
    python procedural_sfx.py --list
    python procedural_sfx.py --pack audio/sfx/procedural      # one of each kind

Kinds: whoosh, swish, riser, hit, boom, click, tick, pop, shimmer, glitch, typing.
Output: 48 kHz stereo 16-bit WAV, peak-normalized to -3 dBFS, short fades (no clicks).
These are designed sounds (not realistic Foley). Audition them before use.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import write_wav  # noqa: E402

SR = 48000
DEFAULT_DUR = {"whoosh": 0.7, "swish": 0.35, "riser": 2.0, "hit": 0.6, "boom": 1.6, "click": 0.05,
               "tick": 0.04, "pop": 0.15, "shimmer": 1.2, "glitch": 0.3, "typing": 1.0}


def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def onepole_lowpass(x, cutoff):
    """Time-varying one-pole low-pass. cutoff: scalar or array (Hz)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=np.float64), x.shape)
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # small buffers; clarity over speed
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def env_ad(n, attack, decay_pow=2.0):
    """Attack (fraction 0..1) then power-law decay."""
    e = np.ones(n)
    na = max(1, int(n * attack))
    e[:na] = np.linspace(0, 1, na)
    e[na:] = np.linspace(1, 0, n - na) ** decay_pow
    return e


def make(kind, dur, rng):
    t = t_axis(dur)
    n = len(t)
    noise = rng.standard_normal(n)
    if kind in ("whoosh", "swish"):
        peak = 0.62 if kind == "whoosh" else 0.5
        shape = np.exp(-((t / dur - peak) ** 2) / (2 * (0.18 if kind == "whoosh" else 0.12) ** 2))
        cutoff = 300 + 5200 * shape
        x = onepole_lowpass(noise, cutoff) * shape
        pan = np.linspace(-0.6, 0.6, n)
        return stereo(x, pan)
    if kind == "riser":
        prog = (t / dur) ** 2
        x = onepole_lowpass(noise, 200 + 7000 * prog) * prog
        x += 0.25 * np.sin(2 * np.pi * (180 + 600 * prog) * t) * prog
        return stereo(x)
    if kind == "hit":
        body = np.sin(2 * np.pi * (140 * np.exp(-t * 18) + 55) * t) * env_ad(n, 0.005, 3)
        crack = onepole_lowpass(noise, 4000) * env_ad(n, 0.002, 8)
        return stereo(body + 0.6 * crack)
    if kind == "boom":
        f = 60 * np.exp(-t * 2.5) + 32
        phase = 2 * np.pi * np.cumsum(f) / SR
        x = np.sin(phase) * env_ad(n, 0.01, 2.2) + 0.3 * onepole_lowpass(noise, 250) * env_ad(n, 0.005, 4)
        return stereo(x)
    if kind in ("click", "tick"):
        f = 2400 if kind == "click" else 3800
        x = np.sin(2 * np.pi * f * t) * np.exp(-t * (180 if kind == "click" else 260))
        x += 0.3 * noise * np.exp(-t * 600)
        return stereo(x)
    if kind == "pop":
        f = 900 * np.exp(-t * 25) + 300
        phase = 2 * np.pi * np.cumsum(f) / SR
        return stereo(np.sin(phase) * env_ad(n, 0.01, 3))
    if kind == "shimmer":
        x = np.zeros(n)
        for k, f in enumerate([1760, 2217, 2637, 3520, 4434]):
            x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t * (2.5 + k * 0.7)) / (k + 1)
        x *= 0.5 * (1 + 0.3 * np.sin(2 * np.pi * 7 * t))
        return stereo(x * env_ad(n, 0.05, 1.2), np.sin(2 * np.pi * 0.8 * t) * 0.5)
    if kind == "glitch":
        x = np.zeros(n)
        seg = int(SR * 0.025)
        for s in range(0, n, seg):
            if rng.random() < 0.7:
                f = rng.choice([220, 440, 880, 1320, 2000])
                x[s:s + seg] = np.sign(np.sin(2 * np.pi * f * t[s:s + seg])) * rng.uniform(0.3, 1.0)
        return stereo(x * 0.6)
    if kind == "typing":
        x = np.zeros(n)
        pos = 0.0
        while pos < dur - 0.03:
            i = int(pos * SR)
            m = min(n - i, int(0.03 * SR))
            tt = np.arange(m) / SR
            x[i:i + m] += (np.sin(2 * np.pi * rng.uniform(1800, 3200) * tt) * 0.5 + rng.standard_normal(m) * 0.5) * np.exp(-tt * 300)
            pos += rng.uniform(0.07, 0.16)
        return stereo(x)
    raise SystemExit(f"Unknown kind '{kind}'. Use --list.")


def stereo(x, pan=None):
    if pan is None:
        pan = np.zeros_like(x)
    left = x * np.cos((pan + 1) * np.pi / 4)
    right = x * np.sin((pan + 1) * np.pi / 4)
    return np.stack([left, right], axis=1)


def finish(a):
    a = a - a.mean(axis=0)  # remove DC offset
    n = len(a)
    fade = min(int(0.004 * SR), n // 4)
    if fade > 0:
        a[:fade] *= np.linspace(0, 1, fade)[:, None]
    tail = min(int(0.03 * SR), n // 3)
    if tail > 0:
        a[-tail:] *= np.linspace(1, 0, tail)[:, None]
    peak = np.max(np.abs(a)) or 1.0
    a = a * (10 ** (-3 / 20) / peak)
    # keep dense sounds (e.g. glitch) from being much louder than the rest: cap RMS at -16 dBFS
    rms = np.sqrt(np.mean(np.square(a))) or 1e-9
    cap = 10 ** (-16 / 20)
    return a * (cap / rms) if rms > cap else a


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind")
    ap.add_argument("--dur", type=float)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out")
    ap.add_argument("--pack", help="write one of each kind into this folder")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, d in DEFAULT_DUR.items():
            print(f"{k:8} default {d}s")
        return
    if a.pack:
        os.makedirs(a.pack, exist_ok=True)
        for k, d in DEFAULT_DUR.items():
            p = os.path.join(a.pack, f"{k}.wav")
            if os.path.exists(p):
                print("skip existing", p)
                continue
            write_wav(p, finish(make(k, d, np.random.default_rng(a.seed))), SR)
            print("wrote", p)
        return
    if not (a.kind and a.out):
        ap.error("--kind and --out are required (or use --pack / --list)")
    if os.path.exists(a.out):
        sys.exit(f"Refusing to overwrite {a.out}; choose a new name.")
    dur = a.dur or DEFAULT_DUR.get(a.kind, 0.5)
    write_wav(a.out, finish(make(a.kind, dur, np.random.default_rng(a.seed))), SR)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
