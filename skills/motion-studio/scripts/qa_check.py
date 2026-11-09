#!/usr/bin/env python3
"""Measured QA checks for a rendered video. Visual review is still required (see references/qa.md).

Usage:
    python qa_check.py renders/acme-9x16-v1.mp4 --expect-format 9:16 [--expect-duration 24]
                       [--fps 30] [--lufs -14] [--no-audio-ok] [--sheet renders/previews/sheet.png]

Checks: resolution/aspect, fps, duration (±0.1 s), H.264 + yuv420p, AAC audio, integrated loudness
(±1 LU), true peak (≤ -1 dBTP + 0.2 tolerance), long silences, black frames at start/end
(a deliberately near-black opening can flag; confirm visually).
--sheet also writes a contact sheet (2 frames/s) for visual inspection.
Exit code 0 = all measured checks pass, 1 = something failed.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ffprobe_json, need, run  # noqa: E402

FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}


def fps_of(stream):
    num, den = stream.get("avg_frame_rate", "0/1").split("/")
    return float(num) / float(den) if float(den) else 0.0


def loudness(path):
    p = run([need("ffmpeg"), "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
             "-f", "null", "-"], check=False)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    return (float(i.group(1)) if i else None, float(tp.group(1)) if tp and tp.group(1) != "-inf" else None)


def silences(path, min_len=1.5):
    p = run([need("ffmpeg"), "-hide_banner", "-nostats", "-i", path, "-vn", "-af",
             f"silencedetect=noise=-50dB:d={min_len}", "-f", "null", "-"], check=False)
    return [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", p.stderr)]


def black_edges(path, duration):
    p = run([need("ffmpeg"), "-hide_banner", "-nostats", "-i", path, "-vf",
             "blackdetect=d=0.1:pix_th=0.05", "-an", "-f", "null", "-"], check=False)
    spans = [(float(s), float(e)) for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", p.stderr)]
    issues = []
    for s, e in spans:
        if s <= 0.05:
            issues.append(f"black frames at start ({s:.2f}-{e:.2f}s)")
        if e >= duration - 0.05:
            issues.append(f"black frames at end ({s:.2f}-{e:.2f}s)")
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--expect-format", choices=FORMATS.keys())
    ap.add_argument("--expect-duration", type=float)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--no-audio-ok", action="store_true", help="silent video is intended")
    ap.add_argument("--sheet", help="write a contact sheet PNG here")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    info = ffprobe_json(a.video)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    results = []

    def check(name, ok, detail):
        results.append({"check": name, "ok": bool(ok), "detail": detail})

    if not v:
        sys.exit("No video stream.")
    w, h = int(v["width"]), int(v["height"])
    if a.expect_format:
        ew, eh = FORMATS[a.expect_format]
        check("resolution", (w, h) == (ew, eh), f"{w}x{h} (expected {ew}x{eh})")
    else:
        check("resolution", True, f"{w}x{h}")
    f = fps_of(v)
    check("fps", abs(f - a.fps) < 0.01, f"{f:.3f} (expected {a.fps})")
    if a.expect_duration:
        check("duration", abs(dur - a.expect_duration) <= 0.1, f"{dur:.3f}s (expected {a.expect_duration}s ±0.1)")
    else:
        check("duration", True, f"{dur:.3f}s")
    check("video codec", v.get("codec_name") == "h264", v.get("codec_name"))
    check("pixel format", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt"))

    if au:
        check("audio codec", au.get("codec_name") == "aac", au.get("codec_name"))
        i, tp = loudness(a.video)
        check("loudness", i is not None and abs(i - a.lufs) <= 1.0, f"{i} LUFS (target {a.lufs} ±1)")
        check("true peak", tp is not None and tp <= -0.8, f"{tp} dBTP (max -1)")
        gaps = silences(a.video)
        check("no long silences", not gaps, "none" if not gaps else f"silence ≥1.5 s starting at {gaps}")
    else:
        check("audio present", a.no_audio_ok, "no audio stream" + (" (intended)" if a.no_audio_ok else ""))

    edges = black_edges(a.video, dur)
    check("no black start/end", not edges, "; ".join(edges) or "clean")

    if a.sheet:
        os.makedirs(os.path.dirname(os.path.abspath(a.sheet)) or ".", exist_ok=True)
        cols = 6 if w >= h else 8
        rows = max(1, min(6, int(dur * 2 / cols) + 1))
        run([need("ffmpeg"), "-v", "error", "-y", "-i", a.video, "-vf",
             f"fps=2,scale={480 if w >= h else 270}:-1,tile={cols}x{rows}", "-frames:v", "1", a.sheet])
        check("contact sheet", os.path.exists(a.sheet), a.sheet + " (inspect it visually)")

    ok = all(r["ok"] for r in results)
    if a.json:
        print(json.dumps({"video": a.video, "ok": ok, "results": results}, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"  [{'PASS' if r['ok'] else 'FAIL'}] {r['check']}: {r['detail']}")
        print("RESULT:", "all measured checks passed (visual review still required)" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
