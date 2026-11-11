"""Shared helpers for motion-studio scripts (stdlib only)."""
import glob
import json
import os
import shutil
import subprocess
import sys

# HyperFrames version this skill release was tested with (tests/regression.py). new_project.py pins it
# in each project's package.json; render.py and preflight.py fall back to it. To try a newer one before
# changing this line: MOTION_STUDIO_HF_VERSION=x.y.z python tests/regression.py
HF_VERSION = os.environ.get("MOTION_STUDIO_HF_VERSION") or "0.9.26"


def utf8_console():
    """Print as UTF-8 everywhere. On Windows, output that goes to a pipe uses a legacy code page by
    default, and printing a character like "≥" or "✗" would stop the script with UnicodeEncodeError."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


utf8_console()


def which(name):
    """Return the executable path for name, honouring MS_FFMPEG / MS_FFPROBE overrides."""
    env = {"ffmpeg": "MS_FFMPEG", "ffprobe": "MS_FFPROBE"}.get(name)
    if env and os.environ.get(env):
        return os.environ[env]
    return shutil.which(name)


def run(cmd, check=True, capture=True, timeout=None):
    """Run a command list and return CompletedProcess (text mode)."""
    return subprocess.run(cmd, check=check, capture_output=capture, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def need(name):
    path = which(name)
    if not path:
        sys.exit(f"[motion-studio] '{name}' not found on PATH. Run scripts/preflight.py and see references/setup.md.")
    return path


def ffprobe_json(path):
    out = run([need("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", path]).stdout
    return json.loads(out)


def decode_audio(path, sr=48000, channels=2):
    """Decode any audio/video file to float32 numpy array shape (n, channels) via ffmpeg."""
    import numpy as np
    cmd = [need("ffmpeg"), "-v", "error", "-i", path, "-vn", "-f", "f32le",
           "-acodec", "pcm_f32le", "-ac", str(channels), "-ar", str(sr), "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    data = np.frombuffer(raw, dtype=np.float32)
    return data.reshape(-1, channels).copy()


def measure_loudness(path):
    """(integrated LUFS, true peak dBTP) of any audio/video file via FFmpeg ebur128. None where unmeasurable."""
    import re
    p = run([need("ffmpeg"), "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true",
             "-f", "null", "-"], check=False)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    return (float(i.group(1)) if i else None, float(tp.group(1)) if tp and tp.group(1) != "-inf" else None)


def write_wav(path, data, sr=48000):
    """Write float array (n, ch) or (n,) to 16-bit PCM WAV with the stdlib wave module."""
    import numpy as np
    import wave
    a = np.asarray(data, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    a = np.clip(a, -1.0, 1.0)
    pcm = (a * 32767.0).astype("<i2")
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(a.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def db_to_gain(db):
    return 10.0 ** (db / 20.0)


def dump(obj, path=None):
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    return text


def find_browser():
    """Path of an installed Chrome/Chromium (Edge as a last resort) that HyperFrames can drive, or None.

    Used when HyperFrames can't download its own chrome-headless-shell (blocked network): set
    HYPERFRAMES_BROWSER_PATH to this path. Read-only: looks at well-known locations, runs nothing.
    """
    cands = [os.environ.get(k) for k in ("HYPERFRAMES_BROWSER_PATH", "PUPPETEER_EXECUTABLE_PATH", "CHROME_PATH")]
    for name in ("chrome-headless-shell", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        cands.append(shutil.which(name))
    home = os.path.expanduser("~")
    # Playwright's Chromium: <root>/chromium-<revision>/<platform folder>/<exact binary>
    if sys.platform == "darwin":
        cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  "/Applications/Chromium.app/Contents/MacOS/Chromium",
                  os.path.join(home, "Applications/Google Chrome.app/Contents/MacOS/Google Chrome")]
        pw_root = os.path.join(home, "Library", "Caches", "ms-playwright")
        pw_tails = [os.path.join("chrome-mac*", "Chromium.app", "Contents", "MacOS", "Chromium"),
                    os.path.join("chrome-mac*", "Google Chrome for Testing.app", "Contents", "MacOS",
                                 "Google Chrome for Testing")]
        edge = ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    elif os.name == "nt":
        bases = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        bases = [b for b in bases if b]
        cands += [os.path.join(b, "Google", "Chrome", "Application", "chrome.exe") for b in bases]
        cands += [os.path.join(b, "Chromium", "Application", "chrome.exe") for b in bases]
        pw_root = os.path.join(os.environ.get("LOCALAPPDATA", home), "ms-playwright")
        pw_tails = [os.path.join("chrome-win*", "chrome.exe")]
        edge = [os.path.join(b, "Microsoft", "Edge", "Application", "msedge.exe") for b in bases]
    else:
        pw_root = os.path.join(home, ".cache", "ms-playwright")
        pw_tails = [os.path.join("chrome-linux*", "chrome")]
        edge = [shutil.which("microsoft-edge"), shutil.which("microsoft-edge-stable")]

    def revision(path):  # newest Playwright revision first (chromium-1200 before chromium-999)
        digits = "".join(ch for ch in os.path.basename(path).split("-")[-1] if ch.isdigit())
        return int(digits or 0)
    for root in (os.environ.get("PLAYWRIGHT_BROWSERS_PATH"), pw_root):
        if not root:
            continue
        for rev_dir in sorted(glob.glob(os.path.join(root, "chromium-*")), key=revision, reverse=True):
            for tail in pw_tails:
                cands += glob.glob(os.path.join(rev_dir, tail))
    cands += edge
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


# ---------- HyperFrames helpers shared by render.py, preview_sheet.py and visual_audit.py ----------

def composition_dir(arg=None):
    """Absolute path of the composition folder: --composition, ./composition, or . if it has index.html."""
    comp = os.path.abspath(arg or ("composition" if os.path.isdir("composition") else "."))
    if not os.path.isfile(os.path.join(comp, "index.html")):
        sys.exit(f"[motion-studio] no index.html in {comp} (run from the project folder or pass --composition)")
    return comp


def pinned_hf_version(comp):
    """HyperFrames version pinned in the composition's package.json, else this skill's tested version."""
    import re
    try:
        with open(os.path.join(comp, "package.json"), encoding="utf-8") as f:
            m = re.search(r"hyperframes@(\d+\.\d+\.\d+)", f.read())
        return m.group(1) if m else HF_VERSION
    except OSError:
        return HF_VERSION


def hf_run(comp, args, timeout=None):
    """Run `npx hyperframes@<pinned> <args>` inside the composition, in the foreground.
    Uses an installed Chrome when HyperFrames reports it can't find one. Returns (exit code, stdout, stderr)."""
    npx = need("npx")
    cmd = [npx, "--yes", f"hyperframes@{pinned_hf_version(comp)}"] + [str(a) for a in args]
    env = dict(os.environ)
    for attempt in (1, 2):
        p = subprocess.run(cmd, cwd=comp, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
        if attempt == 1 and p.returncode != 0 and "Chrome not found" in (p.stdout + p.stderr) \
                and not env.get("HYPERFRAMES_BROWSER_PATH") and find_browser():
            env["HYPERFRAMES_BROWSER_PATH"] = find_browser()
            continue
        break
    return p.returncode, p.stdout, p.stderr


def json_from(text):
    """The first JSON object in a command's output (HyperFrames prints notices around it)."""
    start = text.find("{")
    if start < 0:
        return None
    try:
        return json.JSONDecoder().raw_decode(text[start:])[0]
    except ValueError:
        return None


def new_check_dir(project, name):
    """A new, empty folder renders/checks/<name>-vN in the project. Never reuses or clears an old one."""
    base = os.path.join(project, "renders", "checks")
    n = 1
    while os.path.exists(os.path.join(base, f"{name}-v{n}")):
        n += 1
    path = os.path.join(base, f"{name}-v{n}")
    os.makedirs(path)
    return path


def storyboard_scenes(project):
    """[(id, start, duration)] from storyboard.json, [] if it has none."""
    try:
        with open(os.path.join(project, "storyboard.json"), encoding="utf-8-sig") as f:
            scenes = json.load(f).get("scenes", [])
        return [(str(s.get("id", f"s{i + 1}")), float(s["start"]), float(s["duration"]))
                for i, s in enumerate(scenes) if "start" in s and "duration" in s]
    except (OSError, ValueError, TypeError, KeyError):
        return []


def film_seconds(comp):
    import re
    try:
        with open(os.path.join(comp, "index.html"), encoding="utf-8") as f:
            m = re.search(r'data-composition-id="[^"]*"[^>]*\bdata-duration="([\d.]+)"', f.read())
        return float(m.group(1)) if m else None
    except (OSError, ValueError):
        return None
