// motion-studio 3D stage for the 3D starter: everything drawn in WebGL lives here.
// index.html holds the text scenes and the timeline; its linear clock calls host.render(t).
// Seek-safe: the picture is a pure function of t (references/three-d.md).
// Edit POSES to move the object with your text zones; swap assets/logo.svg for the real logo.
import * as THREE from "three";
import { SVGLoader } from "three/addons/loaders/SVGLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { lerp, easeInOutCubic, easeOutExpo, rng, quality, screenToWorld, worldSize, pin, glowPlane } from "./ms3d.js";

const host = window.__ms3d;   // set up in index.html: { t, duration, cuts, render, ready }
const root = document.getElementById("root");
const W = Number(root.dataset.width), H = Number(root.dataset.height);
const Q = quality();
const css = getComputedStyle(document.documentElement);
const accent = new THREE.Color(css.getPropertyValue("--accent").trim() || "#3b82f6");
const ink = new THREE.Color(css.getPropertyValue("--ink").trim() || "#f5f7fa");

// preserveDrawingBuffer stays on: scripts/visual_audit.py reads the canvas to find text over 3D.
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("gl"), antialias: true, alpha: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
// Neutral tone mapping keeps brand colours true (references/three-d.md, "Look").
renderer.toneMapping = THREE.NeutralToneMapping;
renderer.toneMappingExposure = 0.95;

const scene = new THREE.Scene();
scene.background = new THREE.Color(css.getPropertyValue("--bg").trim() || "#07080c");
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

// The camera stays on the z axis, so layout poses map cleanly to the frame. The object turns, not the camera.
const wide = W > H * 1.2;
const camera = new THREE.PerspectiveCamera(wide ? 32 : 45, W / H, 0.1, 100);
const DIST = wide ? 6.2 : 7.8;

const key = new THREE.DirectionalLight(0xffffff, 1.1); key.position.set(3, 4, 5); scene.add(key);
const rim = new THREE.DirectionalLight(accent, 2.2); rim.position.set(-4, 1, -3); scene.add(rim);

// Layout poses per scene: [x, y, size, yaw]. x and y are frame fractions from the top-left,
// size is a fraction of the frame's shorter side, yaw is in degrees. Edit these with the text zones.
const POSES = {
  "16:9": [[0.5, 0.37, 0.44, 7], [0.25, 0.5, 0.44, -20], [0.5, 0.31, 0.3, 10]],
  "9:16": [[0.5, 0.31, 0.52, 7], [0.5, 0.27, 0.44, -14], [0.5, 0.27, 0.38, 10]],
  "1:1": [[0.5, 0.33, 0.4, 7], [0.5, 0.27, 0.32, -14], [0.5, 0.26, 0.28, 10]],
  "4:5": [[0.5, 0.32, 0.46, 7], [0.5, 0.27, 0.38, -14], [0.5, 0.26, 0.32, 10]],
}[document.documentElement.dataset.format] || [[0.5, 0.35, 0.4, 7], [0.5, 0.28, 0.34, -14], [0.5, 0.27, 0.3, 10]];
const [, S2, S3] = host.cuts;

// Seeded dust: generated once, moved analytically from t.
const rand = rng(7);
const N = Q.particles, pos = new Float32Array(N * 3), base = [];
for (let i = 0; i < N; i++) base.push([(rand() - 0.5) * 12, (rand() - 0.5) * 8, (rand() - 0.5) * 6 - 2, rand() * Math.PI * 2]);
const dustGeo = new THREE.BufferGeometry(); dustGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
scene.add(new THREE.Points(dustGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.02, transparent: true, opacity: 0.3 })));

const glow = glowPlane(accent, Q.glowPx); scene.add(glow);
const logo = new THREE.Group(); scene.add(logo);

// Three small parts that orbit the object in S2 (the "everything in one place" metaphor). Swap or delete them.
const partMat = [new THREE.MeshStandardMaterial({ color: accent, metalness: 0.4, roughness: 0.35 }),
                 new THREE.MeshStandardMaterial({ color: ink, metalness: 0.2, roughness: 0.5 })];
const parts = [new THREE.Mesh(new THREE.SphereGeometry(0.5, Q.sphereSegments, Q.sphereSegments / 2), partMat[0]),
               new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 0.8), partMat[1]),
               new THREE.Mesh(new THREE.OctahedronGeometry(0.6), partMat[0])];
parts.forEach((m) => scene.add(m));
const callout = document.getElementById("callout");
const tmp = new THREE.Vector3();

new SVGLoader().load("assets/logo.svg", (data) => {
  // Measure the logo first, so depth and bevel scale with it whatever the SVG's own units are.
  const shapes = [];
  const box2 = new THREE.Box2();
  data.paths.forEach((p, i) => SVGLoader.createShapes(p).forEach((shape) => {
    shapes.push([shape, p, i]);
    shape.getPoints(8).forEach((pt) => box2.expandByPoint(pt));
  }));
  const dim = Math.max(box2.max.x - box2.min.x, box2.max.y - box2.min.y) || 1;
  // Each SVG path keeps its own fill (multi-colour logos); paths without a fill use --accent.
  // Later paths sit slightly in front so overlapping layers don't z-fight.
  const mats = new Map();
  shapes.forEach(([shape, p, i]) => {
    const fill = p.userData && p.userData.style && p.userData.style.fill;
    const hex = fill && fill !== "none" ? new THREE.Color().setStyle(fill).getHex() : accent.getHex();
    if (!mats.has(hex)) mats.set(hex, new THREE.MeshStandardMaterial({ color: hex, metalness: 0.55, roughness: 0.32 }));
    const geo = new THREE.ExtrudeGeometry(shape, { depth: dim * 0.09, bevelEnabled: true, bevelThickness: dim * 0.015,
      bevelSize: dim * 0.011, bevelSegments: Q.bevelSegments, curveSegments: Q.curveSegments });
    geo.translate(0, 0, i * dim * 0.022);
    logo.add(new THREE.Mesh(geo, mats.get(hex)));
  });
  // Centre it and make its longer side 1 unit. The SVG y axis points down, hence the -1.
  const box = new THREE.Box3().setFromObject(logo);
  const size = box.getSize(new THREE.Vector3()), center = box.getCenter(new THREE.Vector3());
  logo.children.forEach((m) => m.geometry.translate(-center.x, -center.y, -center.z));
  const unit = 1 / Math.max(size.x, size.y);

  host.render = (t) => {
    const D = host.duration;
    camera.position.set(0, 0, DIST - 0.45 * easeInOutCubic(t / D));   // slow dolly-in over the film
    camera.lookAt(0, 0, 0);

    // Blend the layout poses across the two cuts.
    const u1 = easeInOutCubic((t - (S2 - 0.25)) / 0.9), u2 = easeInOutCubic((t - (S3 - 0.25)) / 0.9);
    const p = POSES[0].map((v, k) => lerp(lerp(v, POSES[1][k], u1), POSES[2][k], u2));
    const at = screenToWorld(camera, p[0], p[1]);
    const S = worldSize(camera, p[2]);

    // The object is already in place at frame 0 (the thumbnail): it turns and grows the last bit,
    // then floats a little so no hold is frozen.
    const r = easeOutExpo(t / 1.2), g = S * unit * (0.8 + 0.2 * r);
    logo.position.set(at.x, at.y - 0.08 * S * (1 - r) + Math.sin(t * 1.1) * 0.025 * S, 0);
    logo.rotation.y = THREE.MathUtils.degToRad(p[3]) - 0.7 * (1 - r) + Math.sin(t * 0.7) * 0.04;
    logo.scale.set(g, -g, g);
    glow.position.set(at.x, at.y, -0.8); glow.scale.setScalar(S * 2.3); glow.material.opacity = 0.85 * (0.55 + 0.45 * r);

    // Rim light: one sweep after the entrance, one back across the end card.
    rim.position.x = -4 + 8 * easeInOutCubic((t - 0.8) / 1.4) - 8 * easeInOutCubic((t - S3 - 0.1) / 1.2);

    // Orbiting parts, on stage only during S2.
    const k = easeInOutCubic((t - S2 - 0.2) / 0.5) * (1 - easeInOutCubic((t - (S3 - 0.5)) / 0.35));
    parts.forEach((m, i) => {
      const a = t * 0.9 + (i * Math.PI * 2) / 3;
      m.position.set(at.x + Math.cos(a) * S * 0.74, at.y + Math.sin(a) * S * 0.26, Math.sin(a) * S * 0.55);
      m.rotation.set(t * 0.8 + i, t * 0.6, 0);
      m.scale.setScalar(Math.max(1e-4, S * 0.15 * k));
    });

    // The HTML label follows the object's upper right corner (sharp text, any language).
    pin(callout, camera, tmp.set(at.x + S * 0.34, at.y + S * 0.44, 0), W, H, 0, -callout.offsetHeight);

    for (let i = 0; i < N; i++) {
      const b = base[i];
      pos[i * 3] = b[0] + Math.sin(t * 0.3 + b[3]) * 0.2;
      pos[i * 3 + 1] = b[1] + t * 0.08;
      pos[i * 3 + 2] = b[2];
    }
    dustGeo.attributes.position.needsUpdate = true;
    renderer.render(scene, camera);
  };
  host.render(host.t);
  host.ready();
});
