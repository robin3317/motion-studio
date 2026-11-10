#!/usr/bin/env python3
"""motion-studio update check: fast, silent on failure, throttled, no telemetry.

Usage (run at skill start, any working directory):
    python update_check.py              # prints one status line (or nothing)
    python update_check.py --force      # ignore the throttle and snooze, check now; never silent
    python update_check.py --notes      # print the changelog entries newer than the installed version
    python update_check.py --snooze 1d  # remind later: 1d, 7d (or Nh)
    python update_check.py --never      # never check again (undo with --reset)
    python update_check.py --reset      # clear snooze/never and the cache
    python update_check.py --json       # machine-readable status

Output (first word is the status):
    UPDATE_AVAILABLE <local> <latest> <method>     then lines:  COMMAND: ...  /  NOTES: <url>
    UP_TO_DATE <local>
    CHECK_FAILED <why>                            only with --force or --json: no source could be reached
    (nothing)                                     when disabled, snoozed, offline or the check failed

What it does: reads the installed version from SKILL.md and asks for the newest version of
robin3317/motion-studio, at most once every 24 h (cached). It tries two sources in order:
  1. GitHub Releases API (pre-releases included)
  2. raw.githubusercontent.com: .claude-plugin/plugin.json on main (same version as the latest release)
Source 2 exists because some sandboxes (e.g. Claude Cowork's cloud) block api.github.com but allow
raw.githubusercontent.com. Each request has a 3 s timeout. It sends nothing about the user.
Disable with MOTION_STUDIO_NO_UPDATE_CHECK=1. State lives in ~/.cache/motion-studio/update-state.json.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

for _stream in (sys.stdout, sys.stderr):  # Windows pipes use a legacy code page: "→" in the notes would crash
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

REPO = "robin3317/motion-studio"
MARKETPLACE = "codeonces"
PLUGIN = "motion-studio"
RAW = f"https://raw.githubusercontent.com/{REPO}/main"
API = os.environ.get("MOTION_STUDIO_RELEASES_URL", f"https://api.github.com/repos/{REPO}/releases?per_page=10")
MANIFEST = os.environ.get("MOTION_STUDIO_MANIFEST_URL", f"{RAW}/.claude-plugin/plugin.json")
CHANGELOG = os.environ.get("MOTION_STUDIO_CHANGELOG_URL", f"{RAW}/CHANGELOG.md")
CHANGELOG_PAGE = f"https://github.com/{REPO}/blob/main/CHANGELOG.md"
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
STATE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "motion-studio")
STATE = os.path.join(STATE_DIR, "update-state.json")
THROTTLE = 24 * 3600
TIMEOUT = 3


def local_version():
    try:
        with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as f:
            head = f.read(4000)
        m = re.search(r"^\s*version:\s*([0-9][^\s]*)\s*$", head, re.M)
        return m.group(1) if m else None
    except OSError:
        return None


def parse(v):
    """Semver-ish key: 0.1.0-beta < 0.1.0-beta.2 < 0.1.0 < 0.2.0-beta."""
    v = v.lstrip("vV")
    core, _, pre = v.partition("-")
    nums = [int(x) if x.isdigit() else 0 for x in core.split(".")[:3]]
    nums += [0] * (3 - len(nums))
    if not pre:
        return (nums, (1,))
    parts = tuple((0, int(p)) if p.isdigit() else (1, p) for p in re.split(r"[.]", pre))
    return (nums, (0,) + parts)


def newer(a, b):
    return parse(a) > parse(b)


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(st):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=2)
    except OSError:
        pass


def get_text(url, accept="*/*"):
    """Fetch a URL (or a file:// path, used by the tests) as text."""
    if url.startswith("file://"):
        path = url[7:]
        if re.match(r"^/[A-Za-z]:", path):  # file:///C:/...
            path = path[1:]
        with open(path, encoding="utf-8-sig") as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": "motion-studio-update-check", "Accept": accept})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8-sig")


def from_releases():
    """Newest published release (pre-releases included), or None if the repo has none."""
    rels = json.loads(get_text(API, "application/vnd.github+json"))
    best = None
    for rel in rels:
        if rel.get("draft"):
            continue
        tag = rel.get("tag_name") or ""
        if not re.match(r"^v?\d+\.\d+", tag):
            continue
        if best is None or newer(tag, best["tag"]):
            best = {"tag": tag, "url": rel.get("html_url"), "name": rel.get("name") or tag, "source": "releases"}
    return best


def from_manifest():
    """Version in .claude-plugin/plugin.json on main. It changes only in the release commit."""
    version = str(json.loads(get_text(MANIFEST)).get("version") or "")
    if not re.match(r"^\d+\.\d+", version):
        raise ValueError("no version in plugin.json")
    return {"tag": "v" + version, "url": CHANGELOG_PAGE, "name": "v" + version, "source": "manifest"}


def why(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return f"unreachable ({exc.reason})"
    return exc.__class__.__name__


def fetch_latest():
    """Try each source in order. Returns (latest or None, [reasons the earlier sources failed])."""
    errors = []
    for name, fn in (("releases", from_releases), ("manifest", from_manifest)):
        try:
            latest = fn()
        except Exception as exc:  # noqa: BLE001  offline, blocked, rate-limited, repo moved
            errors.append(f"{name}: {why(exc)}")
            continue
        if latest:
            return latest, errors
        errors.append(f"{name}: no published release")
    return None, errors


def notes_since(local):
    """Changelog sections for versions newer than `local` (newest first), as text. '' if none."""
    text = get_text(CHANGELOG)
    out, keep = [], False
    for line in text.splitlines():
        m = re.match(r"^##\s+v?(\d+\.\d+[^\s:(]*)", line)
        if m:
            keep = newer(m.group(1), local)
        elif line.startswith("# "):
            continue
        if keep:
            out.append(line)
    return "\n".join(out).strip()


def install_method():
    p = SKILL_DIR.replace("\\", "/").lower()
    root = os.path.dirname(os.path.dirname(SKILL_DIR))  # repo root when installed from git/plugin
    if ("/.claude/plugins/" in p or "/plugins/cache/" in p or "/plugins/marketplaces/" in p
            or os.environ.get("CLAUDE_PLUGIN_ROOT")):
        return "plugin", (f"claude plugin marketplace update {MARKETPLACE} && "
                          f"claude plugin update {PLUGIN}@{MARKETPLACE}   (then /reload-plugins)")
    if os.path.isdir(os.path.join(root, ".git")):
        return "git", f'git -C "{root}" pull --ff-only'
    if "/.agents/skills/" in p:
        return "skills-cli", f"npx skills add {REPO}"
    return "zip", f"Download the new skill ZIP from https://github.com/{REPO}/releases and upload it again"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--notes", action="store_true")
    ap.add_argument("--snooze")
    ap.add_argument("--never", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    st = load_state()
    now = time.time()
    if a.reset:
        save_state({})
        print("update check reset")
        return
    if a.never:
        st["never"] = True
        save_state(st)
        print("update check disabled (python update_check.py --reset to undo)")
        return
    if a.snooze:
        m = re.fullmatch(r"(\d+)([dh])", a.snooze.strip())
        if not m:
            sys.exit("--snooze takes e.g. 1d, 7d or 12h")
        secs = int(m.group(1)) * (86400 if m.group(2) == "d" else 3600)
        st["snooze_until"] = now + secs
        save_state(st)
        print(f"update reminder snoozed for {a.snooze}")
        return

    local = local_version()
    if a.notes:
        if not local:
            sys.exit("NOTES_UNAVAILABLE installed version not found in SKILL.md")
        try:
            text = notes_since(local)
        except Exception as exc:  # noqa: BLE001
            sys.exit(f"NOTES_UNAVAILABLE {why(exc)} (read {CHANGELOG_PAGE} instead)")
        print(text or f"No changelog entries newer than {local}.")
        return

    if os.environ.get("MOTION_STUDIO_NO_UPDATE_CHECK") and not a.force:
        return
    if st.get("never") and not a.force:
        return
    if st.get("snooze_until", 0) > now and not a.force:
        return
    if not local:
        return

    latest = st.get("latest") if (now - st.get("checked_at", 0) < THROTTLE and not a.force) else None
    if latest is None:
        latest, errors = fetch_latest()
        if latest is None and errors:  # nothing reachable: stay silent unless asked directly
            if a.json:
                print(json.dumps({"status": "CHECK_FAILED", "local": local, "errors": errors}, indent=2))
            elif a.force:
                print("CHECK_FAILED " + "; ".join(errors))
            return
        st.update({"checked_at": now, "latest": latest})
        save_state(st)
    if not latest:
        return

    method, cmd = install_method()
    status = "UPDATE_AVAILABLE" if newer(latest["tag"], local) else "UP_TO_DATE"
    if a.json:
        print(json.dumps({"status": status, "local": local, "latest": latest["tag"].lstrip("vV"),
                          "method": method, "command": cmd, "notes": latest.get("url"),
                          "source": latest.get("source", "releases")}, indent=2))
        return
    if status == "UP_TO_DATE":
        print(f"UP_TO_DATE {local}")
        return
    print(f"UPDATE_AVAILABLE {local} {latest['tag'].lstrip('vV')} {method}")
    print(f"COMMAND: {cmd}")
    if latest.get("url"):
        print(f"NOTES: {latest['url']}")


if __name__ == "__main__":
    main()
