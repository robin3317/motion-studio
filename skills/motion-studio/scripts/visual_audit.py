#!/usr/bin/env python3
"""Visual audit of a composition: every scene, every pill/tag/card/button, measured and cropped for review.

Usage (from the project folder; fill storyboard.json first so each scene is sampled):
    python visual_audit.py                       # audit at each scene's midpoint and near the end
    python visual_audit.py --at 1.5,7,19         # audit at exact times
    python visual_audit.py --selectors ".chip,.stat"   # extra component selectors
    python visual_audit.py --strict              # exit 1 on warnings too

What it does, all through HyperFrames' own page (so text and layout are exactly what renders):
  1. Runs `hyperframes check` at those times: lint, runtime errors, text overflow and overlap, contrast.
  2. Measures every visible component (.pill .tag .card .chip .badge .btn, button, [data-audit]):
     a label that wraps, text that overflows its box, text that is not centred in its box (measured
     on the letter shapes, not the line box), a box cut by the frame edge, the same class drawn in
     different sizes, and text that sits over a busy part of a 3D/WebGL canvas (which `check` can't see).
  3. Saves one still per time with HyperFrames' labelled contact sheets, and a sheet of enlarged crops
     of every component (the real frame, scaled up), numbered like the report. For a true 3x-density
     look at one element, use preview_sheet.py --zoom.
Everything goes into a NEW folder renders/checks/audit-vN (audit.json, audit.md, sheets). Your
composition is not touched: the measuring script runs in a temporary copy.

Then LOOK at the sheets. The numbers find candidates; only eyes decide whether a border, a radius
or a line of text looks right. Before a final render, give audit.md and the sheets to a fresh
reviewer (references/qa.md).

Exit code: 1 if HyperFrames reports an error (or, with --strict, if anything is flagged), else 0.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (composition_dir, film_seconds, hf_run, json_from, new_check_dir, storyboard_scenes,  # noqa: E402
                     which)

SELECTORS = [".pill", ".tag", ".card", ".chip", ".badge", ".btn", ".button", ".cta-pill", "button",
             "[class*='pill']", "[class*='-tag']", "[class*='card']", "[class*='btn']", "[data-audit]"]
SKIP = ("node_modules", ".hyperframes", "renders", ".git")
MARK = "MSAUDIT "
MAX_CROPS = 36

# Runs inside the page. Reports through console.warn, which `hyperframes check` returns as findings.
PROBE = r"""
<script>
(function () {
  var CFG = __CFG__, seen = {};
  function say(o) { try { console.warn("MSAUDIT " + JSON.stringify(o)); } catch (e) {} }
  function r1(n) { return Math.round(n * 10) / 10; }
  function opacity(el) { var o = 1; for (var e = el; e && e.nodeType === 1; e = e.parentElement) { var cs = getComputedStyle(e); if (cs.visibility === "hidden" || cs.display === "none") return 0; o *= parseFloat(cs.opacity); } return o; }
  function path(el) { var p = []; for (var e = el, i = 0; e && e.nodeType === 1 && i < 4; e = e.parentElement, i++) { if (e.id) { p.unshift("#" + e.id); break; } var c = (typeof e.className === "string" && e.className.trim()) ? "." + e.className.trim().split(/\s+/).slice(0, 2).join(".") : ""; p.unshift(e.tagName.toLowerCase() + c); } return p.join(" > ").slice(0, 110); }
  function textRange(el) { var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), n, first = null, last = null; while ((n = w.nextNode())) { if (n.nodeValue.trim()) { if (!first) first = n; last = n; } } if (!first) return null; var r = document.createRange(); r.setStart(first, 0); r.setEnd(last, last.nodeValue.length); return r; }
  var mc = document.createElement("canvas").getContext("2d");
  function component(el, t, W, H) {
    var b = el.getBoundingClientRect(); if (b.width < 4 || b.height < 4) return;
    var op = opacity(el); if (op < 0.05) return;
    if (b.right < 0 || b.bottom < 0 || b.left > W || b.top > H) return;
    var cs = getComputedStyle(el), txt = (el.textContent || "").replace(/\s+/g, " ").trim();
    var o = { k: "c", t: t, sel: path(el), cls: (typeof el.className === "string" ? el.className : "").trim().slice(0, 40), txt: txt.slice(0, 40), x: r1(b.left), y: r1(b.top), w: r1(b.width), h: r1(b.height), op: r1(op), sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight, br: parseFloat(cs.borderTopLeftRadius) || 0, bw: parseFloat(cs.borderTopWidth) || 0, fs: parseFloat(cs.fontSize) || 0, kids: el.children.length, words: txt ? txt.split(" ").length : 0, box: (cs.backgroundColor !== "rgba(0, 0, 0, 0)" || parseFloat(cs.borderTopWidth) > 0) ? 1 : 0 };
    var rg = textRange(el);
    if (rg && txt.length <= 60) {
      var rects = rg.getClientRects(), tops = [], tr = rg.getBoundingClientRect();
      for (var i = 0; i < rects.length; i++) { if (rects[i].width < 1) continue; var top = Math.round(rects[i].top), hit = false; for (var j = 0; j < tops.length; j++) if (Math.abs(tops[j] - top) < rects[i].height * 0.6) hit = true; if (!hit) tops.push(top); }
      o.lines = tops.length; o.tx = r1(tr.left); o.ty = r1(tr.top); o.tw = r1(tr.width); o.th = r1(tr.height);
      if (tops.length === 1) {
        try { // where the letter shapes sit, not the line box: baseline minus half the tallest letter
          var fcs = getComputedStyle(rg.startContainer.parentElement);
          mc.font = fcs.fontStyle + " " + fcs.fontWeight + " " + fcs.fontSize + " " + fcs.fontFamily;
          var m = mc.measureText(rg.toString().trim());
          var k = tr.height / (m.fontBoundingBoxAscent + m.fontBoundingBoxDescent);
          if (isFinite(k) && k > 0.2 && k < 5) { var base = tr.top + m.fontBoundingBoxAscent * k; o.ink = r1(base - m.actualBoundingBoxAscent * k / 2); }
        } catch (e) {}
      }
    }
    say(o);
  }
  function over3d(t, W, H) {
    var cvs = document.querySelectorAll("canvas");
    for (var c = 0; c < cvs.length; c++) {
      var cv = cvs[c], cb = cv.getBoundingClientRect(); if (cb.width < 100 || cb.height < 100 || opacity(cv) < 0.5) continue;
      var S = 4, small = document.createElement("canvas"); small.width = Math.max(1, Math.round(cb.width / S)); small.height = Math.max(1, Math.round(cb.height / S));
      var g = small.getContext("2d", { willReadFrequently: true }), px;
      try { g.drawImage(cv, 0, 0, small.width, small.height); px = g.getImageData(0, 0, small.width, small.height).data; } catch (e) { say({ k: "o", t: t, unreadable: 1 }); continue; }
      var counts = {}, best = null, bn = 0; // background = most common colour on the canvas border
      function at(x, y) { var i = (y * small.width + x) * 4; return [px[i], px[i + 1], px[i + 2], px[i + 3]]; }
      function tally(x, y) { var p = at(x, y), key = (p[0] >> 3) + "," + (p[1] >> 3) + "," + (p[2] >> 3) + "," + (p[3] >> 6); counts[key] = (counts[key] || 0) + 1; if (counts[key] > bn) { bn = counts[key]; best = p; } }
      for (var x = 0; x < small.width; x += 2) { tally(x, 0); tally(x, small.height - 1); }
      for (var y = 0; y < small.height; y += 2) { tally(0, y); tally(small.width - 1, y); }
      if (!best) continue;
      var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), n, done = [];
      while ((n = w.nextNode())) {
        var el = n.parentElement; if (!n.nodeValue.trim() || !el || done.indexOf(el) >= 0 || cv.contains(el)) continue; done.push(el);
        var tag = el.tagName; if (tag === "SCRIPT" || tag === "STYLE") continue;
        var fs = parseFloat(getComputedStyle(el).fontSize) || 0; if (fs < 18 || opacity(el) < 0.5) continue;
        var rg = document.createRange(); rg.selectNodeContents(el); var b = rg.getBoundingClientRect();
        var x0 = Math.max(b.left, cb.left), y0 = Math.max(b.top, cb.top), x1 = Math.min(b.right, cb.right), y1 = Math.min(b.bottom, cb.bottom);
        if (x1 - x0 < 8 || y1 - y0 < 8) continue;
        var busy = 0, tot = 0;
        for (var yy = Math.floor((y0 - cb.top) / S); yy < Math.ceil((y1 - cb.top) / S); yy++) for (var xx = Math.floor((x0 - cb.left) / S); xx < Math.ceil((x1 - cb.left) / S); xx++) {
          if (xx < 0 || yy < 0 || xx >= small.width || yy >= small.height) continue; var p = at(xx, yy); tot++;
          if (Math.abs(p[0] - best[0]) + Math.abs(p[1] - best[1]) + Math.abs(p[2] - best[2]) + Math.abs(p[3] - best[3]) > 60) busy++;
        }
        if (tot && busy / tot >= 0.15) say({ k: "o", t: t, sel: path(el), txt: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 40), x: r1(b.left), y: r1(b.top), w: r1(b.width), h: r1(b.height), cover: r1(busy / tot * 100) });
      }
    }
  }
  function report(tl) {
    var now = tl.time(), t = null;
    for (var i = 0; i < CFG.times.length; i++) if (Math.abs(CFG.times[i] - now) < 0.02) t = CFG.times[i];
    if (t === null || seen[t]) return; seen[t] = 1;
    var root = document.querySelector("[data-composition-id]"), W = +(root && root.getAttribute("data-width")) || innerWidth, H = +(root && root.getAttribute("data-height")) || innerHeight;
    var els = [], all = document.querySelectorAll(CFG.selectors);
    for (var j = 0; j < all.length; j++) { var inner = false; for (var q = 0; q < els.length; q++) if (els[q].contains(all[j]) && els[q] !== all[j] && (all[j].textContent || "").trim() === (els[q].textContent || "").trim()) inner = true; if (!inner) els.push(all[j]); }
    for (var e = 0; e < els.length; e++) { try { component(els[e], t, W, H); } catch (err) {} }
    try { over3d(t, W, H); } catch (err2) {}
    say({ k: "t", t: t, W: W, H: H, n: els.length });
  }
  function hook() {
    var tls = window.__timelines || {}, root = document.querySelector("[data-composition-id]"), id = root && root.getAttribute("data-composition-id");
    var tl = tls[id] || tls[Object.keys(tls)[0]]; if (!tl || !tl.eventCallback) return false;
    var prev = tl.eventCallback("onUpdate");
    tl.eventCallback("onUpdate", function () { if (prev) { try { prev.apply(this, arguments); } catch (e) {} } report(tl); });
    say({ k: "hook" }); return true;
  }
  if (!hook()) { var tries = 0, iv = setInterval(function () { if (hook() || ++tries > 100) clearInterval(iv); }, 50); }
})();
</script>
"""


def link_dir(src, dst):
    """Make dst point at src without copying: symlink, Windows junction, and only then a real copy."""
    try:
        os.symlink(src, dst, target_is_directory=True)
        return "symlink"
    except (OSError, NotImplementedError, AttributeError):
        pass
    if os.name == "nt":
        try:
            import _winapi
            _winapi.CreateJunction(src, dst)
            return "junction"
        except Exception:  # noqa: BLE001
            pass
    shutil.copytree(src, dst)
    return "copy"


def unlink_dir(dst, how):
    try:
        if how == "symlink":
            os.unlink(dst)
        elif how == "junction":
            os.rmdir(dst)   # removes the junction only, never what it points at
    except OSError:
        pass


def light_copy(src, dst):
    """Copy a file; big media (footage, audio) is linked instead, so an audit doesn't copy gigabytes."""
    try:
        if os.path.getsize(src) > 5 * 1024 * 1024:
            for link in (os.link, os.symlink):
                try:
                    link(src, dst)
                    return dst
                except (OSError, NotImplementedError, AttributeError):
                    continue
    except OSError:
        pass
    return shutil.copy2(src, dst)


def probe_copy(comp, times, selectors):
    """A temporary copy of the composition with the measuring script added. Returns (dir, cleanup)."""
    tmp = tempfile.mkdtemp(prefix="ms-audit-")
    dst = os.path.join(tmp, "composition")
    shutil.copytree(comp, dst, ignore=shutil.ignore_patterns(*SKIP), copy_function=light_copy)
    how = None
    if os.path.isdir(os.path.join(comp, "node_modules")):
        how = link_dir(os.path.join(comp, "node_modules"), os.path.join(dst, "node_modules"))
    index = os.path.join(dst, "index.html")
    with open(index, encoding="utf-8") as f:
        html = f.read()
    cfg = json.dumps({"times": times, "selectors": ",".join(selectors)})
    probe = PROBE.replace("__CFG__", cfg)
    cut = html.lower().rfind("</body>")
    html = html[:cut] + probe + html[cut:] if cut >= 0 else html + probe
    os.remove(index)   # write a new file: the copy must never share storage with the original index.html
    with open(index, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    def cleanup():
        if how:
            unlink_dir(os.path.join(dst, "node_modules"), how)
        shutil.rmtree(tmp, ignore_errors=True)
    return dst, cleanup


def judge(records, canvas):
    """Turn measurements into findings. Each: severity (warning | review), code, time, what, why."""
    out = []
    W, H = canvas
    by_class = {}
    for c in records:
        if c.get("k") != "c" or c.get("op", 0) < 0.95:
            continue   # mid-fade: judge it where it is fully visible
        label = f'"{c["txt"]}"' if c.get("txt") else c.get("cls") or c["sel"]

        def add(sev, code, why, c=c, label=label):
            out.append({"severity": sev, "code": code, "time": c["t"], "what": label, "selector": c["sel"],
                        "why": why, "rect": [c["x"], c["y"], c["w"], c["h"]]})
        short = 0 < c.get("words", 0) <= 4
        if short and c.get("lines", 1) > 1 and c.get("kids", 0) <= 2:
            add("warning", "label_wrapped", f"a {c['words']}-word label wraps onto {c['lines']} lines: add "
                "white-space: nowrap, or give it more room")
        if c.get("sw", 0) > c.get("cw", 0) + 1 and c.get("cw", 0) > 0:
            add("warning", "text_overflow", f"content is {c['sw'] - c['cw']} px wider than its box")
        if c["x"] < -2 or c["y"] < -2 or c["x"] + c["w"] > W + 2 or c["y"] + c["h"] > H + 2:
            add("warning", "cut_by_frame", "the box is partly outside the frame")
        if c.get("box") and c.get("lines") == 1 and c.get("kids", 0) == 0 and "tx" in c:
            if "ink" in c:
                off = c["ink"] - (c["y"] + c["h"] / 2)
                share = abs(off) / c["h"]
                if abs(off) > 2 and share > 0.06:
                    add("warning" if share > 0.10 else "review", "text_off_centre_vertical",
                        f"the letters sit {abs(off):.0f} px too {'low' if off > 0 else 'high'} "
                        f"({share * 100:.0f}% of the box height): centre with flex + align-items, "
                        f"or fix line-height/padding")
            left, right = c["tx"] - c["x"], (c["x"] + c["w"]) - (c["tx"] + c["tw"])
            if abs(left - right) > max(3, 0.08 * c["w"]):
                add("review", "text_off_centre_horizontal",
                    f"padding is {left:.0f} px on the left and {right:.0f} px on the right")
            if min(left, right) < 0.25 * c.get("fs", 0):
                add("review", "tight_padding", f"only {min(left, right):.0f} px between the text and the edge "
                    f"(font size {c.get('fs', 0):.0f} px)")
        if c.get("cls"):
            by_class.setdefault(c["cls"], []).append(c)
    for cls, items in by_class.items():
        heights = sorted({round(i["h"]) for i in items})
        radii = sorted({round(i["br"]) for i in items})
        if len(items) > 1 and (heights[-1] - heights[0] > 2 or len(radii) > 1):
            out.append({"severity": "review", "code": "inconsistent_class", "time": items[0]["t"], "what": "." + cls,
                        "selector": items[0]["sel"], "rect": [items[0]["x"], items[0]["y"], items[0]["w"], items[0]["h"]],
                        "why": f"the same class is drawn with heights {heights} px and corner radii {radii} px: "
                               f"use one token for each"})
    for o in records:
        if o.get("k") == "o" and "cover" in o:
            sev = "warning" if o["cover"] >= 30 else "review"
            out.append({"severity": sev, "code": "text_over_3d", "time": o["t"], "what": f'"{o["txt"]}"',
                        "selector": o["sel"], "rect": [o["x"], o["y"], o["w"], o["h"]],
                        "why": f"{o['cover']:.0f}% of the area behind this text is 3D content, not background: "
                               f"move the object or the text, or put a plate behind the text"})
    return out


def font_file():
    for p in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
              "/usr/share/fonts/TTF/DejaVuSans.ttf"):
        if os.path.isfile(p):
            return p
    return None


def crop_sheets(comps, frames, canvas, out):
    """Enlarged crops of each component from the real stills, numbered, tiled 4 per row. Returns sheet paths."""
    ffmpeg = which("ffmpeg")
    if not ffmpeg or not comps:
        return []
    W, H = canvas
    tw, th = 480, 220
    font = font_file()
    tiles = []
    crop_dir = os.path.join(out, "crops")
    os.makedirs(crop_dir, exist_ok=True)
    for n, c in enumerate(comps, 1):
        still = frames.get(c["t"])
        if not still:
            continue
        pad = max(12, 0.35 * c["h"])
        x0, y0 = max(0, c["x"] - pad), max(0, c["y"] - pad)
        x1, y1 = min(W, c["x"] + c["w"] + pad), min(H, c["y"] + c["h"] + pad)
        cw, ch = int(x1 - x0) // 2 * 2, int(y1 - y0) // 2 * 2
        if cw < 8 or ch < 8:
            continue
        base = (f"crop={cw}:{ch}:{int(x0)}:{int(y0)},scale={tw}:{th - 28}:force_original_aspect_ratio=decrease:"
                f"flags=lanczos,pad={tw}:{th}:(ow-iw)/2:28+({th - 28}-ih)/2:color=0x202020")
        tile = os.path.join(crop_dir, f"{n:02d}.png")
        ok = False
        if font:
            label = f"{n}   {c['t']:g}s"
            ff = font.replace("\\", "/").replace(":", "\\:")
            vf = base + f",drawtext=fontfile='{ff}':text='{label}':x=8:y=6:fontsize=16:fontcolor=white"
            ok = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", still, "-vf", vf, "-frames:v", "1", tile],
                                capture_output=True).returncode == 0
        if not ok:
            ok = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", still, "-vf", base, "-frames:v", "1", tile],
                                capture_output=True).returncode == 0
        if ok:
            tiles.append(tile)
            c["crop"] = n
    sheets = []
    for i in range(0, len(tiles), 12):
        group = tiles[i:i + 12]
        rows = (len(group) + 3) // 4
        sheet = os.path.join(out, f"components-{i // 12 + 1}.jpg")
        cmd = [ffmpeg, "-v", "error", "-y"]
        for t in group:
            cmd += ["-i", t]
        if len(group) == 1:
            cmd += ["-frames:v", "1", "-q:v", "3", sheet]
        else:
            layout = "|".join(f"{(j % 4) * tw}_{(j // 4) * th}" for j in range(len(group)))
            cmd += ["-filter_complex", f"xstack=inputs={len(group)}:layout={layout}:fill=0x202020", "-frames:v", "1",
                    "-q:v", "3", sheet]
        if subprocess.run(cmd, capture_output=True).returncode == 0 and rows:
            sheets.append(sheet)
    return sheets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--composition")
    ap.add_argument("--at", help="comma-separated times (default: every scene midpoint from storyboard.json)")
    ap.add_argument("--selectors", help="extra CSS selectors to treat as components, comma-separated")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    comp = composition_dir(a.composition)
    project = os.path.dirname(comp) if os.path.basename(comp).startswith("composition") else comp
    total = film_seconds(comp) or 0
    notes = []
    if a.at:
        times = [float(x) for x in a.at.split(",") if x.strip()]
    else:
        scenes = [s for s in storyboard_scenes(project) if not total or s[1] < total]
        if scenes:
            times = [round(s[1] + s[2] / 2, 3) for s in scenes]
        else:
            n = 9
            times = [round(total * (i + 0.5) / n, 3) for i in range(n)] if total else [0.5]
            notes.append("storyboard.json has no scenes, so 9 evenly spaced times were sampled. Fill in each "
                         "scene's id, start and duration to audit every scene at its midpoint.")
        if total and all(abs(t - (total - 0.5)) > 0.4 for t in times):
            times.append(round(total - 0.5, 3))   # the closing frame: CTA and logo
    # `hyperframes check` samples on whole frames (rounding down). Tenths of a second are whole frames
    # at 24, 30 and 60 fps, so the measurements and the stills are taken at the same instants.
    times = sorted({round(t, 1) for t in times if t >= 0 and (not total or t <= total)})
    if not times:
        sys.exit("No times to audit.")
    selectors = SELECTORS + [s.strip() for s in (a.selectors or "").split(",") if s.strip()]

    out = new_check_dir(project, "audit")
    at = ",".join(f"{t:g}" for t in times)

    # 1 + 2: HyperFrames check, with the measuring script, in a temporary copy
    work, cleanup = probe_copy(comp, times, selectors)
    try:
        code, stdout, stderr = hf_run(work, ["check", "--json", "--no-cache", "--at", at], timeout=900)
    finally:
        cleanup()
    rep = json_from(stdout)
    if not rep:
        tail = [ln for ln in (stderr + "\n" + stdout).splitlines() if ln.strip()][-12:]
        sys.exit("AUDIT_FAILED hyperframes check gave no report\n  | " + "\n  | ".join(t[:300] for t in tail))
    records, hf = [], []
    for section in ("lint", "runtime", "layout", "motion", "contrast", "craft", "audio"):
        for f in (rep.get(section) or {}).get("findings", []):
            msg = f.get("message", "")
            if msg.startswith(MARK):
                try:
                    records.append(json.loads(msg[len(MARK):]))
                except ValueError:
                    pass
                continue
            if "GL Driver Message" in msg or "GPU stall due to ReadPixels" in msg:
                continue   # graphics-driver notes describe the machine, not the composition
            hf.append({"severity": f.get("severity", "info"), "code": f.get("code", section), "section": section,
                       "time": f.get("time"), "what": f.get("text") or f.get("selector") or "", "selector": f.get("selector"),
                       "why": msg, "fix": f.get("fixHint"), "rect": [f["bbox"][k] for k in ("x", "y", "width", "height")]
                       if isinstance(f.get("bbox"), dict) and f["bbox"].get("width") else None})
    hooked = any(r.get("k") == "hook" for r in records)
    sampled = sorted({r["t"] for r in records if r.get("k") == "t"})
    tinfo = next((r for r in records if r.get("k") == "t"), {})
    canvas = (tinfo.get("W") or 1920, tinfo.get("H") or 1080)
    if not hooked:
        notes.append("The measuring script found no GSAP timeline in window.__timelines, so components and "
                     "text-over-3D were NOT measured. HyperFrames' own findings and the sheets are still valid.")
    elif len(sampled) < len(times):
        notes.append(f"Components were measured at {len(sampled)} of {len(times)} times.")
    if any(r.get("k") == "o" and r.get("unreadable") for r in records):
        notes.append("A canvas couldn't be read, so text-over-3D wasn't measured there: check those scenes by eye.")
    mine = judge(records, canvas) if hooked else []

    # 3: stills + HyperFrames' contact sheets from the real composition
    frames_dir = os.path.join(out, "frames")
    code2, so2, se2 = hf_run(comp, ["snapshot", "--no-end", "--json", "--timeout", "120000", "--at", at, "-o", frames_dir],
                             timeout=900)
    snap = json_from(so2) or {}
    frames = {round(f["time"], 3): f["path"] for f in snap.get("frames", [])}
    scene_sheets = snap.get("contactSheets") or []
    if not frames:
        notes.append("Stills could not be captured (hyperframes snapshot failed), so there are no sheets.")

    # one crop per distinct component, at the first time it is fully visible
    uniq, seen = [], set()
    for c in records:
        if c.get("k") != "c" or c.get("op", 0) < 0.95:
            continue
        key = (c.get("cls"), c.get("txt"), round(c["w"] / 8), round(c["h"] / 8))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    for o in records:   # text over 3D gets a crop too
        if o.get("k") == "o" and "cover" in o:
            uniq.append({"k": "o", "t": o["t"], "sel": o["sel"], "txt": o["txt"], "cls": "text over 3D", "x": o["x"],
                         "y": o["y"], "w": o["w"], "h": o["h"]})
    comp_sheets = crop_sheets(uniq[:MAX_CROPS], frames, canvas, out)
    crop_of = {(c["t"], c["sel"], c.get("txt")): c.get("crop") for c in uniq}
    for f in mine:
        f["crop"] = crop_of.get((f["time"], f["selector"], f["what"].strip('"')))

    errors = [f for f in hf if f["severity"] == "error"]
    warnings = [f for f in hf if f["severity"] == "warning"] + [f for f in mine if f["severity"] == "warning"]
    review = [f for f in mine if f["severity"] == "review"]
    result = {"status": "AUDIT_DONE", "folder": out, "times": times, "canvas": list(canvas),
              "components_measured": sum(1 for c in uniq if c.get("k") == "c"), "errors": len(errors), "warnings": len(warnings),
              "to_review": len(review), "hyperframes_findings": hf, "component_findings": mine,
              "components": [{"n": c.get("crop"), "time": c["t"], "class": c.get("cls"), "text": c.get("txt"),
                              "selector": c["sel"], "size": [c["w"], c["h"]], "radius": c.get("br"),
                              "border": c.get("bw"), "font_size": c.get("fs")} for c in uniq],
              "scene_sheets": scene_sheets, "component_sheets": comp_sheets, "notes": notes}
    with open(os.path.join(out, "audit.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    def line(f):
        crop = f" [crop {f['crop']}]" if f.get("crop") else ""
        t = f"{f['time']:g}s" if isinstance(f.get("time"), (int, float)) else "-"
        return f"- {f['severity'].upper()} `{f['code']}` at {t}: {f['what']}{crop}. {f['why']}"
    md = [f"# Visual audit ({len(times)} times: {at})", "",
          f"{len(errors)} errors, {len(warnings)} warnings, {len(review)} to review by eye. "
          f"{result['components_measured']} components measured.", ""]
    if notes:
        md += ["## Notes"] + [f"- {n}" for n in notes] + [""]
    md += ["## HyperFrames check (lint, runtime, layout, contrast, craft)"]
    shown = [f for f in hf if f["severity"] in ("error", "warning")]
    md += [line(f) for f in shown] or ["- nothing above info level"]
    md += ["", "## Components (pills, tags, cards, buttons)"]
    md += [line(f) for f in mine] or ["- nothing flagged" if hooked else "- not measured"]
    md += ["", "## Look at these", "Scenes, one still per time:"] + [f"- {s}" for s in scene_sheets]
    md += ["Components enlarged, numbered as in the list below:"] + [f"- {s}" for s in comp_sheets]
    md += ["", "| Crop | Time | Component | Size | Radius | Border | Font |", "|---|---|---|---|---|---|---|"]
    md += [f"| {c.get('crop', '-')} | {c['t']:g}s | {c.get('txt') or c.get('cls') or c['sel']} | "
           f"{c['w']:.0f}×{c['h']:.0f} | {c.get('br', 0):.0f} | {c.get('bw', 0):g} | {c.get('fs', 0):.0f} |" for c in uniq[:MAX_CROPS]]
    md += ["", "The numbers find candidates. Open the sheets and judge borders, radii, spacing and "
           "alignment by eye before calling the video done."]
    with open(os.path.join(out, "audit.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")

    if a.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"AUDIT_DONE {len(errors)} errors, {len(warnings)} warnings, {len(review)} to review | "
              f"{result['components_measured']} components at {len(times)} times | {out}")
        for n in notes:
            print("NOTE: " + n)
        for f in errors + warnings + review:
            print(line(f)[2:])
        for s in scene_sheets + comp_sheets:
            print("  look at: " + s)
        print("NEXT: open the sheets and audit.md. Fix what is flagged and what looks wrong, then run it again.")
    sys.exit(1 if errors or (a.strict and (warnings or review)) else 0)


if __name__ == "__main__":
    main()
