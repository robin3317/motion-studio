/* iso-kit.js: motion-studio isometric + kinetic-type toolkit (MIT).
 * Plain script (no modules). Load after GSAP:  <script src="lib/iso-kit.js"></script>
 * Everything here is deterministic: geometry is built once at load, and every animation is a
 * tween on the paused master timeline, so any frame = f(t) (HyperFrames seek-safe).
 *
 * Projection: 2:1 dimetric ("pixel isometric").  world (x right-down, y left-down, z up) in units.
 *   screen = origin + ((x - y)·u,  (x + y)·u/2 − z·u·Z)
 * Visible faces of a box: TOP (lightest), LEFT/front-left (mid), RIGHT/front-right (darkest).
 */
(function (global) {
  "use strict";
  const Z = 1.12; // vertical scale so cubes read as cubes in 2:1 projection

  // ---------- colour helpers ----------
  function hexToRgb(h) {
    h = h.replace("#", "");
    if (h.length === 3) h = h.split("").map((c) => c + c).join("");
    const n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
  }
  function mix(a, b, t) {
    const A = hexToRgb(a), B = hexToRgb(b);
    return rgbToHex(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t, A[2] + (B[2] - A[2]) * t);
  }
  /** Three flat face tones from one base colour: top lighter, left = base, right darker. */
  function shade(base, amt) {
    amt = amt == null ? 0.18 : amt;
    return { top: mix(base, "#ffffff", amt), left: base, right: mix(base, "#000000", amt) };
  }

  // ---------- projection ----------
  function P(o, x, y, z) {
    const u = o.u;
    return [o.ox + (x - y) * u, o.oy + ((x + y) * u) / 2 - z * u * Z];
  }
  const pts = (arr) => arr.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ");
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  /**
   * box(o): an isometric box as an SVG <g>.
   * o = { ox, oy, u,          screen origin of world (0,0,0) and pixels per unit
   *       x=0,y=0,z=0, w=1,d=1,h=1,
   *       color: "#hex" (auto-shaded) | faces: {top,left,right},
   *       stroke="#14161a", sw=3, dash=false (placeholder outline), opacity=1,
   *       id, cls, labels: { top|left|right: {text, size, color, weight, font} }, slots: n (server lines on left face) }
   */
  function box(o) {
    const x = o.x || 0, y = o.y || 0, z = o.z || 0, w = o.w || 1, d = o.d || 1, h = o.h == null ? 1 : o.h;
    const f = o.faces || shade(o.color || "#f4f4f1", o.shade);
    const stroke = o.stroke || "#14161a", sw = o.sw == null ? 3 : o.sw;
    const top = [P(o, x, y, z + h), P(o, x + w, y, z + h), P(o, x + w, y + d, z + h), P(o, x, y + d, z + h)];
    const left = [P(o, x, y + d, z), P(o, x + w, y + d, z), P(o, x + w, y + d, z + h), P(o, x, y + d, z + h)];
    const right = [P(o, x + w, y, z), P(o, x + w, y + d, z), P(o, x + w, y + d, z + h), P(o, x + w, y, z + h)];
    const common = `stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"` + (o.dash ? ` stroke-dasharray="10 8"` : "");
    const fill = (c) => (o.dash ? "none" : c);
    let s = `<g${o.id ? ` id="${o.id}"` : ""} class="iso ${o.cls || ""}"${o.opacity != null ? ` opacity="${o.opacity}"` : ""}>`;
    s += `<polygon points="${pts(left)}" fill="${fill(f.left)}" ${common}/>`;
    s += `<polygon points="${pts(right)}" fill="${fill(f.right)}" ${common}/>`;
    s += `<polygon points="${pts(top)}" fill="${fill(f.top)}" ${common}/>`;
    if (o.slots && !o.dash) {
      for (let i = 0; i < o.slots; i++) {
        const zz = z + h * (0.25 + (0.55 * i) / Math.max(1, o.slots - 1 || 1));
        const a = P(o, x + w * 0.18, y + d, zz), b = P(o, x + w * 0.62, y + d, zz);
        s += `<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="${stroke}" stroke-width="${Math.max(2, sw)}" stroke-linecap="round"/>`;
        const led = P(o, x + w * 0.82, y + d, zz);
        s += `<circle cx="${led[0]}" cy="${led[1]}" r="${o.u * 0.05}" fill="${o.led || "#00d084"}"/>`;
      }
    }
    if (o.labels) for (const face of ["top", "left", "right"]) if (o.labels[face]) s += faceText(o, face, o.labels[face]);
    return s + "</g>";
  }

  /** Text lying on a face of the box described by o. face: "top" | "left" | "right". */
  function faceText(o, face, L) {
    const x = o.x || 0, y = o.y || 0, z = o.z || 0, w = o.w || 1, d = o.d || 1, h = o.h == null ? 1 : o.h;
    let c, m;
    if (face === "top") { c = P(o, x + w / 2, y + d / 2, z + h); m = [1, 0.5, -1, 0.5]; }
    else if (face === "left") { c = P(o, x + w / 2, y + d, z + h / 2); m = [1, 0.5, 0, 1]; }
    else { c = P(o, x + w, y + d / 2, z + h / 2); m = [1, -0.5, 0, 1]; }
    const size = L.size || o.u * 0.22;
    return `<text transform="matrix(${m.join(" ")} ${c[0].toFixed(1)} ${c[1].toFixed(1)})" text-anchor="middle" dominant-baseline="central"
      font-family="${L.font || "var(--font-mono)"}" font-size="${size}" font-weight="${L.weight || 700}" fill="${L.color || "#14161a"}"
      letter-spacing="${L.spacing || 0}">${esc(L.text)}</text>`;
  }

  /** Thin platform/plate under objects (a flat box). */
  function plate(o) { return box(Object.assign({ h: 0.12, color: "#e7e6e1" }, o)); }

  /** Flat diamond (top face only), e.g. a floor tile or a "chapter" tile. */
  function tile(o) { return box(Object.assign({ h: 0.06 }, o)); }

  /** Ellipse ring around a point (orbit). */
  function ring(o) {
    return `<ellipse cx="${o.cx}" cy="${o.cy}" rx="${o.rx}" ry="${o.rx / 2}" fill="none" stroke="${o.color || "#7c4dff"}" stroke-width="${o.sw || 3}"${o.id ? ` id="${o.id}"` : ""}/>`;
  }

  /** Wrap SVG content in a full-size <svg> layer. */
  function svg(w, h, content, attrs) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" ${attrs || ""} style="position:absolute;inset:0;overflow:visible">${content}</svg>`;
  }

  // ---------- kinetic type helpers ----------
  /** Split an element's lines (child .line) for mask reveals: wraps each .line's content in a span. */
  function prepLines(root) {
    root.querySelectorAll(".line").forEach((ln) => {
      if (ln.firstElementChild && ln.firstElementChild.classList.contains("li")) return;
      ln.innerHTML = `<span class="li">${ln.innerHTML}</span>`;
    });
  }
  /** Line-mask rise reveal. times: number (stagger from t) or array of absolute times (one per line, e.g. synced to VO words). */
  function revealLines(tl, root, times, opts) {
    opts = opts || {};
    prepLines(root);
    const lines = root.querySelectorAll(".line .li");
    lines.forEach((el, i) => {
      const t = Array.isArray(times) ? times[Math.min(i, times.length - 1)] : times + i * (opts.stagger || 0.1);
      tl.fromTo(el, { yPercent: 110 }, { yPercent: 0, duration: opts.dur || 0.55, ease: opts.ease || "expo.out", immediateRender: !!opts.immediate }, t);
    });
  }
  /** Shrink font-size until the element fits its own box (run once at load; deterministic). */
  function fit(el, minPx) {
    const cs = getComputedStyle(el);
    let size = parseFloat(cs.fontSize), guard = 0;
    while ((el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) && size > (minPx || 24) && guard++ < 200) {
      size -= 2; el.style.fontSize = size + "px";
    }
    return size;
  }
  /** Count-up text. fmt(v) -> string. */
  function counter(tl, el, from, to, t, dur, fmt) {
    const o = { v: from };
    fmt = fmt || ((v) => Math.round(v).toLocaleString("en-US"));
    el.textContent = fmt(from);
    tl.fromTo(o, { v: from }, { v: to, duration: dur || 1.2, ease: "power3.out", onUpdate: () => { el.textContent = fmt(o.v); } }, t);
  }
  /** Typewriter into el, chars per second cps. */
  function type(tl, el, text, t, cps) {
    const o = { n: 0 };
    el.textContent = "";
    tl.fromTo(o, { n: 0 }, { n: text.length, duration: text.length / (cps || 28), ease: "none", onUpdate: () => { el.textContent = text.slice(0, Math.floor(o.n)); } }, t);
  }
  /**
   * Flip-clock digits: el gets one .flip card per character of `to`; each card flips from the
   * matching char of `from` to `to`, staggered. Cards are built once (seek-safe).
   */
  function flip(tl, el, from, to, t, opts) {
    opts = opts || {};
    from = String(from).padStart(String(to).length, " ");
    el.innerHTML = "";
    const cards = [];
    for (let i = 0; i < String(to).length; i++) {
      const c = document.createElement("span");
      c.className = "flip";
      c.innerHTML = `<b>${esc(from[i])}</b>`;
      el.appendChild(c); cards.push(c);
    }
    cards.forEach((c, i) => {
      const b = c.firstChild, tt = t + i * (opts.stagger || 0.12);
      if (from[i] === String(to)[i]) return;
      tl.to(b, { rotationX: -90, duration: 0.16, ease: "power2.in" }, tt);
      tl.set(b, { textContent: String(to)[i], rotationX: 90 }, tt + 0.16);
      tl.to(b, { rotationX: 0, duration: 0.22, ease: "back.out(2)" }, tt + 0.16);
    });
  }
  /** Drop-in for SVG groups / elements: from above with a little overshoot. */
  function drop(tl, targets, t, opts) {
    opts = opts || {};
    tl.from(targets, { y: opts.y == null ? -120 : opts.y, opacity: 0, duration: opts.dur || 0.6, ease: opts.ease || "back.out(1.6)", stagger: opts.stagger || 0.12 }, t);
  }

  // ---------- frame furniture ----------
  /**
   * HUD: corner labels + scene counter + timecode, driven by the master clock (seek-safe).
   * install(tl, rootEl, { left: "BRAND · CAMPAIGN", scenes: [{start, name}], fps: 30, duration })
   */
  function hud(tl, root, opts) {
    const el = document.createElement("div");
    el.className = "hud";
    el.innerHTML = `<div class="hud-l"><i></i>${esc(opts.left || "")}</div><div class="hud-r"><span class="hud-scene"></span><span class="hud-tc"></span></div>`;
    root.appendChild(el);
    const sceneEl = el.querySelector(".hud-scene"), tcEl = el.querySelector(".hud-tc");
    const fps = opts.fps || 30, scenes = opts.scenes || [];
    const clock = { t: 0 };
    const paint = () => {
      const t = clock.t;
      let idx = 0;
      scenes.forEach((s, i) => { if (t >= s.start - 1e-6) idx = i; });
      const s = scenes[idx];
      if (s) sceneEl.textContent = `SCENE ${String(idx + 1).padStart(2, "0")} / ${String(s.name).toUpperCase()}`;
      const f = Math.floor(t * fps + 1e-6), ss = Math.floor(f / fps), ff = f % fps;
      tcEl.textContent = `00:${String(Math.floor(ss / 60)).padStart(2, "0")}:${String(ss % 60).padStart(2, "0")}:${String(ff).padStart(2, "0")}`;
    };
    tl.fromTo(clock, { t: 0 }, { t: opts.duration, duration: opts.duration, ease: "none", onUpdate: paint }, 0);
    paint();
    return el;
  }

  /** Show/hide scenes at absolute times (hard cuts). scenes: [{sel, start, end}] */
  function cuts(tl, scenes) {
    scenes.forEach((s) => {
      tl.set(s.sel, { autoAlpha: 1 }, s.start);
      if (s.end != null) tl.set(s.sel, { autoAlpha: 0 }, s.end);
    });
  }

  global.IsoKit = { P, box, faceText, plate, tile, ring, svg, shade, mix, prepLines, revealLines, fit, counter, type, flip, drop, hud, cuts };
})(window);
