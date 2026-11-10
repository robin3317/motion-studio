#!/usr/bin/env python3
"""Release regression: build, check, render and QA every template (stdlib only, needs the skill's tools).

    python tests/regression.py                         # all templates, 16:9 + 9:16, with a real audio mix
    python tests/regression.py --templates starter --formats 16:9
    MOTION_STUDIO_HF_VERSION=0.9.28 python tests/regression.py   # try a newer HyperFrames before pinning it

For each template and format it:
  1. scaffolds a project (new_project.py --install) in a scratch folder
  2. mixes music + SFX (mix_audio.py), copies the mix in and switches on the template's <audio> example
  3. runs `hyperframes check` and confirms it changed no source file
  4. renders with render.py, calling it again while it reports RENDER_INCOMPLETE
  5. runs qa_check.py on the MP4 (size, fps, duration, codecs, loudness, true peak, silences)
Prints a table and writes regression-report.json + .md next to the scratch projects.
Exit code 0 only if every row passes. Run it before each release, on your machine AND in a
Claude Cowork cloud session (no GPU, blocked sites): both are places the skill runs.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skills", "motion-studio")
SCRIPTS = os.path.join(SKILL, "scripts")
sys.path.insert(0, SCRIPTS)
from _common import HF_VERSION, find_browser  # noqa: E402

DURATION = {"starter": 8, "three-starter": 6, "isometric-kinetic": 20}
MUSIC = os.path.join(SKILL, "assets", "audio", "music", "corporate-intro_bertsz.mp3")
SFX = os.path.join(SKILL, "assets", "audio", "sfx", "procedural")


def sh(cmd, cwd=None, env=None, timeout=None):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def sources_hash(comp):
    h = hashlib.sha1()
    for root, dirs, files in os.walk(comp):
        dirs[:] = sorted(d for d in dirs if d not in ("node_modules", ".hyperframes", "renders"))
        for fn in sorted(files):
            if fn == "package-lock.json":
                continue
            p = os.path.join(root, fn)
            h.update(os.path.relpath(p, comp).encode())
            with open(p, "rb") as f:
                h.update(f.read())
    return h.hexdigest()


def enable_audio(index):
    """Uncomment the template's <audio> example. Returns False if the example isn't there."""
    with open(index, encoding="utf-8") as f:
        s = f.read()
    m = re.search(r"<!-- AUDIO:.*?(<audio [^>]*></audio>)\s*-->", s, re.S)
    if not m:
        return False
    with open(index, "w", encoding="utf-8", newline="\n") as f:
        f.write(s[:m.start()] + m.group(1) + s[m.end():])
    return True


def one(template, fmt, work, a, env):
    name = f"{template}-{fmt.replace(':', 'x')}"
    row = {"template": template, "format": fmt, "steps": {}, "ok": False}
    dur = DURATION[template]
    proj = os.path.join(work, name)
    comp = os.path.join(proj, "composition")
    py = sys.executable
    t0 = time.time()

    def step(key, ok, detail=""):
        row["steps"][key] = {"ok": bool(ok), "detail": detail}
        print(f"    {'ok  ' if ok else 'FAIL'} {key}: {detail}", flush=True)
        return ok

    code, out = sh([py, os.path.join(SCRIPTS, "new_project.py"), "--name", name, "--format", fmt, "--duration", str(dur),
                    "--template", template, "--parent", work, "--install"], env=env, timeout=600)
    if not step("scaffold", code == 0, "npm install ok" if code == 0 else out[-300:]):
        return row

    plan = {"duration": dur, "music": {"file": MUSIC, "fade_out": 1.0},
            "sfx": [{"file": os.path.join(SFX, "hit-punch.wav"), "start": 0.2, "below_ref_db": 6},
                    {"file": os.path.join(SFX, "boom-deep.wav"), "start": max(0.5, dur - 2.5), "below_ref_db": 4}]}
    with open(os.path.join(proj, "audio", "mix_plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f)
    code, out = sh([py, os.path.join(SCRIPTS, "mix_audio.py"), "--plan", os.path.join(proj, "audio", "mix_plan.json"),
                    "--out", os.path.join(proj, "audio", "mix.wav")], cwd=proj, timeout=300)
    rep = {}
    try:
        rep = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except ValueError:
        pass
    if not step("mix", code == 0 and rep.get("peak_ok"),
                f"{rep.get('integrated_lufs')} LUFS, WAV {rep.get('true_peak_db')} dBTP, AAC {rep.get('aac_true_peak_db')} dBTP"
                if rep else out[-300:]):
        return row
    os.makedirs(os.path.join(comp, "assets"), exist_ok=True)
    shutil.copy(os.path.join(proj, "audio", "mix.wav"), os.path.join(comp, "assets", "mix.wav"))
    if not step("audio example", enable_audio(os.path.join(comp, "index.html")), "switched on"):
        return row

    before = sources_hash(comp)
    npx = shutil.which("npx")
    code, out = sh([npx, "--yes", f"hyperframes@{a.hf}", "check", "--no-cache"], cwd=comp, env=env, timeout=600)
    if "Chrome not found" in out and not env.get("HYPERFRAMES_BROWSER_PATH") and find_browser():
        env["HYPERFRAMES_BROWSER_PATH"] = find_browser()
        code, out = sh([npx, "--yes", f"hyperframes@{a.hf}", "check", "--no-cache"], cwd=comp, env=env, timeout=600)
    flagged = [ln.strip()[:200] for ln in out.splitlines() if re.match(r"\s*[✗⚠] \w+:", ln)]
    errors = sum(1 for ln in flagged if ln.startswith("✗"))
    kinds = sorted({ln.split(":")[0][2:] for ln in flagged if ln.startswith("⚠")})
    summary = f"{errors} errors, {len(flagged) - errors} warnings" + (f" ({', '.join(kinds)})" if kinds else "")
    step("check", code == 0, summary)
    row["check_findings"] = flagged[:12]
    step("check leaves sources alone", sources_hash(comp) == before, "no source file changed")

    mp4 = os.path.join(proj, "renders", f"{name}-v1.mp4")
    calls, last = 0, ""
    while calls < a.max_calls:
        calls += 1
        code, last = sh([py, os.path.join(SCRIPTS, "render.py"), "--out", mp4, "--quality", a.quality,
                         "--budget", str(a.budget)], cwd=proj, env=env, timeout=a.budget + 240 if a.budget else None)
        if code != 3:
            break
    done = re.search(r"RENDER_DONE.*", last)
    if not step("render", code == 0 and os.path.exists(mp4), (done.group(0).split("|", 1)[-1].strip() if done else last[-400:])):
        return row
    row["render_calls"] = calls

    code, out = sh([py, os.path.join(SCRIPTS, "qa_check.py"), mp4, "--expect-format", fmt, "--expect-duration", str(dur),
                    "--json"], timeout=300)
    try:
        qa = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except ValueError:
        qa = {"ok": False, "results": []}
    bad = [f"{r['check']}: {r['detail']}" for r in qa.get("results", []) if not r["ok"]]
    loud = next((r["detail"] for r in qa.get("results", []) if r["check"] == "loudness"), "")
    peak = next((r["detail"] for r in qa.get("results", []) if r["check"] == "true peak"), "")
    step("qa", code == 0 and qa.get("ok"), "; ".join(bad) if bad else f"{loud}; {peak}")
    row["seconds"] = round(time.time() - t0)
    row["ok"] = all(s["ok"] for s in row["steps"].values())
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--templates", default="starter,three-starter,isometric-kinetic")
    ap.add_argument("--formats", default="16:9,9:16")
    ap.add_argument("--quality", default="draft", help="draft (default, fastest) | looks | delivery")
    ap.add_argument("--budget", type=float, default=240.0, help="seconds per render.py call")
    ap.add_argument("--max-calls", type=int, default=12)
    ap.add_argument("--hf", default=HF_VERSION, help="HyperFrames version to test (default: the pinned one)")
    ap.add_argument("--work", help="scratch folder (default: a new temp folder)")
    a = ap.parse_args()

    missing = []
    try:
        import numpy  # noqa: F401
    except ImportError:
        missing.append("numpy    fix: python -m pip install -r skills/motion-studio/scripts/requirements.txt")
    for tool, fix in (("node", "install Node.js 22+"), ("npx", "comes with Node.js"),
                      ("ffmpeg", "install FFmpeg"), ("ffprobe", "comes with FFmpeg")):
        if not shutil.which(tool):
            missing.append(f"{tool}    fix: {fix}")
    if missing:
        sys.exit("Can't run the regression. Missing on this machine:\n  " + "\n  ".join(missing)
                 + "\nscripts/preflight.py shows the full list (references/setup.md has the install commands).")

    work = os.path.abspath(a.work) if a.work else tempfile.mkdtemp(prefix="ms-regression-")
    os.makedirs(work, exist_ok=True)
    env = dict(os.environ, MOTION_STUDIO_HF_VERSION=a.hf)
    print(f"motion-studio regression | hyperframes@{a.hf} | quality {a.quality} | {work}", flush=True)
    rows = []
    for t in [x.strip() for x in a.templates.split(",") if x.strip()]:
        if t not in DURATION:
            sys.exit(f"unknown template {t}")
        for fmt in [x.strip() for x in a.formats.split(",") if x.strip()]:
            print(f"\n== {t} {fmt}", flush=True)
            rows.append(one(t, fmt, work, a, env))

    ok = all(r["ok"] for r in rows)
    lines = [f"# Regression: hyperframes@{a.hf}, quality {a.quality} ({time.strftime('%Y-%m-%d')})", "",
             "| Template | Format | Check | Render | QA | Calls | Time |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        s = r["steps"]

        def cell(k):
            return ("pass" if s[k]["ok"] else "FAIL") if k in s else "-"
        qa = s.get("qa", {}).get("detail", "")
        lines.append(f"| {r['template']} | {r['format']} | {cell('check')} ({s.get('check', {}).get('detail', '')}) | "
                     f"{cell('render')} | {cell('qa')} ({qa}) | {r.get('render_calls', '-')} | {r.get('seconds', '-')} s |")
    lines += ["", "RESULT: " + ("all passed" if ok else "FAILED")]
    with open(os.path.join(work, "regression-report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(work, "regression-report.json"), "w", encoding="utf-8") as f:
        json.dump({"hyperframes": a.hf, "quality": a.quality, "ok": ok, "rows": rows}, f, indent=2)
    print("\n" + "\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
