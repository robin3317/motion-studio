#!/usr/bin/env python3
"""Contact sheet of a time range: see a whole move in one image, in seconds, after every scene edit.

Usage (from the project folder):
    python preview_sheet.py --scene s2                 # that scene, from storyboard.json
    python preview_sheet.py --from 3 --to 6            # any range, 8 frames per second
    python preview_sheet.py --from 3 --to 6 --fps 12   # denser, for fast moves
    python preview_sheet.py --at 0,2.5,19.5            # exact moments only
    python preview_sheet.py --scene s6 --zoom ".pill"  # the same range, cropped to one element at 3x

It asks HyperFrames for stills (`hyperframes snapshot`), so each frame is exactly what the render will
show. HyperFrames tiles them into contact sheets of 9 frames, each labelled with its time. Everything
goes into a NEW folder renders/checks/<name>-vN; nothing is overwritten.

Then LOOK at every sheet (they are the point): framing and safe zone, overlaps, clipped or wrapped
text, borders, a pop or a gap in the easing, the frames on both sides of a cut. Fix, run it again
for the same range, repeat until clean. A single still misses what happens between stills.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import composition_dir, film_seconds, hf_run, json_from, new_check_dir, storyboard_scenes  # noqa: E402

MAX_FRAMES = 54   # 6 sheets; more than that is a render, not a check


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene", help="scene id from storyboard.json")
    ap.add_argument("--from", dest="start", type=float)
    ap.add_argument("--to", dest="end", type=float)
    ap.add_argument("--fps", type=float, default=8.0, help="frames per second of film (default 8)")
    ap.add_argument("--at", help="comma-separated times instead of a range")
    ap.add_argument("--zoom", help="CSS selector (first match) or x,y,w,h: crop to it at 3x density")
    ap.add_argument("--composition")
    ap.add_argument("--name", help="folder name under renders/checks (default: from the range)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    comp = composition_dir(a.composition)
    project = os.path.dirname(comp) if os.path.basename(comp).startswith("composition") else comp
    total = film_seconds(comp)
    args = ["snapshot", "--no-end", "--json", "--timeout", "120000"]
    if a.at:
        times = [float(x) for x in a.at.split(",") if x.strip()]
        name = a.name or "at-" + "-".join(f"{t:g}" for t in times[:4])
        args += ["--at", ",".join(f"{t:g}" for t in times)]
        frames = len(times)
    else:
        start, end = a.start, a.end
        if a.scene:
            hit = [s for s in storyboard_scenes(project) if s[0] == a.scene]
            if not hit:
                sys.exit(f"Scene '{a.scene}' not found in storyboard.json. Use --from/--to, or add the scene "
                         f"(id, start, duration) to storyboard.json.")
            start, end = hit[0][1], hit[0][1] + hit[0][2]
        if start is None or end is None:
            sys.exit("Give --scene, or --from and --to, or --at.")
        if total:
            end = min(end, total)
        if end <= start:
            sys.exit("--to must be after --from (and inside the film).")
        # stop just before the end of the range: the last instant of a scene already shows the next one
        end = max(start, end - 0.02)
        frames = max(2, min(MAX_FRAMES, int(round((end - start) * a.fps)) + 1))
        name = a.name or (a.scene or f"{start:g}-{end + 0.02:g}s")
        args += ["--range", f"{start:g},{end:g}", "--frames", str(frames)]
    if a.zoom:
        args += ["--zoom", a.zoom]
        name += "-zoom"
    out = new_check_dir(project, "sheet-" + "".join(c if c.isalnum() or c in "-_." else "-" for c in name))
    code, stdout, stderr = hf_run(comp, args + ["-o", out], timeout=900)
    rep = json_from(stdout) or {}
    sheets = rep.get("contactSheets") or []
    stills = [f["path"] for f in rep.get("frames", [])]
    if code != 0 or not stills:
        tail = [ln for ln in (stderr + "\n" + stdout).splitlines() if ln.strip()][-12:]
        sys.exit("SHEET_FAILED\n  | " + "\n  | ".join(t[:300] for t in tail))
    if a.json:
        print(json.dumps({"status": "SHEET_DONE", "folder": out, "sheets": sheets, "frames": stills}, indent=2))
        return
    print(f"SHEET_DONE {len(stills)} frames in {out}")
    for s in sheets or stills:
        print("  look at: " + s)
    if not sheets:
        print("  (one frame per file: HyperFrames makes no sheet for this request)")
    print("NEXT: open every sheet and check framing, overlaps, clipped or wrapped text, borders and easing. "
          "Fix and run the same command again until clean.")


if __name__ == "__main__":
    main()
