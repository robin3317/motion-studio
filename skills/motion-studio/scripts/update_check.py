#!/usr/bin/env python3
"""motion-studio update check: fast, silent on failure, throttled, no telemetry.

Usage (run at skill start, any working directory):
    python update_check.py              # prints one status line (or nothing)
    python update_check.py --force      # ignore the throttle and snooze, check now
    python update_check.py --snooze 1d  # remind later: 1d, 7d (or Nh)
    python update_check.py --never      # never check again (undo with --reset)
    python update_check.py --reset      # clear snooze/never and the cache
    python update_check.py --json       # machine-readable status

Output (first word is the status):
    UPDATE_AVAILABLE <local> <latest> <method>     then lines:  COMMAND: ...  /  NOTES: <release url>
    UP_TO_DATE <local>
    (nothing)                                     when disabled, snoozed, offline or the check failed

What it does: reads the installed version from SKILL.md, asks GitHub for the newest release of
robin3317/motion-studio (pre-releases included), at most once every 24 h (cached), 3 s timeout.
It sends nothing about the user. Disable with MOTION_STUDIO_NO_UPDATE_CHECK=1.
State lives in ~/.cache/motion-studio/update-state.json.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

REPO = "robin3317/motion-studio"
MARKETPLACE = "codeonces"
PLUGIN = "motion-studio"
API = os.environ.get("MOTION_STUDIO_RELEASES_URL", f"https://api.github.com/repos/{REPO}/releases?per_page=10")
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
STATE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "motion-studio")
STATE = os.path.join(STATE_DIR, "update-state.json")
THROTTLE = 24 * 3600


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


def fetch_latest():
    if API.startswith("file://"):
        with open(API[7:], encoding="utf-8") as f:
            rels = json.load(f)
    else:
        req = urllib.request.Request(API, headers={"User-Agent": "motion-studio-update-check",
                                                   "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=3) as r:
            rels = json.loads(r.read().decode("utf-8"))
    best = None
    for rel in rels:
        if rel.get("draft"):
            continue
        tag = rel.get("tag_name") or ""
        if not re.match(r"^v?\d+\.\d+", tag):
            continue
        if best is None or newer(tag, best["tag"]):
            best = {"tag": tag, "url": rel.get("html_url"), "name": rel.get("name") or tag}
    return best


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

    if os.environ.get("MOTION_STUDIO_NO_UPDATE_CHECK") and not a.force:
        return
    if st.get("never") and not a.force:
        return
    if st.get("snooze_until", 0) > now and not a.force:
        return

    local = local_version()
    if not local:
        return
    latest = st.get("latest") if (now - st.get("checked_at", 0) < THROTTLE and not a.force) else None
    if latest is None:
        try:
            latest = fetch_latest()
        except Exception:  # offline, rate-limited, repo moved: stay silent
            return
        st.update({"checked_at": now, "latest": latest})
        save_state(st)
    if not latest:
        return

    method, cmd = install_method()
    status = "UPDATE_AVAILABLE" if newer(latest["tag"], local) else "UP_TO_DATE"
    if a.json:
        print(json.dumps({"status": status, "local": local, "latest": latest["tag"].lstrip("vV"),
                          "method": method, "command": cmd, "notes": latest.get("url")}, indent=2))
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
