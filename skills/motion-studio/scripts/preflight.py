#!/usr/bin/env python3
"""motion-studio preflight: READ-ONLY inventory of the tools the skill needs.

Installs nothing, downloads nothing, prints no secret values.

Usage:
    python preflight.py            # human-readable report
    python preflight.py --json     # machine-readable report
Exit code: 0 if all required items pass, 1 otherwise.
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
from _common import which  # noqa: E402

HF_SKILLS = ["hyperframes", "hyperframes-cli", "media-use"]


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

    # HyperFrames CLI (no download: --no-install)
    hf_ver = None
    npx = which("npx")
    if npx:
        try:
            r = subprocess.run([npx, "--no-install", "hyperframes", "--version"], capture_output=True,
                               text=True, timeout=60, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                hf_ver = (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else "ok"
        except Exception:  # noqa: BLE001
            pass
    add("HyperFrames CLI (cached)", bool(hf_ver), hf_ver or "not cached yet",
        required=False, fix="First `npx hyperframes ...` run downloads it; fine to proceed")

    # HyperFrames skills
    found = find_hf_skills()
    for name in HF_SKILLS:
        add(f"skill /{name}", name in found, found.get(name, "not found in common locations"),
            fix="User runs: npx hyperframes skills update  (or installs the HyperFrames plugin)")

    # Optional tools
    add("Playwright (optional, site screenshots)", node_module_available("playwright"),
        "resolvable from this folder" if node_module_available("playwright") else "not resolvable here",
        required=False, fix="npm i -D playwright && npx playwright install chromium")
    add("Docker (optional, reproducible renders)", bool(which("docker")), which("docker") or "not found",
        required=False)
    if os.environ.get("HYPERFRAMES_BROWSER_PATH"):
        add("HYPERFRAMES_BROWSER_PATH", os.path.exists(os.environ["HYPERFRAMES_BROWSER_PATH"]),
            "set", required=False)

    # Keys: presence only, never values
    for key in ("ELEVENLABS_API_KEY", "HEYGEN_API_KEY"):
        add(f"{key} (optional, paid APIs)", bool(os.environ.get(key)),
            "set" if os.environ.get(key) else "not set", required=False)

    report = {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "ok": all(c["ok"] for c in checks if c["required"]),
        "checks": checks,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"motion-studio preflight  |  {report['os']}")
        for c in checks:
            mark = "OK " if c["ok"] else ("MISSING" if c["required"] else "-- ")
            tag = "" if c["required"] else " (optional)" if "optional" not in c["name"] else ""
            print(f"  [{mark:7}] {c['name']}{tag}: {c['detail']}")
            if not c["ok"] and c["fix"]:
                print(f"            fix: {c['fix']}")
        print("\nRESULT:", "ready" if report["ok"] else "missing required items (see references/setup.md)")
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
