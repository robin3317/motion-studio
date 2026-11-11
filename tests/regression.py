#!/usr/bin/env python3
"""Release regression: build, check, render and QA every template (stdlib only, needs the skill's tools).

    python tests/regression.py                         # all templates, 16:9 + 9:16, with a real audio mix
    python tests/regression.py --templates starter --formats 16:9
    MOTION_STUDIO_HF_VERSION=0.9.28 python tests/regression.py   # try a newer HyperFrames before pinning it

For each template and format it:
  1. scaffolds a project (new_project.py --install) in a scratch folder
  2. mixes music + SFX (mix_audio.py), copies the mix in and switches on the template's <audio> example
  3. runs `hyperframes check` and confirms it changed no source file
  4. makes a contact sheet (preview_sheet.py) and runs the visual audit (visual_audit.py)
  5. renders with render.py, calling it again while it reports RENDER_INCOMPLETE
  6. runs qa_check.py on the MP4 (size, fps, duration, codecs, loudness, true peak, silences)
Then one extra row: a 3D render that is stopped part-way and must resume from its saved frames
and finish, on this machine (skip with --no-resume-test; run it alone with --only-resume-test).
Prints a table and writes regression-report.json + .md next to the scratch projects.
Exit code 0 only if every row passes. Run it before each release, on your machine AND in a
Claude Cowork cloud session (no GPU, blocked sites): both are places the skill runs.

    python tests/regression.py --record    # also write this machine's result into tests/RELEASE_CHECKS.json
"""
import argparse
import hashlib
import json
import os
import platform
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

DURATION = {"starter": 8, "three-starter": 8, "isometric-kinetic": 20}
MUSIC = os.path.join(SKILL, "assets", "audio", "music", "corporate-intro_bertsz.mp3")
SFX = os.path.join(SKILL, "assets", "audio", "sfx", "procedural")


def one_line(text, limit=220):
    """The last meaningful line of a command's output, safe to put in a table cell."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    pick = next((ln for ln in reversed(lines) if ln.startswith(("RENDER_", "AUDIT_", "SHEET_", "ERROR", "Traceback"))),
                lines[-1] if lines else "")
    return pick.replace("|", "/")[:limit]


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
    if not step("scaffold", code == 0, "npm install ok" if code == 0 else one_line(out)):
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
                if rep else one_line(out)):
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

    with open(os.path.join(proj, "storyboard.json"), encoding="utf-8") as f:
        sb = json.load(f)
    third = dur / 3
    sb["scenes"] = [{"id": f"s{i + 1}", "start": round(i * third, 2), "duration": round(third, 2)} for i in range(3)]
    with open(os.path.join(proj, "storyboard.json"), "w", encoding="utf-8") as f:
        json.dump(sb, f)
    code, out = sh([py, os.path.join(SCRIPTS, "preview_sheet.py"), "--scene", "s1", "--fps", "4", "--json"],
                   cwd=proj, env=env, timeout=600)
    sheet = {}
    try:
        sheet = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except ValueError:
        pass
    sheets = sheet.get("sheets") or []
    step("contact sheet", code == 0 and sheets and all(os.path.getsize(x) > 2000 for x in sheets),
         f"{len(sheet.get('frames', []))} frames on {len(sheets)} sheet(s)" if sheets else one_line(out))
    code, out = sh([py, os.path.join(SCRIPTS, "visual_audit.py"), "--json"], cwd=proj, env=env, timeout=900)
    audit = {}
    try:
        audit = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except ValueError:
        pass
    measured = not any("NOT measured" in n for n in audit.get("notes", []))
    step("visual audit", code == 0 and audit.get("status") == "AUDIT_DONE" and measured and audit.get("scene_sheets"),
         (f"{audit.get('errors')} errors, {audit.get('warnings')} warnings, {audit.get('to_review')} to review, "
          f"{audit.get('components_measured')} components") if audit else one_line(out))
    row["audit_findings"] = [f"{x['code']}: {x['what']}" for x in audit.get("component_findings", [])
                             + [h for h in audit.get("hyperframes_findings", []) if h["severity"] != "info"]][:12]

    mp4 = os.path.join(proj, "renders", f"{name}-v1.mp4")
    calls, last = 0, ""
    while calls < a.max_calls:
        calls += 1
        code, last = sh([py, os.path.join(SCRIPTS, "render.py"), "--out", mp4, "--quality", a.quality,
                         "--budget", str(a.budget)], cwd=proj, env=env, timeout=a.budget + 240 if a.budget else None)
        if code != 3:
            break
    done = re.search(r"RENDER_DONE.*", last)
    if not step("render", code == 0 and os.path.exists(mp4), (done.group(0).split("|", 1)[-1].strip() if done else one_line(last))):
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


def tools_test(work, a, env, rows):
    """The scripts around the film: the default template, the font fetcher and the reference analysis."""
    row = {"template": "tools", "format": "default 3D, fonts, reference", "steps": {}, "ok": False}
    py = sys.executable
    t0 = time.time()

    def step(key, ok, detail=""):
        row["steps"][key] = {"ok": bool(ok), "detail": detail}
        print(f"    {'ok  ' if ok else 'FAIL'} {key}: {detail}", flush=True)
        return ok

    code, out = sh([py, os.path.join(SCRIPTS, "new_project.py"), "--name", "tools-test", "--format", "4:5",
                    "--duration", "10", "--parent", work], env=env, timeout=120)
    info = {}
    try:
        info = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except ValueError:
        pass
    proj = os.path.join(work, "tools-test")
    comp = os.path.join(proj, "composition")
    html = ""
    if os.path.isfile(os.path.join(comp, "index.html")):
        with open(os.path.join(comp, "index.html"), encoding="utf-8") as f:
            html = f.read()
    step("default template is 3D", code == 0 and info.get("template") == "three-starter"
         and os.path.isfile(os.path.join(comp, "lib", "stage.js")) and "{{" not in html
         and re.search(r'data-quality="(cpu|standard)"', html),
         f"{info.get('template')}, 3D profile {info.get('quality_3d')}" if info else one_line(out))

    code, out = sh([py, os.path.join(SCRIPTS, "get_font.py"), "JetBrains Mono", "--weights", "500", "--as", "Mono"],
                   cwd=proj, env=env, timeout=240)
    font_dir = os.path.join(comp, "assets", "fonts", "jetbrains-mono")
    credited = False
    try:
        with open(os.path.join(proj, "credits.json"), encoding="utf-8") as f:
            credited = any(c.get("type") == "font" for c in json.load(f))
    except (OSError, ValueError):
        pass
    step("font fetch", code == 0 and "FONT_DONE" in out and credited
         and os.path.isfile(os.path.join(font_dir, "jetbrains-mono-latin-500-normal.woff2"))
         and os.path.isfile(os.path.join(font_dir, "LICENSE")),
         "woff2 + licence + credits entry" if code == 0 else one_line(out))

    names = [f"{r['template']}-{r['format'].replace(':', 'x')}" for r in rows if r.get("steps", {}).get("render", {}).get("ok")]
    mp4 = os.path.join(work, names[0], "renders", f"{names[0]}-v1.mp4") if names else None
    if not mp4 or not os.path.isfile(mp4):   # no film was rendered in this run: make a small test clip
        mp4 = os.path.join(work, "tools-ref.mp4")
        sh([shutil.which("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=4",
            "-f", "lavfi", "-i", "sine=f=440:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", mp4], timeout=120)
    code, out = sh([py, os.path.join(SCRIPTS, "analyze_ref.py"), mp4], cwd=proj, env=env, timeout=600)
    done = re.search(r"ANALYSIS_DONE (.*?) \| (.*)", out)
    folder = done.group(2).strip() if done else ""
    step("reference analysis", code == 0 and done and os.path.isfile(os.path.join(folder, "recipe.md"))
         and any(f.startswith("hook-") for f in os.listdir(folder)), done.group(1) if done else one_line(out))
    row["seconds"] = round(time.time() - t0)
    row["ok"] = all(v["ok"] for v in row["steps"].values())
    return row


def resume_test(work, a, env):
    """A render that is stopped part-way must keep its finished segments and finish on a later call.
    The stop is forced as soon as 60 frames are saved in finished segments (render.py's test hook), so it
    happens on any machine, fast or slow, with one worker or many. Budget stops use the same code path."""
    row = {"template": "three-starter", "format": "resume test", "steps": {}, "ok": False}
    py, t0 = sys.executable, time.time()
    proj = os.path.join(work, "resume-test")
    code, out = sh([py, os.path.join(SCRIPTS, "new_project.py"), "--name", "resume-test", "--format", "16:9", "--duration",
                    "12", "--template", "three-starter", "--parent", work, "--install"], env=env, timeout=600)
    ok = code == 0
    row["steps"]["scaffold"] = {"ok": ok, "detail": "ok" if ok else one_line(out)}
    mp4 = os.path.join(proj, "renders", "resume-test-v1.mp4")
    calls, stops, saved, last, code = 0, 0, 0, "", 1
    while ok and calls < 6:
        calls += 1
        call_env = dict(env)
        if not saved:                      # keep stopping part-way until a call leaves saved frames behind
            call_env["MS_RENDER_STOP_AFTER_SAVED_FRAMES"] = "60"
        code, last = sh([py, os.path.join(SCRIPTS, "render.py"), "--out", mp4, "--quality", "draft", "--budget", "300"],
                        cwd=proj, env=call_env, timeout=600)
        said = next((ln for ln in last.splitlines() if ln.startswith("RENDER_")), "")
        print(f"    call {calls}: exit {code}", flush=True)
        for ln in last.strip().splitlines()[:12]:   # render.py's own short report: workers, saved frames, hints
            print(f"      | {ln[:200]}", flush=True)
        if code != 3:
            break
        stops += 1
        m = re.search(r"RENDER_INCOMPLETE (\d+)/", said)
        saved = int(m.group(1)) if m else 0
    resumed = re.search(r"(\d+) frames already saved", last)
    finished = code == 0 and os.path.exists(mp4)
    proven = bool(finished and stops and resumed and int(resumed.group(1)) > 0)
    detail = (f"stopped {stops} time(s), resumed from {resumed.group(1)} saved frames, finished on call {calls}" if proven else
              "finished, but no call resumed from saved frames: resume is NOT proven here" if finished else one_line(last))
    row["steps"]["render"] = {"ok": proven, "detail": detail}
    row["resume_tested"] = proven
    print(f"    {'ok  ' if proven else 'FAIL'} resume: {detail}", flush=True)
    if finished:
        code, out = sh([py, os.path.join(SCRIPTS, "qa_check.py"), mp4, "--expect-format", "16:9", "--expect-duration", "12",
                        "--no-audio-ok", "--json"], timeout=300)
        row["steps"]["qa"] = {"ok": code == 0, "detail": "12 s, all frames" if code == 0 else one_line(out)}
    row["render_calls"] = calls
    row["seconds"] = round(time.time() - t0)
    row["ok"] = all(s["ok"] for s in row["steps"].values())
    return row


def record(rows, a, ok):
    """Write this machine's result into tests/RELEASE_CHECKS.json (one entry per machine, per version)."""
    path = os.path.join(REPO, "tests", "RELEASE_CHECKS.json")
    with open(os.path.join(REPO, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        version = json.load(f)["version"]
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        doc = {}
    if doc.get("version") != version:   # a new version starts clean; the hand-written lists carry over for review
        doc = {"version": version, "automated": [], "manual": {k: "not run" for k in doc.get("manual", {})} or
               {"acceptance prompts (tests/acceptance.md)": "not run", "trigger prompts (tests/triggers.md)": "not run"},
               "not_tested": doc.get("not_tested", [])}
    try:
        node = subprocess.run([shutil.which("node"), "--version"], capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        node = "?"
    host = f"{platform.system()} {platform.release()} ({platform.machine()}), {os.cpu_count()} cores"
    resume = next((r for r in rows if r["format"] == "resume test"), None)
    entry = {"host": host, "date": time.strftime("%Y-%m-%d"), "python": platform.python_version(), "node": node,
             "hyperframes": a.hf, "quality": a.quality, "result": "all passed" if ok else "FAILED",
             "rows": [{"template": r["template"], "format": r["format"], "ok": r["ok"],
                       "failed_steps": [k for k, v in r["steps"].items() if not v["ok"]],
                       "qa": r["steps"].get("qa", {}).get("detail", "")} for r in rows],
             "resume_after_budget_stop": ("tested, works" if resume and resume.get("resume_tested") else
                                          "not proven" if resume and resume["ok"] else
                                          "FAILED" if resume else "not run")}
    doc["automated"] = [e for e in doc.get("automated", []) if e.get("host") != host] + [entry]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"recorded in {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--templates", default="starter,three-starter,isometric-kinetic")
    ap.add_argument("--formats", default="16:9,9:16")
    ap.add_argument("--quality", default="draft", help="draft (default, fastest) | looks | delivery")
    ap.add_argument("--budget", type=float, default=240.0, help="seconds per render.py call")
    ap.add_argument("--max-calls", type=int, default=12)
    ap.add_argument("--hf", default=HF_VERSION, help="HyperFrames version to test (default: the pinned one)")
    ap.add_argument("--work", help="scratch folder (default: a new temp folder)")
    ap.add_argument("--no-resume-test", action="store_true", help="skip the stop + resume row")
    ap.add_argument("--no-tools-test", action="store_true", help="skip the default-template, font and reference row")
    ap.add_argument("--only-resume-test", action="store_true", help="run only the stop + resume row")
    ap.add_argument("--record", action="store_true", help="write this machine's result into tests/RELEASE_CHECKS.json")
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
    for t in [] if a.only_resume_test else [x.strip() for x in a.templates.split(",") if x.strip()]:
        if t not in DURATION:
            sys.exit(f"unknown template {t}")
        for fmt in [x.strip() for x in a.formats.split(",") if x.strip()]:
            print(f"\n== {t} {fmt}", flush=True)
            rows.append(one(t, fmt, work, a, env))
    if not a.no_tools_test and not a.only_resume_test:
        print("\n== tools (default template, get_font.py, analyze_ref.py)", flush=True)
        rows.append(tools_test(work, a, env, rows))
    if not a.no_resume_test:
        print("\n== resume test (three-starter 12 s, stopped once 60 frames are saved)", flush=True)
        rows.append(resume_test(work, a, env))

    ok = all(r["ok"] for r in rows)
    lines = [f"# Regression: hyperframes@{a.hf}, quality {a.quality} ({time.strftime('%Y-%m-%d')})", "",
             "| Template | Format | Check | Sheet + audit | Render | QA | Calls | Time |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        s = r["steps"]

        def cell(k):
            return ("pass" if s[k]["ok"] else "FAIL") if k in s else "-"
        qa = one_line(s.get("qa", {}).get("detail", ""))
        tools = "-" if "contact sheet" not in s else ("pass" if s["contact sheet"]["ok"] and s.get("visual audit", {}).get("ok")
                                                      else "FAIL")
        render = cell("render") + (f" ({one_line(s['render']['detail'])})" if r["format"] == "resume test" and "render" in s else "")
        if r["template"] == "tools":
            lines.append(f"| tools | {r['format']} | " + " · ".join(f"{k}: {'pass' if v['ok'] else 'FAIL'}" for k, v in s.items())
                         + f" | - | - | - | - | {r.get('seconds', '-')} s |")
            continue
        check = f"{cell('check')} ({s['check']['detail']})" if "check" in s else "-"
        lines.append(f"| {r['template']} | {r['format']} | {check} | {tools} | "
                     f"{render} | {cell('qa')} ({qa}) | {r.get('render_calls', '-')} | {r.get('seconds', '-')} s |")
    lines += ["", "RESULT: " + ("all passed" if ok else "FAILED")]
    with open(os.path.join(work, "regression-report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(work, "regression-report.json"), "w", encoding="utf-8") as f:
        json.dump({"hyperframes": a.hf, "quality": a.quality, "ok": ok, "rows": rows}, f, indent=2)
    print("\n" + "\n".join(lines))
    if a.record:
        record(rows, a, ok)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
