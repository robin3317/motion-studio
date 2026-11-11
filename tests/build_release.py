#!/usr/bin/env python3
"""Build the two release ZIPs into dist/ (stdlib only).

    python tests/build_release.py            # writes dist/motion-studio-skill-v<V>.zip and -plugin-v<V>.zip

- Skill ZIP: skills/motion-studio/ as the top folder "motion-studio/" (for Settings → Capabilities → Skills).
- Plugin ZIP: the repository as "motion-studio/", without dist/, tests/renders/, docs/_references-bundle.md,
  node_modules, caches and .git.
It first checks that the version is the same in .claude-plugin/plugin.json and both SKILL.md files, and that
CHANGELOG.md has a section for it. Run it after `python tests/regression.py --record`, so the ZIP carries
this machine's test result (docs/RELEASING.md).
"""
import json
import os
import re
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "dist", "node_modules", "__pycache__", ".hyperframes", ".pytest_cache"}
SKIP_FILES = {".DS_Store", "Thumbs.db", ".env"}
SKIP_PATHS = {"tests/renders", "docs/_references-bundle.md"}


def files_under(root):
    out = []
    for base, dirs, files in os.walk(root):
        rel_base = os.path.relpath(base, REPO).replace(os.sep, "/")
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS
                         and (rel_base + "/" + d).lstrip("./") not in SKIP_PATHS)
        for fn in sorted(files):
            rel = (rel_base + "/" + fn).lstrip("./") if rel_base != "." else fn
            if fn in SKIP_FILES or fn.endswith(".pyc") or rel in SKIP_PATHS:
                continue
            out.append(os.path.join(base, fn))
    return out


def skill_version(path):
    with open(path, encoding="utf-8") as f:
        m = re.search(r"^\s*version:\s*(\S+)", f.read(), re.M)
    return m.group(1) if m else None


def write_zip(path, files, root):
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            z.write(f, "motion-studio/" + os.path.relpath(f, root).replace(os.sep, "/"))
    os.replace(tmp, path)
    return len(files), os.path.getsize(path)


def main():
    with open(os.path.join(REPO, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        version = json.load(f)["version"]
    skill = os.path.join(REPO, "skills", "motion-studio")
    found = {"plugin.json": version,
             "skills/motion-studio/SKILL.md": skill_version(os.path.join(skill, "SKILL.md")),
             "skills/motion-studio-upgrade/SKILL.md": skill_version(os.path.join(REPO, "skills", "motion-studio-upgrade", "SKILL.md"))}
    if len(set(found.values())) != 1:
        sys.exit("BUILD_FAILED the version differs between files: " + json.dumps(found))
    with open(os.path.join(REPO, "CHANGELOG.md"), encoding="utf-8") as f:
        if not re.search(r"^## " + re.escape(version) + r"\b", f.read(), re.M):
            sys.exit(f"BUILD_FAILED CHANGELOG.md has no '## {version}' section.")
    dist = os.path.join(REPO, "dist")
    os.makedirs(dist, exist_ok=True)
    s_zip = os.path.join(dist, f"motion-studio-skill-v{version}.zip")
    p_zip = os.path.join(dist, f"motion-studio-plugin-v{version}.zip")
    n1, b1 = write_zip(s_zip, files_under(skill), skill)
    n2, b2 = write_zip(p_zip, files_under(REPO), REPO)
    for z in (s_zip, p_zip):
        with zipfile.ZipFile(z) as zf:
            bad = zf.testzip()
            names = zf.namelist()
            if bad or "motion-studio/SKILL.md" not in names and "motion-studio/.claude-plugin/plugin.json" not in names:
                sys.exit(f"BUILD_FAILED {z} is not valid (bad member: {bad}).")
    print(f"BUILD_DONE v{version}\n  {s_zip}  ({n1} files, {b1 / 1e6:.1f} MB)\n  {p_zip}  ({n2} files, {b2 / 1e6:.1f} MB)")
    notes = os.path.join(dist, f"release-notes-v{version}.md")
    print("  release notes: " + (notes if os.path.isfile(notes) else "MISSING: write " + notes))


if __name__ == "__main__":
    main()
