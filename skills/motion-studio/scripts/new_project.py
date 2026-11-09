#!/usr/bin/env python3
"""Create a motion-studio video project with tracking files and a HyperFrames composition.

Usage:
    python new_project.py --name acme-promo --format 9:16 [--duration 20] [--lang en]
                          [--template starter|three-starter] [--parent .] [--install]

Creates <parent>/<name>/ with brief.md, facts.json, decisions.md, script.md, storyboard.json,
style.md, credits.json, assets/, audio/, composition/ (from templates/), renders/previews/.
Refuses to overwrite an existing project folder.
--install runs `npm install` inside composition/ (downloads gsap + three from npm; ask the user first).
Extra formats for the same project: run again with --composition-only --format 1:1
(creates composition-1x1/).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
TEMPLATES = os.path.join(SKILL, "templates")
HF_VERSION = "0.9.23"  # version this skill release was tested with; upgrade per HyperFrames docs

FORMATS = {
    #        w     h    safeL  safeR  top    bottom headline body
    "16:9": (1920, 1080, "5%", "5%", "5%", "5%", 120, 48),
    "9:16": (1080, 1920, "8%", "12%", "12%", "28%", 120, 52),
    "1:1": (1080, 1080, "6%", "6%", "6%", "6%", 104, 46),
    "4:5": (1080, 1350, "6%", "6%", "6%", "6%", 110, 48),
}

TRACKING = {
    "brief.md": "# Brief\n\n- Goal (know / feel / do):\n- Audience:\n- Platform:\n- Format(s): {fmt}\n- Duration: {dur} s\n- Language: {lang}\n- Mode: (autopilot | step-by-step)\n- Playbook:\n- CTA:\n",
    "decisions.md": "# Decisions\n\nLog what was decided at each gate (G1–G4) and why.\n",
    "script.md": "# Script\n\n| # | Time | On-screen text | VO line | Purpose |\n|---|---|---|---|---|\n",
    "style.md": "# Style\n\n- Preset:\n- Palette (hex: role):\n- Fonts (role, weight, file, licence):\n- Motion feel (easing, durations):\n- Transitions:\n",
}


def slug_ok(name):
    return re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name) is not None


def fill(text, values):
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    left = re.findall(r"{{[A-Z_]+}}", text)
    if left:
        sys.exit(f"Template placeholders not filled: {sorted(set(left))}")
    return text


def make_composition(dest, template, fmt, duration, lang, project):
    w, h, sl, sr, st, sb, hp, bp = FORMATS[fmt]
    values = {
        "WIDTH": w, "HEIGHT": h, "FORMAT": fmt, "LANG": lang, "DURATION": duration,
        "MID_DURATION": round(duration - 6, 3), "CTA_START": round(duration - 3, 3),
        "SAFE_LEFT": sl, "SAFE_RIGHT": sr, "SAFE_TOP": st, "SAFE_BOTTOM": sb,
        "HEADLINE_PX": hp, "BODY_PX": bp, "PROJECT": project, "HF_VERSION": HF_VERSION,
    }
    src = os.path.join(TEMPLATES, template)
    if not os.path.isdir(src):
        sys.exit(f"Unknown template '{template}'. Available: {os.listdir(TEMPLATES)}")
    shutil.copytree(src, dest)
    for rootdir, _, files in os.walk(dest):
        for fn in files:
            if fn.endswith((".html", ".json")):
                p = os.path.join(rootdir, fn)
                with open(p, encoding="utf-8") as f:
                    txt = f.read()
                with open(p, "w", encoding="utf-8") as f:
                    f.write(fill(txt, values))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="kebab-case project name, e.g. acme-promo")
    ap.add_argument("--format", default="16:9", choices=FORMATS.keys())
    ap.add_argument("--duration", type=float, default=20.0, help="seconds (default 20; brief default is 15–30)")
    ap.add_argument("--lang", default="en", help="BCP-47 language code for on-screen text, e.g. en, bn, ar")
    ap.add_argument("--template", default="starter", help="starter | three-starter")
    ap.add_argument("--parent", default=".", help="folder to create the project in")
    ap.add_argument("--composition-only", action="store_true", help="add another format to an existing project")
    ap.add_argument("--install", action="store_true", help="run npm install in the composition (ask first)")
    a = ap.parse_args()

    if a.duration <= 0:
        sys.exit("Duration must be positive.")
    if not slug_ok(a.name):
        sys.exit("Use a kebab-case name: lowercase letters, digits, hyphens.")
    if a.template == "starter" and a.duration < 6:
        sys.exit("Duration must be at least 6 s for the starter's 3-scene layout (edit scenes for shorter pieces).")
    proj = os.path.abspath(os.path.join(a.parent, a.name))
    comp_name = "composition" if not a.composition_only else "composition-" + a.format.replace(":", "x")

    if a.composition_only:
        if not os.path.isdir(proj):
            sys.exit(f"Project not found: {proj}")
    else:
        if os.path.exists(proj):
            sys.exit(f"Refusing to overwrite existing folder: {proj}")
        for d in ["assets/fonts", "assets/images", "assets/screens", "assets/footage", "assets/3d",
                  "audio/music", "audio/sfx", "audio/vo", "plan", "renders/previews"]:
            os.makedirs(os.path.join(proj, d), exist_ok=True)
        for fn, body in TRACKING.items():
            with open(os.path.join(proj, fn), "w", encoding="utf-8") as f:
                f.write(body.format(fmt=a.format, dur=a.duration, lang=a.lang))
        for fn, obj in {"facts.json": [], "credits.json": [],
                        "storyboard.json": {"fps": 30, "duration": a.duration, "formats": [a.format], "scenes": []}}.items():
            with open(os.path.join(proj, fn), "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2)
                f.write("\n")

    dest = os.path.join(proj, comp_name)
    if os.path.exists(dest):
        sys.exit(f"Refusing to overwrite existing composition: {dest}")
    make_composition(dest, a.template, a.format, a.duration, a.lang, a.name)

    if a.install:
        npm = shutil.which("npm")
        if not npm:
            sys.exit("npm not found; install Node.js 22+ first.")
        subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=dest, check=True)

    print(json.dumps({"project": proj, "composition": dest, "format": a.format,
                      "template": a.template, "installed": a.install}, indent=2))
    if not a.install:
        print("Next: run `npm install` inside the composition folder (downloads gsap + three).")


if __name__ == "__main__":
    main()
