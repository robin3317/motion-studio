#!/usr/bin/env python3
"""Search openly licensed music/SFX on Openverse and download a chosen track with its licence record.

Only licences that are safe for commercial promos are searched: CC0, Public Domain Mark, CC BY.
(NC, ND and SA licences are excluded: see references/audio.md.)

Usage:
    python find_music.py search "upbeat corporate" [--licence cc0|by|all] [--min 30] [--max 240]
                         [--sfx] [--source freesound] [--out plan/music_search.json]
    python find_music.py get <openverse-id> --to audio/music [--credits credits.json]

`search` prints a numbered table (title, author, length, licence, source page).
`get` downloads the file, appends an entry to credits.json (with the attribution line CC BY
requires), and refuses to overwrite existing files. Always open the source page and check that
the licence shown there matches before using a track in a delivery.
Network: needs api.openverse.org and the file host (e.g. cdn.freesound.org).
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API = "https://api.openverse.org/v1/audio/"
UA = "motion-studio-skill/0.1 (+https://github.com/robin3317/motion-studio)"
SAFE = {"cc0": "cc0", "pdm": "pdm", "by": "by"}


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def filter_results(data, min_s, max_s):
    rows = []
    for x in data.get("results", []):
        lic = (x.get("license") or "").lower()
        if lic not in SAFE:
            continue  # defence in depth: never pass NC/ND/SA through
        dur = (x.get("duration") or 0) / 1000.0
        if dur and (dur < min_s or dur > max_s):
            continue
        rows.append({
            "id": x.get("id"), "title": x.get("title"), "author": x.get("creator"),
            "duration": round(dur, 1), "licence": f"{lic.upper()} {x.get('license_version') or ''}".strip(),
            "licence_url": x.get("license_url"), "source": x.get("source"),
            "page": x.get("foreign_landing_url"), "file_url": x.get("url"),
            "filetype": x.get("filetype"), "tags": [t.get("name") for t in (x.get("tags") or [])][:10],
            "attribution": x.get("attribution"),
        })
    return rows


def cmd_search(a):
    lic = {"cc0": "cc0,pdm", "by": "by", "all": "cc0,pdm,by"}[a.licence]
    params = {"q": a.query, "license": lic, "page_size": 20, "format": "json"}
    if a.source:
        params["source"] = a.source
    if a.sfx:
        params["category"] = "sound_effect"
    data = get_json(API + "?" + urllib.parse.urlencode(params))
    rows = filter_results(data, a.min, a.max)
    for i, r in enumerate(rows, 1):
        print(f"{i:2}. {r['title'][:48]:48} | {r['author'][:18]:18} | {r['duration']:6}s | {r['licence']:8} | {r['page']}")
        print(f"    id: {r['id']}   tags: {', '.join(t for t in r['tags'] if t)}")
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
    if not rows:
        print("No safe-licence results. Try broader words (e.g. 'corporate', 'cinematic', 'lofi', 'piano').")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "track").lower()).strip("-")[:48] or "track"


def cmd_get(a):
    x = get_json(API + urllib.parse.quote(a.id) + "/?format=json")
    rows = filter_results({"results": [x]}, 0, 10 ** 9)
    if not rows:
        sys.exit(f"Refusing: licence '{x.get('license')}' is not CC0/PDM/BY.")
    r = rows[0]
    ext = (r["filetype"] or os.path.splitext(urllib.parse.urlparse(r["file_url"]).path)[1].lstrip(".") or "mp3")
    os.makedirs(a.to, exist_ok=True)
    dest = os.path.join(a.to, f"{slug(r['title'])}_{slug(r['author'])}.{ext}")
    if os.path.exists(dest):
        sys.exit(f"Refusing to overwrite {dest}")
    req = urllib.request.Request(r["file_url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        f.write(resp.read())
    entry = {"file": dest.replace("\\", "/"), "type": "music", "title": r["title"], "author": r["author"],
             "source": r["page"], "licence": r["licence"], "licence_url": r["licence_url"],
             "attribution": r["attribution"] if r["licence"].startswith("BY") else None,
             "openverse_id": r["id"], "ai_generated": False,
             "note": "Openverse preview/derivative file; verify licence on the source page."}
    if a.credits:
        data = []
        if os.path.exists(a.credits):
            with open(a.credits, encoding="utf-8") as f:
                data = json.load(f)
        data.append(entry)
        with open(a.credits, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    print(json.dumps(entry, indent=2, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--licence", choices=["cc0", "by", "all"], default="all")
    s.add_argument("--min", type=float, default=20)
    s.add_argument("--max", type=float, default=300)
    s.add_argument("--sfx", action="store_true", help="search sound effects instead of music")
    s.add_argument("--source", help="e.g. freesound, jamendo, ccmixter, wikimedia_audio")
    s.add_argument("--out")
    g = sub.add_parser("get")
    g.add_argument("id")
    g.add_argument("--to", default="audio/music")
    g.add_argument("--credits", default="credits.json")
    a = ap.parse_args()
    try:
        (cmd_search if a.cmd == "search" else cmd_get)(a)
    except urllib.error.URLError as e:
        sys.exit(f"Network error ({e}). Openverse/file host unreachable from this shell: "
                 "use the user's own track or ask them to download it.")


if __name__ == "__main__":
    main()
