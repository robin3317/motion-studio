#!/usr/bin/env python3
"""motion-studio preflight: READ-ONLY inventory of the tools the skill needs, and of the host's limits.

Installs nothing, downloads nothing, prints no secret values.

Usage:
    python preflight.py            # human-readable report
    python preflight.py --json     # machine-readable report
    python preflight.py --no-net   # skip the reachability checks (6 one-byte requests, 3 s timeout, in parallel)
Exit code: 0 if all required items pass, 1 otherwise.

Besides the tools, it reports what this host can't do, so you can plan around it up front:
CPU cores, memory, GPU, an installed Chrome to use when HyperFrames' own download is blocked,
where the HyperFrames skills are (also the copies bundled inside the CLI), and which sites
this machine can reach (npm, Chrome download, GitHub, Hugging Face, the open web).
"""
import argparse
import glob
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _common import HF_VERSION, find_browser, which  # noqa: E402

HF_SKILLS = ["hyperframes", "hyperframes-cli", "media-use"]
REACH = [  # (label, url, what it is for, what to do when blocked)
    ("npm registry", "https://registry.npmjs.org/-/ping", "npx hyperframes, npm install",
     "nothing can be installed here: use a machine with npm access"),
    ("Chrome download", "https://storage.googleapis.com/chrome-for-testing-public/LATEST_RELEASE_STABLE",
     "HyperFrames' own Chrome", "fine if a Chrome is installed: scripts/render.py uses it automatically"),
    ("GitHub API", "https://api.github.com/repos/robin3317/motion-studio/releases?per_page=1", "update check (first source)",
     "fine: update_check.py falls back to raw.githubusercontent.com"),
    ("GitHub raw", "https://raw.githubusercontent.com/robin3317/motion-studio/main/.claude-plugin/plugin.json",
     "update check (fallback), HyperFrames registry blocks",
     "no update notices or registry blocks here"),
    ("Hugging Face models", "https://huggingface.co/Systran/faster-whisper-tiny/resolve/main/model.bin",
     "speech and cut-out model downloads (transcription, rembg)",
     "run transcription on the user's machine, or ask for a transcript/model file"),
    ("Open web", "https://example.com/", "website capture for facts, logo and screenshots",
     "capture the site on the user's machine or ask for screenshots (references/data-gathering.md)"),
]


def version_of(cmd, args=("--version",), timeout=20):
    path = which(cmd) if not os.path.isabs(cmd) else cmd
    if not path:
        return None, None
    try:
        out = subprocess.run([path, *args], capture_output=True, text=True, timeout=timeout,
                             encoding="utf-8", errors="replace")
        text = (out.stdout or out.stderr).strip().splitlines()
        return path, (text[0] if text else "")
    except Exception as exc:  # noqa: BLE001
        return path, f"error: {exc.__class__.__name__}"


def parse_ver(text):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    return tuple(int(x or 0) for x in m.groups()) if m else None


def find_hf_skills():
    """Look for the official HyperFrames skills in common skill/plugin locations."""
    home = os.path.expanduser("~")
    roots = [
        os.path.join(home, ".claude", "skills"),
        os.path.join(home, ".claude", "plugins"),
        os.path.join(home, ".agents", "skills"),
        os.path.join(os.getcwd(), ".claude", "skills"),
        os.path.join(os.getcwd(), ".agents", "skills"),
    ]
    found = {}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for skill_md in glob.glob(os.path.join(root, "**", "SKILL.md"), recursive=True):
            name = os.path.basename(os.path.dirname(skill_md))
            if name in HF_SKILLS and name not in found:
                found[name] = os.path.dirname(skill_md)
    return found


def npm_cache_dir():
    if os.environ.get("npm_config_cache"):
        return os.environ["npm_config_cache"]
    npm = which("npm")
    if npm:
        try:
            r = subprocess.run([npm, "config", "get", "cache"], capture_output=True, text=True, timeout=20,
                               encoding="utf-8", errors="replace")
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip().splitlines()[-1]
        except Exception:  # noqa: BLE001
            pass
    return os.path.join(os.path.expanduser("~"), ".npm")


def find_hf_cli():
    """HyperFrames CLI packages already on disk: {version: package dir}. No download, no npx run."""
    dirs = glob.glob(os.path.join(npm_cache_dir(), "_npx", "*", "node_modules", "hyperframes"))
    for base in (os.getcwd(), os.path.join(os.getcwd(), "composition")):
        dirs.append(os.path.join(base, "node_modules", "hyperframes"))
    exe = which("hyperframes")
    if exe:
        real = os.path.realpath(exe)
        dirs.append(os.path.dirname(os.path.dirname(real)))
    found = {}
    for d in dirs:
        try:
            with open(os.path.join(d, "package.json"), encoding="utf-8") as f:
                found.setdefault(str(json.load(f).get("version")), d)
        except (OSError, ValueError):
            continue
    return found


def bundled_skills(cli_dirs):
    """The CLI ships its skills in dist/skills. Returns {skill: dir} from the newest CLI found."""
    for version in sorted(cli_dirs, key=lambda v: parse_ver(v) or (0,), reverse=True):
        root = os.path.join(cli_dirs[version], "dist", "skills")
        got = {n: os.path.join(root, n) for n in HF_SKILLS if os.path.isfile(os.path.join(root, n, "SKILL.md"))}
        if got:
            return got
    return {}


def memory_gb():
    try:
        if os.path.isfile("/proc/meminfo"):
            with open("/proc/meminfo", encoding="utf-8") as f:
                kb = int(re.search(r"MemTotal:\s+(\d+)", f.read()).group(1))
            return round(kb / 1048576, 1)
        if hasattr(os, "sysconf") and "SC_PHYS_PAGES" in os.sysconf_names:
            return round(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 2 ** 30, 1)
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
                    (n, ctypes.c_ulonglong) for n in ("ullTotalPhys", "ullAvailPhys", "ullTotalPageFile",
                                                      "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual",
                                                      "sullAvailExtendedVirtual")]
            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 2 ** 30, 1)
    except Exception:  # noqa: BLE001
        pass
    return None


def gpu_hint():
    """Best guess without launching a browser: (has_gpu or None if unknown, detail)."""
    if sys.platform == "darwin":
        return True, "macOS (Metal)"
    if os.name == "nt":
        return None, "not checked on Windows (render.py reports the real capture speed)"
    if which("nvidia-smi"):
        return True, "NVIDIA driver found"
    if glob.glob("/dev/dri/renderD*"):
        return True, "/dev/dri render node found"
    return False, "none found: WebGL/3D renders on the CPU (several times slower)"


def reach(url, timeout=3):
    import urllib.error
    import urllib.request
    try:
        # Range: ask for one byte only, so nothing is really downloaded (redirects to CDNs are followed).
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "motion-studio-preflight",
                                                                 "Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        # An HTTP answer means the host was reached. 407 is always a proxy. 403 is a block for the hosts
        # this skill needs (a filtering proxy, or GitHub's rate limit), except on Google's download
        # bucket, which answers 403/404 for a missing object while still being reachable.
        if e.code == 407:
            return False, "HTTP 407 (proxy)"
        if e.code == 403 and "storage.googleapis.com" not in url:
            return False, "HTTP 403"
        return True, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        reason = str(getattr(e, "reason", e))
        if "CERTIFICATE_VERIFY_FAILED" in reason:
            return False, "this Python can't verify TLS certificates, so the check is inconclusive"
        return False, (e.__class__.__name__ + (": " + reason[:60] if reason else ""))


def reach_all():
    import threading
    out = {}

    def one(label, url):
        out[label] = reach(url)
    threads = [threading.Thread(target=one, args=(label, url), daemon=True) for label, url, _, _ in REACH]
    for t in threads:
        t.start()
    for t in threads:
        t.join(5)
    return out


def node_module_available(name):
    node = which("node")
    if not node:
        return False
    try:
        r = subprocess.run([node, "-e", f"require.resolve('{name}')"], capture_output=True,
                           text=True, timeout=20, cwd=os.getcwd())
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--no-net", action="store_true", help="skip the reachability checks")
    args = ap.parse_args()

    checks = []

    def add(name, ok, detail, required=True, fix=""):
        checks.append({"name": name, "ok": bool(ok), "required": required, "detail": detail, "fix": fix})

    # Node
    path, ver = version_of("node")
    v = parse_ver(ver)
    add("Node.js >= 22", bool(v and v[0] >= 22), ver or "not found",
        fix="Install Node.js 22+ (see references/setup.md)")
    add("npx", bool(which("npx")), which("npx") or "not found", fix="Comes with Node.js")

    # FFmpeg
    for tool in ("ffmpeg", "ffprobe"):
        path, ver = version_of(tool, ("-version",))
        add(tool, bool(path), (ver or "not found")[:80], fix="Install FFmpeg (see references/setup.md)")

    # Python
    pv = sys.version_info
    add("Python >= 3.10", pv >= (3, 10), platform.python_version(), fix="Install Python 3.10+")
    add("numpy", importlib.util.find_spec("numpy") is not None,
        "installed" if importlib.util.find_spec("numpy") else "missing",
        fix="python -m pip install -r scripts/requirements.txt")
    add("rembg (optional, product cut-outs)", importlib.util.find_spec("rembg") is not None,
        "installed" if importlib.util.find_spec("rembg") else "missing", required=False,
        fix="python -m pip install rembg (ask the user first; downloads a model)")

    # HyperFrames CLI already on disk (no download)
    cli = find_hf_cli()
    versions = sorted(cli, key=lambda v: parse_ver(v) or (0,), reverse=True)
    add("HyperFrames CLI (cached)", bool(cli),
        (", ".join(versions) + ("" if HF_VERSION in cli else f" (this skill pins {HF_VERSION}: first run downloads it)"))
        if cli else "not cached yet",
        required=False, fix=f"First `npx hyperframes@{HF_VERSION} ...` run downloads it; fine to proceed")

    # HyperFrames skills: host skill folders first, then the copies bundled inside the CLI
    found = find_hf_skills()
    bundled = bundled_skills(cli)
    for name in HF_SKILLS:
        if name in found:
            add(f"skill /{name}", True, found[name])
        elif name in bundled:
            add(f"skill /{name}", True, "bundled with the CLI (not installed in the host): read "
                + os.path.join(bundled[name], "SKILL.md"))
        else:
            add(f"skill /{name}", False, "not found in skill folders or in a cached CLI",
                fix=f"Run `npx hyperframes@{HF_VERSION} --version` once (the CLI bundles the skills in dist/skills), "
                    "or the user runs: npx hyperframes skills update")

    # Chrome for rendering
    browser = find_browser()
    env_browser = os.environ.get("HYPERFRAMES_BROWSER_PATH")
    if env_browser:
        add("HYPERFRAMES_BROWSER_PATH", os.path.exists(env_browser), "set" if os.path.exists(env_browser)
            else "set, but the file doesn't exist", required=False)
    add("Installed Chrome (fallback for rendering)", bool(browser), browser or "none found", required=False,
        fix="Only needed if HyperFrames can't download its own Chrome. Install Chrome or Chromium")

    # Optional tools
    add("Playwright (optional, site screenshots)", node_module_available("playwright"),
        "resolvable from this folder" if node_module_available("playwright") else "not resolvable here",
        required=False, fix="npm i -D playwright && npx playwright install chromium")
    add("Docker (optional, reproducible renders)", bool(which("docker")), which("docker") or "not found",
        required=False)
    # Keys: presence only, never values
    for key in ("ELEVENLABS_API_KEY", "HEYGEN_API_KEY"):
        add(f"{key} (optional, paid APIs)", bool(os.environ.get(key)),
            "set" if os.environ.get(key) else "not set", required=False)

    # Host limits (information, never a failure)
    cores = os.cpu_count() or 0
    mem = memory_gb()
    gpu, gpu_detail = gpu_hint()
    limits = {"cpu_cores": cores, "memory_gb": mem, "gpu": gpu, "gpu_detail": gpu_detail,
              "browser_fallback": browser, "reachable": {}}
    notes = []
    if cores and cores <= 4:
        notes.append(f"{cores} CPU cores: render.py uses 1 worker here. Expect slow renders; keep previews at draft quality.")
    if gpu is False:
        notes.append("No GPU: 3D/WebGL scenes render on the CPU. Keep them light (references/three-d.md, Performance).")
    if not args.no_net:
        got = reach_all()
        for label, _url, used_for, when_blocked in REACH:
            ok, detail = got.get(label, (False, "timeout"))
            limits["reachable"][label] = ok
            add(f"reach: {label}", ok, f"{'reachable' if ok else 'BLOCKED'} ({detail}) | used for {used_for}",
                required=False, fix="" if ok else when_blocked)
        if not limits["reachable"].get("Chrome download") and not browser:
            notes.append("Chrome can't be downloaded and none is installed: rendering can't work on this machine yet.")
    notes.append("Renders: always `python scripts/render.py` in the foreground, never in the background. Give the "
                 "call your shell tool's longest time limit and pass --budget = that limit minus 60 s.")

    report = {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "ok": all(c["ok"] for c in checks if c["required"]),
        "checks": checks,
        "limits": limits,
        "notes": notes,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"motion-studio preflight  |  {report['os']}")
        for c in checks:
            mark = "OK " if c["ok"] else ("MISSING" if c["required"] else "-- ")
            tag = "" if c["required"] else " (optional)" if ("optional" not in c["name"] and not c["name"].startswith("reach:")) else ""
            print(f"  [{mark:7}] {c['name']}{tag}: {c['detail']}")
            if not c["ok"] and c["fix"]:
                print(f"            {'then' if c['name'].startswith('reach:') else 'fix'}: {c['fix']}")
        print(f"\nHOST: {cores or '?'} CPU cores | {mem if mem is not None else '?'} GB RAM | GPU: {gpu_detail}")
        for n in notes:
            print(f"  - {n}")
        if browser and not env_browser and not limits["reachable"].get("Chrome download", True):
            q = '"' if " " in browser else ""
            print(f"  - Chrome download is blocked. For raw `npx hyperframes` commands (check, snapshot) set:\n"
                  f"      HYPERFRAMES_BROWSER_PATH={q}{browser}{q}")
        print("\nRESULT:", "ready" if report["ok"] else "missing required items (see references/setup.md)")
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
