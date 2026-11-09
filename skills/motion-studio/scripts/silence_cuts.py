#!/usr/bin/env python3
"""Build an edit decision list (EDL) that removes long silences (and optional extra ranges) from footage.

Usage:
    python silence_cuts.py assets/footage/a.mp4 [--threshold -35] [--min 0.6] [--pad 0.15]
                           [--cut-ranges plan/filler_cuts.json] --out plan/edl.json

--threshold  dBFS below which audio counts as silence, or "auto" (default): measured per recording as
             noise floor + 40% of the gap to speech level, so quiet and noisy recordings both work
--min        only silences longer than this (s) are removed
--pad        seconds of silence kept on each side of speech so words aren't clipped
--cut-ranges JSON list of [start, end] pairs to remove as well (e.g. filler words from the transcript)

Output EDL: {"source": ..., "duration": ..., "keep": [{"in": s, "out": e, "at": t}, ...],
             "removed_seconds": x, "result_duration": y}
"at" is where each kept segment starts on the new timeline. The source file is never modified.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import decode_audio, dump, ffprobe_json, need, run  # noqa: E402


def auto_threshold(path):
    """Noise floor (10th pct) and speech level (90th pct) of 50 ms RMS frames -> threshold in dBFS."""
    import numpy as np
    mono = decode_audio(path, sr=16000, channels=1)[:, 0]
    hop = 800
    n = len(mono) // hop
    if n < 10:
        return -35.0, None, None
    rms = np.sqrt(np.mean(np.square(mono[:n * hop].reshape(n, hop)), axis=1)) + 1e-9
    db = 20 * np.log10(rms)
    noise, speech = float(np.percentile(db, 10)), float(np.percentile(db, 90))
    noise = max(noise, -70.0)  # digital silence would otherwise drag the threshold to -120 dB
    return round(noise + 0.4 * (speech - noise), 1), round(noise, 1), round(speech, 1)


def detect_silence(path, thr, min_len):
    p = run([need("ffmpeg"), "-hide_banner", "-nostats", "-i", path, "-vn", "-af",
             f"silencedetect=noise={thr}dB:d={min_len}", "-f", "null", "-"], check=False)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    return starts, ends


def merge(ranges):
    out = []
    for s, e in sorted(ranges):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--threshold", default="auto", help='dBFS number or "auto"')
    ap.add_argument("--min", type=float, default=0.6)
    ap.add_argument("--pad", type=float, default=0.15)
    ap.add_argument("--cut-ranges")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    info = ffprobe_json(a.source)
    duration = float(info["format"]["duration"])
    if not any(s.get("codec_type") == "audio" for s in info["streams"]):
        sys.exit("Source has no audio stream; silence detection needs audio.")

    noise = speech = None
    if str(a.threshold).lower() == "auto":
        thr, noise, speech = auto_threshold(a.source)
    else:
        thr = float(a.threshold)
    starts, ends = detect_silence(a.source, thr, a.min)
    if len(ends) < len(starts):  # silence runs to the end
        ends.append(duration)
    cuts = []
    for s, e in zip(starts, ends):
        s2 = max(0.0, s) + (a.pad if s > 0 else 0)
        e2 = e - (a.pad if e < duration else 0)
        if e2 - s2 > 0.05:
            cuts.append([s2, e2])
    if a.cut_ranges:
        with open(a.cut_ranges, encoding="utf-8") as f:
            extra = json.load(f)
        cuts += [[float(s), float(e)] for s, e in extra if float(e) > float(s)]
    cuts = merge(cuts)

    keep, pos, at = [], 0.0, 0.0
    for s, e in cuts:
        if s - pos > 0.04:
            keep.append({"in": round(pos, 3), "out": round(s, 3), "at": round(at, 3)})
            at += s - pos
        pos = max(pos, e)
    if duration - pos > 0.04:
        keep.append({"in": round(pos, 3), "out": round(duration, 3), "at": round(at, 3)})
        at += duration - pos

    edl = {"source": a.source, "duration": round(duration, 3), "threshold_db": thr, "noise_floor_db": noise, "speech_level_db": speech,
           "min_silence": a.min, "pad": a.pad, "keep": keep,
           "removed_seconds": round(duration - at, 3), "result_duration": round(at, 3)}
    if os.path.exists(a.out):
        sys.exit(f"Refusing to overwrite {a.out}; use a new name.")
    dump(edl, a.out)
    print(f"threshold {thr} dBFS (noise {noise}, speech {speech})")
    print(f"wrote {a.out}: {len(keep)} segments, removed {edl['removed_seconds']} s, "
          f"new duration {edl['result_duration']} s (source {edl['duration']} s)")


if __name__ == "__main__":
    main()
