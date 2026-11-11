#!/usr/bin/env python3
"""Render a composition to MP4 in the foreground, inside a time budget, and resume if it didn't finish.

Usage (run from the project folder; the composition must have had `npm install`):
    python render.py --out renders/acme-16x9-v1.mp4 --quality delivery
    python render.py --out renders/previews/acme-preview-v1.mp4 --quality draft --budget 540
    python render.py --out renders/acme-16x9-v1.mp4 --status      # progress of an unfinished render

Options:
    --composition DIR   composition folder (default: ./composition, or . if it has index.html)
    --quality Q         draft | looks | delivery (default: delivery)
    --budget SECONDS    longest this ONE call may run (default 100; 0 = no limit). Set it to your
                        shell tool's time limit minus 60 s (a 10-minute limit -> --budget 540)
    --workers N|auto    capture workers (default auto: 1 on machines with 4 cores or fewer)
    --fps N             override the composition's frame rate
    --restart           throw away saved progress for this composition and start again
    --json              print the final report as JSON only
    -- ARGS             anything after `--` goes to `hyperframes render` unchanged

Exit codes:  0 = finished (prints RENDER_DONE)
             3 = not finished yet (prints RENDER_INCOMPLETE): run the SAME command again, it resumes
             1 = failed (prints RENDER_FAILED and the end of the HyperFrames log)

Why this script exists: shell tools kill a command that runs longer than their limit, and a render
that is put in the background dies with the call and leaves Chrome running. So NEVER background a
render. This script keeps the render in the foreground, stops it before the budget ends, and uses
HyperFrames' own segmented capture (HF_SEGMENTED_CAPTURE + --resume), so finished segments are kept
and the next call only renders what is missing. If any file of the composition changed since the
last call, it starts again from frame 0, so old and new frames never end up in one video.
It also points HyperFrames at an installed Chrome when its own download is blocked, uses one worker
on small machines, raises the player-ready timeout for slow WebGL start-up, and ends processes its
own render left behind. It refuses to overwrite --out. It does not use `render --start/--end`:
that path skips node_modules, so compositions that load GSAP/Three from there fail.
"""
import argparse
import glob
import hashlib
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import HF_VERSION, find_browser, which  # noqa: E402

WIN = os.name == "nt"
STATE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "motion-studio", "render")
MIN_SEGMENT_FRAMES = 30          # HyperFrames' minimum
STOP_MARGIN = 15                 # seconds kept free at the end of the budget for a clean stop
LAST_MOMENT = 10                 # once every frame is captured, assembly may use the margin up to this point
SKIP_DIRS = {"node_modules", "renders", ".hyperframes", ".git", "__pycache__"}
STOP_NOW = False                 # set by SIGTERM/SIGINT: stop the render and report progress


# ---------- process helpers ----------
# Rule: only ever end a process that this render started. On Linux/macOS children are recorded while
# the render runs (pid + start time + command line) and checked against all three before anything is
# ended. On Windows nothing is recorded: the render's own process tree is ended while it is alive.

def proc_table():
    """[(pid, ppid, start, command)] for every process on Linux/macOS; [] on Windows or on any error."""
    rows = []
    try:
        if os.path.isdir("/proc/self"):
            for name in os.listdir("/proc"):
                if not name.isdigit():
                    continue
                try:
                    with open(f"/proc/{name}/stat", encoding="utf-8", errors="replace") as f:
                        fields = f.read().rsplit(")", 1)[1].split()
                    with open(f"/proc/{name}/cmdline", "rb") as f:
                        cmd = f.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
                    rows.append((int(name), int(fields[1]), fields[19], cmd))  # ppid, start time in ticks
                except (OSError, ValueError, IndexError):
                    continue
        elif not WIN:
            out = subprocess.run(["ps", "-axww", "-o", "pid=,ppid=,lstart=,command="], capture_output=True,
                                 text=True, timeout=10, errors="replace").stdout
            for line in out.splitlines():
                p = line.split(None, 7)  # pid ppid + 5 words of lstart + command
                if len(p) >= 7 and p[0].isdigit() and p[1].isdigit():
                    rows.append((int(p[0]), int(p[1]), " ".join(p[2:7]), p[7] if len(p) > 7 else ""))
    except Exception:  # noqa: BLE001  never let bookkeeping break a render
        return []
    return rows


def family(root, table):
    """The process `root` and everything it started: {pid: {"start":…, "cmd":…}}."""
    kids, info = {}, {}
    for pid, ppid, start, cmd in table:
        kids.setdefault(ppid, []).append(pid)
        info[pid] = {"start": start, "cmd": cmd[:300]}
    out, stack = {}, [root]
    if root in info:
        out[root] = info[root]
    while stack:
        for pid in kids.get(stack.pop(), []):
            if pid not in out:
                out[pid] = info[pid]
                stack.append(pid)
    return out


def end_leftovers(known):
    """End recorded processes of our render that are still running. A pid counts as 'still ours' only
    if its start time and command line are unchanged; zombies (empty command line) are ignored."""
    if not known or WIN:
        return 0
    now = {pid: (start, cmd[:300]) for pid, _, start, cmd in proc_table()}
    hit = []
    for pid, rec in known.items():
        pid = int(pid)
        cur = now.get(pid)
        if cur and cur[1] and isinstance(rec, dict) and cur == (rec.get("start"), rec.get("cmd")):
            hit.append(pid)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in hit:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        if hit and sig == signal.SIGTERM:
            time.sleep(1.5)
    return len(hit)


# ---------- state ----------

def state_path(out):
    key = hashlib.sha1(os.path.normcase(os.path.abspath(out)).encode("utf-8")).hexdigest()[:12]
    return os.path.join(STATE_DIR, key + ".json")


def load_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(path, st):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=2)
        os.replace(tmp, path)
    except OSError:
        pass


def fingerprint(comp, settings):
    """Changes when any file of the composition (or a render setting) changes. HyperFrames' own check
    only looks at the compiled HTML, so a changed image or script file would be missed without this."""
    h = hashlib.sha1(json.dumps(settings, sort_keys=True).encode("utf-8"))
    for root, dirs, files in os.walk(comp):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for fn in sorted(files):
            p = os.path.join(root, fn)
            try:
                s = os.stat(p)
            except OSError:
                continue
            h.update(f"{os.path.relpath(p, comp)}|{s.st_size}|{s.st_mtime_ns}\n".encode("utf-8"))
    return h.hexdigest()[:16]


def manifests(comp):
    """HyperFrames' segment manifests in this composition: [(mtime, segment size, total frames, saved frames)]."""
    out = []
    for mf in glob.glob(os.path.join(comp, "renders", ".hf-segments", "*", "segments.json")):
        try:
            with open(mf, encoding="utf-8") as f:
                m = json.load(f)
            out.append((os.path.getmtime(mf), int(m.get("segmentFrames", 0)), int(m.get("totalFrames", 0)),
                        sum(int(s["endFrame"]) - int(s["startFrame"]) for s in m.get("completed", []))))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return out


def fresh_segment_size(comp, wanted):
    """Start from frame 0: drop HyperFrames' saved segments. Where files can't be deleted (some sandboxes),
    pick a segment size no saved manifest uses: the size is part of HyperFrames' cache key, so it can't reuse them."""
    shutil.rmtree(os.path.join(comp, "renders", ".hf-segments"), ignore_errors=True)
    used = {m[1] for m in manifests(comp)}
    n = max(MIN_SEGMENT_FRAMES, wanted)
    while n in used:
        n += 1
    return n


def saved_frames(comp, seg):
    """(frames in finished segments, total frames) from the newest manifest written with our segment size."""
    mine = sorted(m for m in manifests(comp) if m[1] == seg)
    return (mine[-1][3], mine[-1][2]) if mine else (0, 0)


# ---------- HyperFrames ----------

def pinned_version(comp):
    try:
        with open(os.path.join(comp, "package.json"), encoding="utf-8") as f:
            m = re.search(r"hyperframes@(\d+\.\d+\.\d+)", f.read())
        return m.group(1) if m else None
    except OSError:
        return None


def film_seconds(comp):
    try:
        with open(os.path.join(comp, "index.html"), encoding="utf-8") as f:
            m = re.search(r'data-composition-id="[^"]*"[^>]*\bdata-duration="([\d.]+)"', f.read())
        return float(m.group(1)) if m else None
    except (OSError, ValueError):
        return None


def probe(path):
    """{'seconds', 'frames', 'audio'} of the finished file; {} if it can't be read; None without ffprobe."""
    ffprobe = which("ffprobe")
    if not ffprobe:
        return None
    try:
        out = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,nb_frames",
                              "-of", "json", path], capture_output=True, text=True, timeout=60).stdout
        d = json.loads(out)
        v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
        return {"seconds": round(float(d["format"]["duration"]), 3), "frames": int(v.get("nb_frames") or 0),
                "audio": any(s.get("codec_type") == "audio" for s in d.get("streams", []))}
    except Exception:  # noqa: BLE001
        return {}


class Run:
    """One foreground `hyperframes render`, stopped when the deadline passes."""

    def __init__(self, cmd, env, cwd, log_path, deadline, st, st_path, quiet):
        self.cmd, self.env, self.cwd, self.log_path = cmd, env, cwd, log_path
        self.deadline, self.st, self.st_path, self.quiet = deadline, st, st_path, quiet
        self.samples = []            # (time, frames captured) from @hf-progress
        self.total = 0
        self.done = 0
        self.tail = []
        self.stopped_for_budget = False
        self.segmented = False
        self.children = {}
        self.began = time.time()
        self.first_frame_at = None   # when capture started: everything before it is start-up
        # Test hook (tests/regression.py): stop once this many frames are SAVED in finished segments,
        # whatever the machine's speed or worker count. `saved` is set by main().
        self.stop_after = int(os.environ.get("MS_RENDER_STOP_AFTER_SAVED_FRAMES") or 0)
        self.saved = lambda: 0

    def _reader(self, pipe, q):
        try:
            for line in iter(pipe.readline, ""):
                q.put(line)
        except ValueError:
            pass
        q.put(None)

    def _note(self, line, log):
        log.write(line)
        s = line.strip()
        if not s:
            return
        if s.startswith("@hf-progress"):
            try:
                p = json.loads(s[len("@hf-progress"):])
            except ValueError:
                return
            if p.get("code") == "capture" and p.get("total"):
                self.total, self.done = int(p["total"]), int(p.get("done", 0))
                self.samples.append((time.time(), self.done))
                if self.first_frame_at is None:
                    self.first_frame_at = time.time()
            return
        if "(segment " in s or "capture_segmented" in s or "Segmented capture" in s:
            self.segmented = True
        if re.match(r"^[\s█░]+\d+%", s) or s.startswith("[INFO] [Render:trace]"):
            return  # progress bars and trace lines: in the log file, not in the tail
        self.tail.append(s[:400])
        del self.tail[:-40]

    def speed(self):
        s = self.samples
        if len(s) < 3:
            return None
        (t0, d0), (t1, d1) = s[1], s[-1]
        return (d1 - d0) / (t1 - t0) if t1 - t0 >= 2 and d1 > d0 else None

    def _watch_children(self, pid):
        kids = family(pid, proc_table())
        if kids:
            self.children.update(kids)
            self.st["children"] = {str(k): v for k, v in self.children.items()}
            save_state(self.st_path, self.st)

    def _stop(self, proc):
        """Stop HyperFrames. On Linux/macOS it gets SIGTERM first and closes Chrome itself."""
        self.stopped_for_budget = True
        try:
            if WIN:
                proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(proc.pid, signal.SIGTERM)
        except Exception:  # noqa: BLE001
            pass
        try:
            proc.wait(timeout=2 if WIN else 6)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            if WIN:  # ends the whole tree (npx -> node -> Chrome) while it is still attached to us
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=15)
            else:
                os.killpg(proc.pid, signal.SIGKILL)
        except Exception:  # noqa: BLE001
            pass
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass

    def go(self):
        kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if WIN else {"start_new_session": True}
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8", errors="replace") as log:
            log.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')}  {' '.join(self.cmd)}\n")
            proc = subprocess.Popen(self.cmd, cwd=self.cwd, env=self.env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    encoding="utf-8", errors="replace", bufsize=1, **kw)
            q = queue.Queue()
            threading.Thread(target=self._reader, args=(proc.stdout, q), daemon=True).start()
            last_watch = last_print = time.time()
            stopped_at = None
            while True:
                try:
                    line = q.get(timeout=0.5)
                    if line is None:
                        break
                    self._note(line, log)
                except queue.Empty:
                    pass
                now = time.time()
                if stopped_at and now - stopped_at > 5:
                    break  # stopped, but something still holds the output pipe open: don't wait for it
                if not WIN and now - last_watch >= 2:
                    last_watch = now
                    self._watch_children(proc.pid)
                if not self.quiet and now - last_print >= 20 and self.total:
                    last_print = now
                    sp = self.speed()
                    print(f"[render] {self.done}/{self.total} frames" + (f", {sp:.1f} fps" if sp else ""), flush=True)
                if not self.stopped_for_budget and self.stop_after and self.done < self.total \
                        and self.saved() >= self.stop_after:
                    self._stop(proc)
                    stopped_at = time.time()
                if not self.stopped_for_budget and (STOP_NOW or self.deadline):
                    captured_all = self.total and self.done >= self.total
                    limit = (self.deadline + ((STOP_MARGIN - LAST_MOMENT) if captured_all else 0)) if self.deadline else 0
                    if STOP_NOW or now >= limit:
                        self._stop(proc)
                        stopped_at = time.time()
            try:
                code = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                code = -1
        end_leftovers(self.children)
        self.st["children"] = {}
        save_state(self.st_path, self.st)
        return code


def main():
    t0 = time.time()
    argv, extra = sys.argv[1:], []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--composition")
    ap.add_argument("--quality", default="delivery")
    ap.add_argument("--budget", type=float, default=100.0)
    ap.add_argument("--workers", default="auto")
    ap.add_argument("--fps")
    ap.add_argument("--segment-frames", type=int, default=MIN_SEGMENT_FRAMES, help=argparse.SUPPRESS)
    ap.add_argument("--hf-version", help=argparse.SUPPRESS)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--restart", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    def fail(msg, tail=None, log=None):
        if a.json:
            print(json.dumps({"status": "RENDER_FAILED", "error": msg, "log": log}, indent=2))
        else:
            print(f"RENDER_FAILED {msg}")
            for line in (tail or [])[-25:]:
                print("  | " + line)
            if log:
                print(f"Full HyperFrames log: {log}")
        sys.exit(1)

    out = os.path.abspath(a.out)
    comp = os.path.abspath(a.composition or ("composition" if os.path.isdir("composition") else "."))
    if not os.path.isfile(os.path.join(comp, "index.html")):
        fail(f"no index.html in {comp} (run from the project folder or pass --composition)")
    if not out.lower().endswith(".mp4"):
        fail("--out must end in .mp4 (for other formats or --batch, call `npx hyperframes render` directly)")
    if any(x.split("=")[0] in ("--batch", "-o", "--output", "--start", "--end") for x in extra):
        fail("--batch, --output and --start/--end can't be passed through this script")

    st_path = state_path(out)
    log_path = st_path[:-5] + ".log"
    st = load_state(st_path)
    total_s = film_seconds(comp)

    if a.status:
        done, total = saved_frames(comp, int(st.get("segment_frames") or 0)) if st else (0, 0)
        rep = {"status": "RENDER_DONE" if os.path.exists(out) else ("RENDER_INCOMPLETE" if st else "NOT_STARTED"),
               "out": out, "frames_saved": done, "frames_total": total or st.get("frames_total", 0),
               "calls": st.get("calls", 0), "fps": st.get("fps")}
        print(json.dumps(rep, indent=2))
        return
    if os.path.exists(out):
        fail(f"{out} already exists. Never overwrite a render: use the next version number (-v2, -v3…).")
    if not os.path.isdir(os.path.join(comp, "node_modules")):
        fail(f"{comp} has no node_modules: run `npm install` there first (the composition loads GSAP/Three from it)")
    npx = which("npx")
    if not npx:
        fail("npx not found: install Node.js 22+ (references/setup.md)")

    # A previous call that the shell tool killed can leave its render running. End it before starting.
    ended = end_leftovers(st.get("children", {}))

    version = a.hf_version or pinned_version(comp) or HF_VERSION
    fp = fingerprint(comp, {"quality": a.quality, "fps": a.fps, "extra": extra, "hf": version})
    restarted = ""
    if a.restart or st.get("fingerprint") != fp:
        if st.get("fingerprint") and not a.restart:
            restarted = "the composition changed since the last call: starting again from frame 0"
        keep = {} if a.restart else {k: st[k] for k in ("browser", "single_worker") if k in st}
        st = dict(keep, fingerprint=fp, segment_frames=fresh_segment_size(comp, a.segment_frames))
    seg = int(st["segment_frames"])

    cores = os.cpu_count() or 2
    workers = a.workers
    if st.get("single_worker"):
        workers = "1"
    elif workers == "auto":
        workers = "1" if cores <= 4 else None
    partial = out[:-4] + ".partial.mp4"
    os.makedirs(os.path.dirname(out), exist_ok=True)

    cmd = [npx, "--yes", f"hyperframes@{version}", "render", "-q", a.quality, "-o", partial, "--resume",
           "--player-ready-timeout", "180000", "--protocol-timeout", "600000"]
    if workers:
        cmd += ["-w", str(workers)]
    if a.fps:
        cmd += ["--fps", str(a.fps)]
    cmd += extra

    env = dict(os.environ, HF_SEGMENTED_CAPTURE="true", HF_SEGMENT_FRAMES=str(seg))
    browser_note = "HyperFrames' own"
    if env.get("HYPERFRAMES_BROWSER_PATH"):
        browser_note = env["HYPERFRAMES_BROWSER_PATH"]
    elif st.get("browser") and os.path.isfile(st["browser"]):
        env["HYPERFRAMES_BROWSER_PATH"] = browser_note = st["browser"]

    st.update({"out": out, "composition": comp, "hf_version": version, "calls": int(st.get("calls", 0)) + 1})
    save_state(st_path, st)
    before, _ = saved_frames(comp, seg)
    deadline = (t0 + a.budget - STOP_MARGIN) if a.budget > 0 else None

    def stop_now(*_):
        global STOP_NOW
        STOP_NOW = True
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, stop_now)
        except (ValueError, OSError):
            pass
    if not a.json:
        if ended:
            print(f"[render] ended {ended} process(es) left running by an earlier call of this render", flush=True)
        if restarted:
            print(f"[render] {restarted}", flush=True)
        est = f", film {total_s:g} s" if total_s else ""
        print(f"[render] hyperframes@{version}, quality {a.quality}, workers {workers or 'auto'}{est}, "
              f"call {st['calls']}" + (f", {before} frames already saved" if before else ""), flush=True)

    run = Run(cmd, env, comp, log_path, deadline, st, st_path, a.json)
    run.saved = lambda: saved_frames(comp, seg)[0]
    code = run.go()
    text = "\n".join(run.tail)
    if code != 0 and not run.stopped_for_budget and "Chrome not found" in text and not env.get("HYPERFRAMES_BROWSER_PATH"):
        found = find_browser()
        if not found:
            fail("HyperFrames couldn't download its Chrome and no installed Chrome/Chromium/Edge was found. "
                 "Install Chrome, or see references/setup.md (HYPERFRAMES_BROWSER_PATH).", run.tail, log_path)
        env["HYPERFRAMES_BROWSER_PATH"] = st["browser"] = browser_note = found
        save_state(st_path, st)
        if not a.json:
            print(f"[render] Chrome download blocked: using the installed browser at {found}", flush=True)
        run = Run(cmd, env, comp, log_path, deadline, st, st_path, a.json)
        run.saved = lambda: saved_frames(comp, seg)[0]
        code = run.go()
        text = "\n".join(run.tail)

    sp = run.speed()
    if sp:
        st["fps"] = round(sp, 2)
    if run.total:
        st["frames_total"] = run.total
    elapsed = time.time() - t0

    if code == 0 and os.path.exists(partial):
        if os.path.exists(out):
            fail(f"{out} appeared while rendering. The finished render is kept as {partial}: rename it to the next version.")
        for attempt in range(5):  # Windows: a virus scanner or indexer can hold the new file for a moment
            try:
                os.replace(partial, out)
                break
            except PermissionError:
                if attempt == 4:
                    fail(f"the render finished but couldn't be renamed. It is at {partial}: rename it by hand.")
                time.sleep(1.5)
        info = probe(out)
        rep = {"status": "RENDER_DONE", "out": out, "seconds": (info or {}).get("seconds"),
               "frames": (info or {}).get("frames"), "audio": (info or {}).get("audio"), "calls": st["calls"],
               "capture_fps": st.get("fps"), "this_call_s": round(elapsed, 1), "hyperframes": version,
               "browser": browser_note, "workers": workers or "auto"}
        for leftover in (st_path, log_path):
            try:
                os.remove(leftover)
            except OSError:
                pass
        if a.json:
            print(json.dumps(rep, indent=2))
        else:
            if info:
                print(f"RENDER_DONE {out} | {info['seconds']} s, {info['frames']} frames, "
                      f"audio {'yes' if info['audio'] else 'NO'} | {st['calls']} call(s)"
                      + (f", {st['fps']} fps capture" if st.get("fps") else ""))
            else:
                print(f"RENDER_DONE {out} | {st['calls']} call(s)")
                print("WARNING: " + ("ffprobe couldn't read the file: check it before delivering." if info is not None
                                     else "ffprobe not found, so the file wasn't checked."))
            print("NEXT: python qa_check.py on this file (references/qa.md).")
        return

    if run.stopped_for_budget:
        done, total = saved_frames(comp, seg)
        total = total or run.total or st.get("frames_total", 0)
        fps = st.get("fps")
        gained = done - before
        st["stalled"] = 0 if gained > 0 else int(st.get("stalled", 0)) + 1
        hint = ""
        if gained <= 0:
            if workers != "1":
                # Several workers render several segments at once, so a short call can end with none finished.
                st["single_worker"] = True
                hint = ("No segment was finished in this call: with several workers, several segments are in work "
                        "at once and none was complete yet. The next call uses 1 worker, which finishes them "
                        "one after another.")
            elif run.total and not run.segmented:
                need = int(run.total / fps * 1.3 + 60) if fps else None
                hint = ("No segment was saved: this composition renders on a HyperFrames route that can't be "
                        "resumed (e.g. shader transitions). It has to finish in one call"
                        + (f": about {need} s. Run again with --budget {need} and a tool time limit above that."
                           if need else ". Raise --budget."))
            elif not run.total:
                hint = ("No frame was captured: the budget ended during start-up. Run again with --budget 120 or "
                        "more (and a tool time limit above it).")
            else:
                startup = (run.first_frame_at - run.began) if run.first_frame_at else 0
                per = seg / fps if fps else None
                need = int(startup + 2 * per + STOP_MARGIN + 15) if per else 120
                hint = (f"No segment finished in this call (start-up about {startup:.0f} s"
                        + (f", one {seg}-frame segment about {per:.0f} s" if per else "")
                        + f"). Run again with --budget {max(need, 60)} or more (and a tool time limit above it).")
        save_state(st_path, st)
        left = max(0, total - done)
        eta = int(left / fps) if fps and total else None
        calls_left = None
        if eta is not None and a.budget > 0:
            usable = max(10.0, a.budget - STOP_MARGIN - 20)
            calls_left = max(1, int(eta / usable + 0.999))
        rep = {"status": "RENDER_INCOMPLETE", "out": out, "frames_saved": done, "frames_total": total,
               "capture_fps": fps, "seconds_left_estimate": eta, "calls_left_estimate": calls_left,
               "calls": st["calls"], "hint": hint}
        if st["stalled"] >= 3:
            fail(f"3 calls in a row saved nothing. {hint}")
        if a.json:
            print(json.dumps(rep, indent=2))
        else:
            pct = f" ({100 * done // total}%)" if total else ""
            print(f"RENDER_INCOMPLETE {done}/{total or '?'} frames saved{pct}"
                  + (f" | {fps} fps capture" if fps else "")
                  + (f" | about {eta} s of rendering left (~{calls_left} more call(s))" if eta is not None else ""))
            if hint:
                print("NOTE: " + hint)
            print("NEXT: run the SAME command again, in the foreground. It resumes; saved frames aren't re-rendered.")
        sys.exit(3)

    save_state(st_path, st)
    why = "HyperFrames exited with an error"
    if "404 Not Found: /node_modules" in text:
        why = "the composition couldn't load a library from node_modules (run `npm install` in the composition)"
    elif "COMPOSITION_SETUP_TIMEOUT" in text or "did not finish within" in text:
        why = "the composition never became ready (a script error or a missing asset: read the lines below)"
    fail(why, run.tail, log_path)


if __name__ == "__main__":
    main()
