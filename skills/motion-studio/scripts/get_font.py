#!/usr/bin/env python3
"""Fetch a free (open-licence) font from npm's @fontsource into the composition, with its licence.

Usage (project folder as working directory):
    python get_font.py "Space Grotesk" --weights 500,700 --as Display
    python get_font.py "Hind Siliguri" --weights 400,700 --subsets bengali,latin --as Body
    python get_font.py "Fraunces" --list            # what the package offers; downloads nothing into the project

What it does:
- `npm pack @fontsource/<name>` (the npm registry is reachable even where font sites and CDNs are blocked;
  no install scripts run), then copies only the .woff2 files asked for, plus the LICENSE, into
  <composition>/assets/fonts/<name>/.
- Writes font-face.css there and prints it: paste the rules into index.html's <style>. With --as, the
  family is named "Display", "Body" or "Mono", which is what the templates' --font-* tokens point at.
  Each subset gets its unicode-range, so two scripts can share one family name.
- Adds the font to the project's credits.json (name, source, licence, attribution).

It never overwrites a font folder that already has the same files. On the user's own machine, ask
before the first download (critical rule 6). Brand fonts that are not free must come from the user.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _common import composition_dir  # noqa: E402

FREE = ("OFL", "Apache", "MIT", "UFL", "CC0")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def fetch(pkg, tmp):
    npm = shutil.which("npm")
    if not npm:
        sys.exit("FONT_FAILED npm not found. Install Node.js 22+ first (references/setup.md).")
    p = subprocess.run([npm, "pack", pkg, "--pack-destination", tmp], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180, shell=(os.name == "nt"))
    tgz = [f for f in os.listdir(tmp) if f.endswith(".tgz")]
    if p.returncode != 0 or not tgz:
        err = (p.stderr or p.stdout or "").strip().splitlines()
        why = next((x for x in err if "404" in x or "ENOTFOUND" in x or "ETIMEDOUT" in x or "ECONNRE" in x), err[0] if err else "no output")
        hint = ("That family is not on @fontsource under this name. Check the spelling at fontsource.org, or pick another family "
                "(references/typography-i18n.md)." if "404" in why else "Check the network: the npm registry must be reachable.")
        sys.exit(f"FONT_FAILED could not fetch {pkg}: {why[:160]}\n{hint}")
    return os.path.join(tmp, tgz[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("family", help='font family as on fontsource.org, e.g. "Space Grotesk"')
    ap.add_argument("--weights", default="400,700", help="comma-separated weights (default 400,700)")
    ap.add_argument("--subsets", default="latin", help="comma-separated subsets, e.g. latin,bengali (default latin)")
    ap.add_argument("--italic", action="store_true", help="also fetch the italic style")
    ap.add_argument("--as", dest="alias", help='CSS family name to use, e.g. Display, Body, Mono (default: the real name)')
    ap.add_argument("--composition", help="composition folder (default: ./composition)")
    ap.add_argument("--list", action="store_true", help="only show the weights, styles and subsets the package has")
    a = ap.parse_args()

    name = slug(a.family)
    if not name:
        sys.exit("FONT_FAILED give a font family name.")
    with tempfile.TemporaryDirectory(prefix="ms-font-") as tmp:
        tgz = fetch(f"@fontsource/{name}", tmp)
        with tarfile.open(tgz) as tar:
            members = {m.name: m for m in tar.getmembers() if m.isfile()}

            def read(path):
                m = members.get("package/" + path)
                return tar.extractfile(m).read() if m else None

            meta = json.loads(read("metadata.json") or b"{}")
            pkg = json.loads(read("package.json") or b"{}")
            ranges = json.loads(read("unicode.json") or b"{}")
            lic = (meta.get("license") or {})
            lic_type = lic.get("type") or pkg.get("license") or "unknown"
            have_w = [int(w) for w in meta.get("weights", [])]
            have_s = meta.get("subsets", [])
            have_st = meta.get("styles", ["normal"])
            family = meta.get("family") or a.family
            if a.list:
                print(f"{family} (@fontsource/{name}@{pkg.get('version', '?')}), licence {lic_type}")
                print(f"  weights: {have_w}\n  styles: {have_st}\n  subsets: {have_s}")
                return
            if not any(lic_type.upper().startswith(x.upper()) for x in FREE):
                sys.exit(f"FONT_FAILED {family} has licence '{lic_type}', which this script does not treat as free for video use. "
                         "Read the licence yourself, or pick another family.")
            weights = [int(w) for w in a.weights.split(",") if w.strip()]
            subsets = [s.strip() for s in a.subsets.split(",") if s.strip()]
            styles = ["normal"] + (["italic"] if a.italic else [])
            bad = [f"weight {w}" for w in weights if w not in have_w] + [f"subset {s}" for s in subsets if s not in have_s] \
                + [f"style {s}" for s in styles if s not in have_st]
            if bad:
                sys.exit(f"FONT_FAILED {family} has no {', '.join(bad)}.\n  weights: {have_w}\n  styles: {have_st}\n  subsets: {have_s}")

            comp = composition_dir(a.composition)
            dest = os.path.join(comp, "assets", "fonts", name)
            os.makedirs(dest, exist_ok=True)
            css_family = a.alias or family
            rules, files = [], []
            for subset in subsets:
                for w in weights:
                    for st in styles:
                        fn = f"{name}-{subset}-{w}-{st}.woff2"
                        data = read("files/" + fn)
                        if data is None:
                            sys.exit(f"FONT_FAILED the package has no file {fn}.")
                        path = os.path.join(dest, fn)
                        if not os.path.exists(path):
                            with open(path, "wb") as f:
                                f.write(data)
                        files.append(fn)
                        rng = f" unicode-range: {ranges[subset]};" if subset in ranges and len(subsets) > 1 else ""
                        rules.append(f'@font-face {{ font-family: "{css_family}"; src: url("assets/fonts/{name}/{fn}") format("woff2"); '
                                     f'font-weight: {w}; font-style: {st};{rng} }}')
            licence_text = read("LICENSE")
            if licence_text and not os.path.exists(os.path.join(dest, "LICENSE")):
                with open(os.path.join(dest, "LICENSE"), "wb") as f:
                    f.write(licence_text)
            with open(os.path.join(dest, "font-face.css"), "w", encoding="utf-8") as f:
                f.write(f"/* {family}, {lic_type}. {lic.get('attribution', '')} */\n" + "\n".join(rules) + "\n")

    project = os.path.dirname(comp)
    credits = os.path.join(project, "credits.json")
    credited = False
    if os.path.isfile(credits):
        try:
            with open(credits, encoding="utf-8") as f:
                items = json.load(f)
            if isinstance(items, list):
                src = f"npm @fontsource/{name}@{pkg.get('version', '?')}"
                if not any(isinstance(i, dict) and i.get("type") == "font" and i.get("name") == family for i in items):
                    items.append({"type": "font", "name": family, "source": src, "licence": lic_type,
                                  "licence_file": f"composition/assets/fonts/{name}/LICENSE",
                                  "attribution": lic.get("attribution", ""), "ai_generated": False, "files": files})
                    with open(credits, "w", encoding="utf-8") as f:
                        json.dump(items, f, indent=2, ensure_ascii=False)
                        f.write("\n")
                credited = True
        except (OSError, ValueError):
            pass

    print(f"FONT_DONE {family} ({lic_type}): {len(files)} file(s) in {dest}")
    print("Paste into the <style> of index.html (replacing the old rules of the same family):\n")
    print("\n".join(rules))
    token = {"display": "--font-display", "body": "--font-body", "mono": "--font-mono"}.get((a.alias or "").lower())
    if token:
        print(f'\nThe token {token} already points at "{css_family}".')
    else:
        print(f'\nThen use it: font-family: "{css_family}", sans-serif;  (or set it in the --font-* tokens)')
    print("credits.json: " + ("updated." if credited else "not found or not a list; add the font there yourself."))
    print("NEXT: render a still and look at the text, especially non-Latin scripts (references/typography-i18n.md).")


if __name__ == "__main__":
    main()
