#!/usr/bin/env python3
"""Estimate tempo (BPM) and beat times of a music track (numpy + ffmpeg only).

Usage:
    python beats.py audio/music/track.mp3 [--out plan/beats_music.json] [--min-bpm 70 --max-bpm 180]

Output JSON: {"bpm": 120.2, "beats": [0.51, 1.01, ...], "bars": [every 4th beat from the first, approximate downbeats], "duration": 92.4}
Estimates are good for cutting on beats; confirm by ear for important hits.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import decode_audio, dump  # noqa: E402

SR = 22050
HOP = 512


def onset_envelope(mono):
    win = 2048
    n_frames = 1 + max(0, (len(mono) - win) // HOP)
    window = np.hanning(win)
    frames = np.lib.stride_tricks.as_strided(
        mono, shape=(n_frames, win), strides=(mono.strides[0] * HOP, mono.strides[0]))
    mag = np.log1p(np.abs(np.fft.rfft(frames * window, axis=1)) * 10)
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, mode="same")  # remove slow trend
    return np.maximum(flux, 0)


def estimate_bpm(env, fps, lo, hi):
    env = env - env.mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    lags = np.arange(len(ac))
    bpm_axis = 60.0 * fps / np.maximum(lags, 1)
    mask = (bpm_axis >= lo) & (bpm_axis <= hi)
    # mild preference around 120 BPM to resolve half/double ambiguity
    weight = np.exp(-0.5 * (np.log2(bpm_axis / 120.0) / 0.9) ** 2)
    score = np.where(mask, ac * weight, -np.inf)
    lag = int(np.argmax(score))
    # parabolic interpolation for a fractional lag (finer BPM)
    frac = float(lag)
    if 1 <= lag < len(ac) - 1:
        y0, y1, y2 = ac[lag - 1], ac[lag], ac[lag + 1]
        denom = y0 - 2 * y1 + y2
        if denom != 0:
            frac = lag + 0.5 * (y0 - y2) / denom
    return 60.0 * fps / frac, frac


def track_beats(env, period):
    """Pick the grid phase with the most onset energy, then snap each beat to a local peak."""
    p_int = max(1, int(round(period)))
    best_phase, best = 0, -1.0
    for ph in range(p_int):
        idx = np.round(np.arange(ph, len(env), period)).astype(int)
        idx = idx[idx < len(env)]
        s = env[idx].sum()
        if s > best:
            best, best_phase = s, ph
    beats = []
    tol = max(1, p_int // 8)
    for c in np.arange(best_phase, len(env), period):
        c = int(round(c))
        lo, hi = max(0, c - tol), min(len(env), c + tol + 1)
        beats.append(lo + int(np.argmax(env[lo:hi])))
    return beats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--out")
    ap.add_argument("--min-bpm", type=float, default=70)
    ap.add_argument("--max-bpm", type=float, default=180)
    a = ap.parse_args()
    mono = decode_audio(a.audio, sr=SR, channels=1)[:, 0].astype(np.float64)
    if len(mono) < SR * 3:
        sys.exit("Track too short for beat analysis (< 3 s).")
    env = onset_envelope(mono)
    fps = SR / HOP
    bpm, lag = estimate_bpm(env, fps, a.min_bpm, a.max_bpm)
    # +half window: STFT frames are indexed by their start, onsets sit near the window centre
    beats = [round((b * HOP + 1024) / SR, 3) for b in track_beats(env, lag)]
    result = {"file": os.path.basename(a.audio), "bpm": round(bpm, 1), "beats": beats,
              "bars": beats[::4], "duration": round(len(mono) / SR, 3)}
    text = dump(result, a.out)
    print(text if not a.out else f"wrote {a.out}  (bpm {result['bpm']}, {len(beats)} beats)")


if __name__ == "__main__":
    main()
