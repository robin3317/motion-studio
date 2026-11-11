// motion-studio 3D helpers (seek-safe: nothing here keeps state between frames).
// See references/three-d.md. Import with:  import { ... } from "./lib/ms3d.js";
import * as THREE from "three";

export const clamp01 = (x) => Math.min(1, Math.max(0, x));
export const lerp = (a, b, u) => a + (b - a) * u;
export const easeInOutCubic = (x) => { x = clamp01(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const easeOutExpo = (x) => { x = clamp01(x); return x === 1 ? 1 : 1 - Math.pow(2, -10 * x); };
export const easeOutCubic = (x) => { x = clamp01(x); return 1 - Math.pow(1 - x, 3); };

// Seeded RNG (mulberry32): the same seed gives the same numbers on every machine and every frame.
export function rng(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Quality profile. "cpu" is for hosts without a GPU (cloud sandboxes): fewer particles and
// lighter geometry, the same look. Set it with data-quality on <html> (new_project.py does this).
export function quality() {
  const cpu = document.documentElement.dataset.quality === "cpu";
  return cpu
    ? { name: "cpu", particles: 120, curveSegments: 10, bevelSegments: 2, sphereSegments: 16, glowPx: 256 }
    : { name: "standard", particles: 400, curveSegments: 24, bevelSegments: 4, sphereSegments: 32, glowPx: 512 };
}

// Screen fraction (0..1 from the top-left) -> world position on the z = 0 plane, for a camera
// on the z axis looking at the origin. Lets you place 3D objects by layout, next to the text zones.
export function screenToWorld(camera, fx, fy) {
  const halfH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z;
  return new THREE.Vector3((fx - 0.5) * 2 * halfH * camera.aspect, (0.5 - fy) * 2 * halfH, 0);
}
// World units for a size given as a fraction of the frame's shorter side.
export function worldSize(camera, frac) {
  const halfH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z;
  return frac * 2 * halfH * Math.min(1, camera.aspect);
}

// World position -> pixel position in the frame. Use it to pin an HTML label to a 3D object
// ("UI in 3D": the text stays HTML, so it is sharp and any language shapes correctly).
const _v = new THREE.Vector3();
export function toScreen(camera, world, W, H) {
  _v.copy(world).project(camera);
  return { x: (_v.x * 0.5 + 0.5) * W, y: (-_v.y * 0.5 + 0.5) * H, visible: _v.z > -1 && _v.z < 1 };
}
// Pin an absolutely positioned element (left: 0; top: 0) to a world position, plus a pixel offset.
export function pin(el, camera, world, W, H, dx = 0, dy = 0) {
  const p = toScreen(camera, world, W, H);
  el.style.transform = `translate(${(p.x + dx).toFixed(2)}px, ${(p.y + dy).toFixed(2)}px)`;
}

// Soft glow behind an object: one additive plane with a radial gradient. A cheap stand-in for
// bloom that costs almost nothing on a CPU and never blurs text.
export function glowPlane(color, px = 512) {
  const c = document.createElement("canvas"); c.width = c.height = px;
  const g = c.getContext("2d");
  const col = new THREE.Color(color);
  const rgb = `${Math.round(col.r * 255)}, ${Math.round(col.g * 255)}, ${Math.round(col.b * 255)}`;
  const grad = g.createRadialGradient(px / 2, px / 2, 0, px / 2, px / 2, px / 2);
  grad.addColorStop(0, `rgba(${rgb}, 0.55)`); grad.addColorStop(0.35, `rgba(${rgb}, 0.18)`); grad.addColorStop(1, `rgba(${rgb}, 0)`);
  g.fillStyle = grad; g.fillRect(0, 0, px, px);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
  return new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
}

// A text label drawn to a canvas texture, for the rare case where the label must live INSIDE the
// 3D scene (it turns with an object, or something passes in front of it). Otherwise use pin().
// Done right: the stroke is inset by half its width so it is never clipped, the text is centred
// on its real letter shapes, the texture is large enough to stay sharp, and it has mipmaps.
// Returns a mesh `heightWorld` tall. Call it after the font has loaded (document.fonts.ready).
export function labelTexture(text, o = {}) {
  const font = o.font || '700 96px system-ui, sans-serif';
  const padX = o.padX ?? 56, padY = o.padY ?? 34, lw = o.lineWidth ?? 6;
  const radius = o.radius ?? 999, heightWorld = o.heightWorld ?? 0.4;
  const m = document.createElement("canvas").getContext("2d");
  m.font = font;
  const tm = m.measureText(text);
  const capH = m.measureText("H").actualBoundingBoxAscent;         // centre on the capitals
  const w = Math.ceil(tm.width + padX * 2), h = Math.ceil(capH + padY * 2);
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d");
  const r = Math.min(radius, (h - lw) / 2);
  g.beginPath(); g.roundRect(lw / 2, lw / 2, w - lw, h - lw, r);  // inset by lineWidth / 2
  if (o.fill) { g.fillStyle = o.fill; g.fill(); }
  if (lw > 0 && o.stroke) { g.lineWidth = lw; g.strokeStyle = o.stroke; g.stroke(); }
  g.font = font; g.fillStyle = o.color || "#fff"; g.textAlign = "center"; g.textBaseline = "alphabetic";
  g.fillText(text, w / 2, h / 2 + capH / 2);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace; tex.generateMipmaps = true;
  tex.minFilter = THREE.LinearMipmapLinearFilter; tex.anisotropy = o.anisotropy ?? 8;
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false, depthWrite: false });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(heightWorld * (w / h), heightWorld), mat);
  mesh.userData.pixels = { w, h };
  return mesh;
}
