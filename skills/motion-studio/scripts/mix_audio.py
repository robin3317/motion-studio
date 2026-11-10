#!/usr/bin/env python3
"""Mix voiceover, music and SFX into one master WAV with automatic ducking and loudness normalization.

Usage:
    python mix_audio.py --plan audio/mix_plan.json --out audio/mix.wav

Plan (all times in seconds, gains in dB; only "duration" is required):
{
  "duration": 24,
  "vo":    [{"file": "audio/vo/vo.wav", "start": 0.3, "gain_db": 0}],
  "music": {"file": "audio/music/track.mp3", "start": 0, "offset": 0, "gain_db": 0,
            "fade_in": 0.3, "fade_out": 1.5, "loop": false},
  "sfx":   [{"file": "audio/sfx/whoosh1.wav", "start": 2.9, "below_ref_db": 10}],
  "music_under_vo_db": 18,     # music sits this far below the voice while speech plays (15-20 recommended)
  "music_open_db": 6,          # music this far below voice level when nobody speaks (intro/outro)
  "duck_attack": 0.1, "duck_release": 0.45, "duck_preroll": 0.12,
  "target_lufs": -14,
  "true_peak": -1.5,           # ceiling of the master WAV
  "delivery_true_peak": -1.0   # ceiling after AAC encoding (what the MP4 is checked against)
}
Each SFX is scaled so its peak sits `below_ref_db` under the reference peak (voice, or music if no VO).

The script checks its own result and corrects it:
- Ducking: it measures the real music-vs-voice gap during speech. Music is rarely as even as its average
  level, so the first pass often lands a few dB short. It deepens the duck and measures again until the
  gap is at least `music_under_vo_db` - 1 (17 dB by default; never accepted below 15).
- Peaks: the master is normalized with FFmpeg loudnorm (two-pass) to `true_peak`. AAC encoding raises
  peaks, so the master is then encoded to AAC, measured, and turned down if it would pass
  `delivery_true_peak` in the final MP4.
Prints a JSON report with the measured numbers. Refuses to overwrite --out.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import db_to_gain, decode_audio, measure_loudness, need, write_wav  # noqa: E402

SR = 48000
MIN_GAP_FLOOR = 15.0   # the music is never accepted closer to the voice than this


def place(track, clip, start):
    i = int(round(start * SR))
    if i >= len(track) or i + len(clip) <= 0:
        return
    c0 = max(0, -i)
    i = max(0, i)
    n = min(len(track) - i, len(clip) - c0)
    track[i:i + n] += clip[c0:c0 + n]


def rms_db(x):
    v = np.sqrt(np.mean(np.square(x))) if len(x) else 0.0
    return 20 * np.log10(max(v, 1e-9))


def speech_mask(vo, preroll):
    """Frame-wise speech activity from the VO track (20 ms frames), returned per-sample (0/1)."""
    mono = np.abs(vo).mean(axis=1)
    hop = int(0.02 * SR)
    n = len(mono) // hop
    if n == 0:
        return np.zeros(len(vo))
    fr = np.sqrt(np.mean(np.square(mono[:n * hop].reshape(n, hop)), axis=1))
    peak = fr.max()
    if peak <= 0:
        return np.zeros(len(vo))
    thr = peak * db_to_gain(-35)
    act = (fr > thr).astype(float)
    # close gaps shorter than 250 ms, add pre-roll
    gap = int(0.25 / 0.02)
    idx = np.where(act > 0)[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if 1 < b - a <= gap:
            act[a:b] = 1
    pre = int(preroll / 0.02)
    act = np.maximum(act, np.concatenate([act[pre:], np.zeros(pre)])) if pre else act
    m = np.repeat(act, hop)
    return np.concatenate([m, np.zeros(len(vo) - len(m))])


def smooth(mask, attack, release):
    """One-pole attack/release follower on a 0..1 mask, computed at 1 ms resolution."""
    step = SR // 1000
    m = mask[::step]
    au = np.exp(-step / max(1.0, attack * SR))
    ad = np.exp(-step / max(1.0, release * SR))
    o = np.empty_like(m)
    acc = 0.0
    for i, v in enumerate(m):
        a = au if v > acc else ad
        acc = a * acc + (1 - a) * v
        o[i] = acc
    up = np.repeat(o, step)
    if len(up) < len(mask):
        up = np.pad(up, (0, len(mask) - len(up)), mode="edge")
    return up[:len(mask)]


def loudnorm(src, dst, lufs, tp):
    ff = need("ffmpeg")
    p1 = subprocess.run([ff, "-hide_banner", "-i", src, "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json",
                         "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr, re.S)
    if not m:
        raise SystemExit("loudnorm measurement failed:\n" + p1.stderr[-800:])
    meas = json.loads(m.group(0))
    af = (f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:"
          f"measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:"
          f"linear=true:print_format=json")
    p2 = subprocess.run([ff, "-hide_banner", "-y", "-i", src, "-af", af, "-ar", str(SR), "-ac", "2",
                         "-c:a", "pcm_s16le", dst], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p2.returncode != 0:
        raise SystemExit("loudnorm render failed:\n" + p2.stderr[-800:])
    m2 = re.search(r"\{[^{}]*\"output_i\"[^{}]*\}", p2.stderr, re.S)
    out = json.loads(m2.group(0)) if m2 else {}
    return {"integrated_lufs": float(out.get("output_i", "nan")), "true_peak_db": float(out.get("output_tp", "nan")),
            "normalization": out.get("normalization_type", "")}


def duck(music, mask, vo_t, speech, vo_level, plan):
    """Level the music against the voice and duck it under speech. Measures the real gap during speech
    and deepens the duck until it is big enough. Returns (ducked music, measured gap dB, passes)."""
    under = float(plan.get("music_under_vo_db", 18))
    open_gap = float(plan.get("music_open_db", 6))
    min_gap = max(MIN_GAP_FLOOR, under - 1.0)
    aim = max(under, min_gap)              # a setting below the floor is raised to it
    level = rms_db(music[music.any(axis=1)]) if music.any() else -120.0
    env = smooth(mask, plan.get("duck_attack", 0.1), plan.get("duck_release", 0.45))
    g_open = db_to_gain(vo_level - open_gap - level)
    vo_speech = rms_db(vo_t[speech])
    extra, out, gap = 0.0, music, None
    for n in range(1, 7):
        g_duck = min(g_open, db_to_gain(vo_level - under - extra - level))
        out = music * (g_open + (g_duck - g_open) * env)[:, None]
        under_speech = out[speech]
        if not under_speech.any():
            return out, None, n            # no music while anyone speaks
        gap = vo_speech - rms_db(under_speech)
        if gap >= min_gap:
            return out, gap, n
        extra += (aim - gap) + 0.3         # aim for the asked value, not just the minimum
    return out, gap, 6


def aac_true_peak(wav):
    """True peak the mix will have after AAC encoding (the MP4's audio codec)."""
    with tempfile.TemporaryDirectory() as td:
        m4a = os.path.join(td, "check.m4a")
        p = subprocess.run([need("ffmpeg"), "-hide_banner", "-v", "error", "-y", "-i", wav, "-c:a", "aac",
                            "-b:a", "192k", m4a], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            return None
        return measure_loudness(m4a)[1]


def trim_gain(path, db):
    """Turn the finished master down by `db` (a plain gain change), in place."""
    tmp = path + ".trim.wav"
    p = subprocess.run([need("ffmpeg"), "-hide_banner", "-v", "error", "-y", "-i", path, "-af", f"volume=-{db:.2f}dB",
                        "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", tmp],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise SystemExit("peak trim failed:\n" + p.stderr[-800:])
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"Refusing to overwrite {a.out}; use a new version name (e.g. mix_v2.wav).")
    with open(a.plan, encoding="utf-8") as f:
        plan = json.load(f)
    base = os.path.dirname(os.path.abspath(a.plan))
    proj = os.path.dirname(base) if os.path.basename(base) in ("audio", "plan") else base

    def path(p):
        if os.path.isabs(p):
            return p
        for root in (proj, base, os.getcwd()):
            if os.path.exists(os.path.join(root, p)):
                return os.path.join(root, p)
        raise SystemExit(f"File not found: {p}")

    n = int(round(float(plan["duration"]) * SR))
    vo_t, mu_t, sx_t = (np.zeros((n, 2), dtype=np.float64) for _ in range(3))
    gap, duck_passes = None, 0

    vo_cut = 0.0
    for v in plan.get("vo", []):
        clip = decode_audio(path(v["file"]), SR) * db_to_gain(v.get("gain_db", 0))
        vo_cut = max(vo_cut, v.get("start", 0) + len(clip) / SR - float(plan["duration"]))
        place(vo_t, clip, v.get("start", 0))

    mask = speech_mask(vo_t, plan.get("duck_preroll", 0.12)) if np.any(vo_t) else np.zeros(n)
    speech = mask > 0.5
    vo_level = rms_db(vo_t[speech]) if speech.any() else None

    music_cfg = plan.get("music")
    if music_cfg:
        mus = decode_audio(path(music_cfg["file"]), SR)
        off = int(music_cfg.get("offset", 0) * SR)
        mus = mus[off:]
        start = music_cfg.get("start", 0)
        need_len = n - int(start * SR)
        if music_cfg.get("loop") and len(mus) < need_len and len(mus) > 0:
            mus = np.tile(mus, (int(np.ceil(need_len / len(mus))), 1))
        mus = mus[:max(0, need_len)].astype(np.float64) * db_to_gain(music_cfg.get("gain_db", 0))
        fi, fo = int(music_cfg.get("fade_in", 0.3) * SR), int(music_cfg.get("fade_out", 1.5) * SR)
        if fi and len(mus) > fi:
            mus[:fi] *= np.linspace(0, 1, fi)[:, None]
        if fo and len(mus) > fo:
            mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
        place(mu_t, mus, start)
        if vo_level is not None:
            mu_t, gap, duck_passes = duck(mu_t, mask, vo_t, speech, vo_level, plan)

    ref_peak = np.max(np.abs(vo_t)) if np.any(vo_t) else (np.max(np.abs(mu_t)) if np.any(mu_t) else 0.5)
    for s in plan.get("sfx", []):
        clip = decode_audio(path(s["file"]), SR).astype(np.float64)
        pk = np.max(np.abs(clip)) or 1.0
        clip *= (ref_peak * db_to_gain(-float(s.get("below_ref_db", 10)))) / pk
        place(sx_t, clip, s.get("start", 0))

    mix = vo_t + mu_t + sx_t
    pk = np.max(np.abs(mix)) or 1.0
    if pk > 0.98:
        mix *= 0.98 / pk  # headroom before loudnorm

    report = {"out": a.out, "duration": plan["duration"]}
    if gap is not None:
        under = float(plan.get("music_under_vo_db", 18))
        report["music_below_voice_db_during_speech"] = round(float(gap), 1)
        report["music_gap_ok"] = bool(gap >= max(MIN_GAP_FLOOR, under - 1.0))
        report["duck_passes"] = duck_passes
    target_tp = float(plan.get("true_peak", -1.5))
    delivery_tp = float(plan.get("delivery_true_peak", -1.0))
    with tempfile.TemporaryDirectory() as td:
        pre = os.path.join(td, "premaster.wav")
        write_wav(pre, mix, SR)
        report.update(loudnorm(pre, a.out, plan.get("target_lufs", -14), target_tp))
    # Check the result the way it will be delivered: AAC raises peaks. Turn the master down if needed.
    trimmed = 0.0
    for _ in range(3):
        _, wav_tp = measure_loudness(a.out)
        aac_tp = aac_true_peak(a.out)
        over = max((wav_tp - target_tp) if wav_tp is not None else 0.0,
                   (aac_tp - delivery_tp) if aac_tp is not None else 0.0)
        if over <= 0.05:
            break
        trim_gain(a.out, over + 0.1)
        trimmed += over + 0.1
    lufs, wav_tp = measure_loudness(a.out)
    aac_tp = aac_true_peak(a.out)
    report.update({"integrated_lufs": lufs, "true_peak_db": wav_tp, "aac_true_peak_db": aac_tp,
                   "peak_trim_db": round(trimmed, 2),
                   "peak_ok": bool(aac_tp is not None and aac_tp <= delivery_tp + 0.05)})
    if vo_cut > 0.05:
        report["vo_cut_off_s"] = round(vo_cut, 2)
    print(json.dumps(report, indent=2))
    if report.get("music_gap_ok") is False:
        print("WARNING: the music is still too close to the voice. Raise music_under_vo_db, or use a calmer "
              "passage of the track (music.offset) or another track, then mix again to a new file name. "
              "(music.gain_db doesn't help: with a voiceover the music is levelled against the voice.)",
              file=sys.stderr)
    if vo_cut > 0.05:
        print(f"WARNING: the voiceover runs {vo_cut:.2f} s past \"duration\" and was cut off there. "
              "Make the film longer or start the voiceover earlier.", file=sys.stderr)


if __name__ == "__main__":
    main()
