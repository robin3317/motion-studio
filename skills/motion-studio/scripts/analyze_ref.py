#!/usr/bin/env python3
"""Study a reference video: what cuts when, how the first seconds hook, how sound and picture line up.

Usage (project folder as working directory, or anywhere with --out):
    python analyze_ref.py path/to/reference.mp4 [--out DIR] [--window 15] [--hook 3] [--cut-threshold 0.3]

Writes into a new folder (renders/checks/ref-<name>-vN in a project):
    recipe.md          the numbers, the shot table to fill in by eye, and what to look at
    analysis.json      the same numbers for scripts
    hook-N.jpg         EVERY frame of the first --hook seconds, 30 frames per sheet, time on each frame
    sheet-<a>-<b>s.jpg one sheet per --window seconds, 2 frames per second, time on each frame
    spectrum-<a>-<b>s.png  the sound of each window as a picture (when the file has audio)

It downloads nothing and uses only FFmpeg and numpy. A reference is for learning rhythm, structure and
craft. Never copy its footage, music, logo or wording into the user's video (critical rule 3).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _common import decode_audio, ffprobe_json, measure_loudness, need, new_check_dir  # noqa: E402

SHEET_FRAMES = 30


def font_arg():
    for p in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
              "/usr/share/fonts/TTF/DejaVuSans.ttf"):
        if os.path.isfile(p):
            return "fontfile='" + p.replace("\\", "/").replace(":", "\\:") + "':"
    return ""   # FFmpeg's default font, if it has one


def ffmpeg(args, timeout=600):
    return subprocess.run([need("ffmpeg"), "-hide_banner", "-nostdin", "-v", "error", "-y"] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def stamp(wide):
    """Scale to a tile and write the frame's own time in its corner."""
    scale = "scale=320:-2" if wide else "scale=-2:320"
    return (scale + ",drawbox=x=0:y=0:w=96:h=22:color=black@0.65:t=fill,"
            "drawtext=" + font_arg() + "text='%{pts\\:hms}':x=4:y=4:fontsize=14:fontcolor=white")


def sheets(video, out, name, start, length, fps, wide, max_sheets):
    """Tiled sheets of [start, start+length). fps=None keeps every frame. Returns the files written."""
    grid = "6x5" if wide else "10x3"
    vf = (f"fps={fps}," if fps else "") + stamp(wide) + f",tile={grid}:padding=4:margin=4:color=0x1a1a1a"
    pattern = os.path.join(out, name + "-%02d.jpg")
    p = ffmpeg(["-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-copyts", "-i", video, "-an", "-vf", vf,
                "-frames:v", str(max_sheets), "-q:v", "3", pattern])
    files = sorted(f for f in os.listdir(out) if f.startswith(name + "-") and f.endswith(".jpg"))
    if not files and p.stderr:
        print("  sheet failed: " + p.stderr.strip().splitlines()[-1][:200], file=sys.stderr)
    return files


def scene_cuts(video, threshold, duration):
    p = subprocess.run([need("ffmpeg"), "-hide_banner", "-nostdin", "-i", video, "-an",
                        "-vf", f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    cuts = [round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", p.stderr)]
    out = []
    for t in cuts:                      # a flash or a fast wipe trips the detector on several frames in a row
        if 0.05 < t < duration - 0.05 and (not out or t - out[-1] >= 0.2):
            out.append(t)
    return out


def audio_facts(video, duration):
    import numpy as np
    import beats
    sr = 22050
    mono = decode_audio(video, sr=sr, channels=1)[:, 0]
    if len(mono) < sr // 2 or float(np.abs(mono).max()) < 1e-4:
        return None
    env = beats.onset_envelope(mono)
    fps = sr / beats.HOP
    thr = env.mean() + 1.5 * env.std()
    onsets = []
    for i in range(2, len(env) - 2):
        t = round(i / fps, 3)
        if env[i] > thr and env[i] == env[i - 2:i + 3].max() and (not onsets or t - onsets[-1] >= 0.12):
            onsets.append(t)
    bpm = None
    if duration >= 6 and len(onsets) >= 8:      # a tempo needs a rhythm to stand on
        b, _ = beats.estimate_bpm(env, fps, 70, 180)
        bpm = round(float(b), 1) if math.isfinite(b) and 60 <= b <= 200 else None
    n = max(1, int(len(mono) / sr))
    rms = []
    for s in range(n):
        chunk = mono[s * sr:(s + 1) * sr]
        rms.append(round(float(20 * np.log10(max(1e-6, np.sqrt(np.mean(chunk ** 2))))), 1))
    lufs, peak = measure_loudness(video)
    return {"onsets": onsets, "bpm_estimate": bpm, "rms_db_per_second": rms, "integrated_lufs": lufs, "true_peak_dbtp": peak}


def near(t, times, tol):
    return any(abs(t - x) <= tol for x in times)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", help="output folder (default: a new renders/checks/ref-<name>-vN, or next to the video)")
    ap.add_argument("--window", type=float, default=15.0, help="seconds per overview sheet (default 15)")
    ap.add_argument("--hook", type=float, default=3.0, help="seconds at the start captured frame by frame (default 3)")
    ap.add_argument("--cut-threshold", type=float, default=0.3, help="scene-change sensitivity, 0.1 (many cuts) to 0.5 (few)")
    a = ap.parse_args()

    video = os.path.abspath(a.video)
    if not os.path.isfile(video):
        sys.exit(f"ANALYSIS_FAILED file not found: {video}")
    info = ffprobe_json(video)
    vs = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    if not vs:
        sys.exit("ANALYSIS_FAILED no video stream in this file")
    has_audio = any(s.get("codec_type") == "audio" for s in info["streams"])
    duration = float(info["format"].get("duration") or vs.get("duration") or 0)
    if duration <= 0:
        sys.exit("ANALYSIS_FAILED could not read the duration")
    num, den = (vs.get("avg_frame_rate") or "30/1").split("/")
    fps = round(float(num) / float(den or 1), 3) if float(den or 1) else 30.0
    w, h = int(vs["width"]), int(vs["height"])
    wide = w >= h
    stem = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(video))[0].lower()).strip("-")[:40] or "ref"

    if a.out:
        out = os.path.abspath(a.out)
        os.makedirs(out, exist_ok=True)
    elif os.path.isdir("renders") or os.path.isfile("PROGRESS.md"):
        out = new_check_dir(os.getcwd(), "ref-" + stem)
    else:
        n = 1
        while os.path.exists(os.path.join(os.path.dirname(video), f"{stem}-analysis-v{n}")):
            n += 1
        out = os.path.join(os.path.dirname(video), f"{stem}-analysis-v{n}")
        os.makedirs(out)

    print(f"[ref] {os.path.basename(video)}: {duration:.1f} s, {w}x{h}, {fps:g} fps, audio {'yes' if has_audio else 'NO'}", flush=True)
    hook_len = min(a.hook, duration)
    hook_frames = int(round(hook_len * fps))
    hook_files = sheets(video, out, "hook", 0, hook_len, None, wide, math.ceil(hook_frames / SHEET_FRAMES))
    print(f"[ref] hook: {hook_frames} frames on {len(hook_files)} sheet(s)", flush=True)

    over = []
    t = 0.0
    while t < duration - 0.05:
        length = min(a.window, duration - t)
        name = f"sheet-{int(round(t))}-{int(round(t + length))}s"
        over += sheets(video, out, name, t, length, 2, wide, 1)
        if has_audio:
            png = os.path.join(out, f"spectrum-{int(round(t))}-{int(round(t + length))}s.png")
            ffmpeg(["-ss", f"{t:.3f}", "-t", f"{length:.3f}", "-i", video, "-lavfi",
                    "showspectrumpic=s=1500x420:legend=0:scale=log", "-frames:v", "1", png])
        t += a.window
    print(f"[ref] overview: {len(over)} sheet(s) of {a.window:g} s", flush=True)

    cuts = scene_cuts(video, a.cut_threshold, duration)
    edges = [0.0] + cuts + [round(duration, 3)]
    shots = [{"n": i + 1, "start": edges[i], "end": edges[i + 1], "length": round(edges[i + 1] - edges[i], 3)}
             for i in range(len(edges) - 1)]
    audio = audio_facts(video, duration) if has_audio else None
    on_sound = None
    if audio and cuts:
        on_sound = round(100 * sum(near(c, audio["onsets"], 0.1) for c in cuts) / len(cuts))
    lengths = sorted(s["length"] for s in shots)
    facts = {"file": os.path.basename(video), "duration": round(duration, 3), "fps": fps, "width": w, "height": h,
             "has_audio": has_audio, "cuts": cuts, "shots": shots,
             "shot_length": {"count": len(shots), "median": lengths[len(lengths) // 2], "shortest": lengths[0], "longest": lengths[-1]},
             "cuts_within_0.1s_of_a_sound_onset_percent": on_sound, "audio": audio,
             "sheets": {"hook": hook_files, "overview": over}}
    with open(os.path.join(out, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=2)
        f.write("\n")

    L = [f"# Reference recipe: {os.path.basename(video)}", "",
         "Numbers come from the file. The **bold blanks** are for you: open the sheets and fill them in.",
         "Learn the rhythm, structure and craft. Never copy its footage, music, logo or wording (critical rule 3).", "",
         "## The film",
         f"- {duration:.1f} s, {w}×{h}, {fps:g} fps, audio: {'yes' if has_audio else 'none'}",
         f"- {len(shots)} shots. Shot length: median {facts['shot_length']['median']:.2f} s, shortest {lengths[0]:.2f} s, longest {lengths[-1]:.2f} s"]
    if audio:
        tempo = f"about {audio['bpm_estimate']} BPM (estimate; confirm by ear)" if audio["bpm_estimate"] else "no steady tempo found"
        L.append(f"- Sound: {tempo}, {len(audio['onsets'])} strong onsets, "
                 f"{audio['integrated_lufs']} LUFS integrated, true peak {audio['true_peak_dbtp']} dBTP")
        if on_sound is not None:
            L.append(f"- **{on_sound}% of the cuts land within 0.1 s of a sound onset.** Above about 70%: the edit is cut to the sound, so cut yours to beats or hits too")
    L += ["", f"## The hook (first {hook_len:g} s, every frame: {', '.join(hook_files) or 'no sheets'})",
          "- Frame 0 shows: **…**",
          "- First text readable at: **… s**   First cut at: " + (f"{cuts[0]:.2f} s" if cuts else "no cut found"),
          "- What moves in the first second, and how fast (frames from start to rest): **…**", "",
          "## Shots (look at " + (", ".join(over) or "the sheets") + ")", "",
          "| # | Start | Length | On screen (object, layout) | Text (words, size, accent) | Motion in / hold / out | Transition out | Sound at the cut |",
          "|---|---|---|---|---|---|---|---|"]
    for s in shots[:80]:
        hit = "" if not audio or s["n"] == 1 else ("onset" if near(s["start"], audio["onsets"], 0.1) else "–")
        L.append(f"| {s['n']} | {s['start']:.2f} | {s['length']:.2f} | **…** | **…** | **…** | **…** | {hit} |")
    if len(shots) > 80:
        L.append(f"| … | | | {len(shots) - 80} more shots in analysis.json | | | | |")
    L += ["", "## What to take from it (fill in, 3 to 6 lines)",
          "- Pace: **…** (shot length, where it speeds up or holds)",
          "- Type: **…** (how many words per line, how lines enter, what marks the key word)",
          "- 3D and depth: **…** (camera moves, materials, light, what stays flat)",
          "- Colour and background rhythm: **…**",
          "- Sound design: **…** (what plays on cuts, on text, on the logo)",
          "- One thing NOT to take: **…**", "",
          "## After our first version", "Run this script on our render too, put both recipes side by side and list the gaps. That list drives the next version.", ""]
    with open(os.path.join(out, "recipe.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"ANALYSIS_DONE {len(shots)} shots, {len(hook_files)} hook sheet(s), {len(over)} overview sheet(s) | {out}")
    for fn in ["recipe.md"] + hook_files[:2] + over[:2]:
        print("  look at: " + os.path.join(out, fn))
    print("NEXT: open every sheet, then fill the bold blanks in recipe.md. Use it at S2 (pace, shots) and S3 (style).")


if __name__ == "__main__":
    main()
