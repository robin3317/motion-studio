#!/usr/bin/env python3
"""Apply an EDL (from silence_cuts.py) to footage: write the cut video and re-time a word transcript.

Usage:
    python apply_edl.py plan/edl.json --out assets/footage/cut-v1.mp4 [--words plan/words.json --words-out plan/words_cut.json]

- Video is re-encoded (H.264 CRF 16, AAC 192k) with frame-accurate cuts and 10 ms audio fades at each cut
  so joins don't click. The source file is never modified; existing outputs are never overwritten.
- --words: JSON list of {"text", "start", "end"} (seconds, source timeline). Words that fall inside removed
  ranges are dropped; the rest are shifted onto the new timeline.
Use the cut video as ONE clip in the HyperFrames composition (simplest and most robust), or place each
EDL segment as its own clip with media offsets if the edit needs per-segment treatment.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import dump, ffprobe_json, need, run  # noqa: E402


def retime(words, keep):
    # Match on the word's START: speech recognisers often stretch a sentence's last word over the
    # following pause, so its midpoint can land inside a removed silence even though it was spoken.
    out = []
    for w in words:
        anchor = w["start"] + 0.02
        for k in keep:
            if k["in"] <= anchor < k["out"]:
                shift = k["at"] - k["in"]
                out.append({**w, "start": round(max(k["at"], w["start"] + shift), 3),
                            "end": round(min(k["at"] + (k["out"] - k["in"]), w["end"] + shift), 3)})
                break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--words")
    ap.add_argument("--words-out")
    a = ap.parse_args()
    with open(a.edl, encoding="utf-8") as f:
        edl = json.load(f)
    keep = edl["keep"]
    src = edl["source"]
    if not os.path.isabs(src) and not os.path.exists(src):
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(a.edl))), src)
    if os.path.exists(a.out):
        sys.exit(f"Refusing to overwrite {a.out}")
    has_audio = any(s.get("codec_type") == "audio" for s in ffprobe_json(src)["streams"])

    parts, labels = [], ""
    for i, k in enumerate(keep):
        d = k["out"] - k["in"]
        parts.append(f"[0:v]trim=start={k['in']}:end={k['out']},setpts=PTS-STARTPTS[v{i}]")
        if has_audio:
            fade = min(0.01, d / 4)
            parts.append(f"[0:a]atrim=start={k['in']}:end={k['out']},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d={fade},afade=t=out:st={max(0, d - fade)}:d={fade}[a{i}]")
            labels += f"[v{i}][a{i}]"
        else:
            labels += f"[v{i}]"
    n = len(keep)
    parts.append(f"{labels}concat=n={n}:v=1:a={1 if has_audio else 0}[v]" + ("[a]" if has_audio else ""))
    cmd = [need("ffmpeg"), "-v", "error", "-i", src, "-filter_complex", ";".join(parts), "-map", "[v]"]
    if has_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", a.out]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    run(cmd)
    print(f"wrote {a.out} ({edl['result_duration']} s from {edl['duration']} s, {n} segments)")

    if a.words:
        with open(a.words, encoding="utf-8") as f:
            words = json.load(f)
        out = retime(words, keep)
        target = a.words_out or os.path.splitext(a.words)[0] + "_cut.json"
        if os.path.exists(target):
            sys.exit(f"Refusing to overwrite {target}")
        dump(out, target)
        print(f"wrote {target}: {len(out)} of {len(words)} words kept")


if __name__ == "__main__":
    main()
