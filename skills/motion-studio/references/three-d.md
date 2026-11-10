# 3D with Three.js (inside HyperFrames)

HyperFrames renders by **seeking** each frame in headless Chrome: frames can be requested in any order. So every 3D scene must be a pure function of time:

> `state = f(t)` where `t = frame / fps`. Same `t` → same pixels, always.

Use the `/hyperframes` skill for how the composition hosts a Three.js scene in the current HyperFrames version. This file covers *what* to build and the rules that keep it correct.

## Hard rules
- No `requestAnimationFrame` render loops, no `Date.now()`/`performance.now()` for motion, no `THREE.Clock` driving motion.
- No physics engines or simulations that depend on previous frames. Compute positions analytically from `t`.
- Randomness only from a seeded generator (e.g. mulberry32 with a fixed seed), generated once at setup.
- Load every model, texture, HDRI and font **before** the first frame. Nothing is fetched mid-render. Keep assets in `assets/3d/`.
- Use `renderer.setPixelRatio(1)` and the composition's exact width and height. Enable antialiasing.
- Dispose of geometries, materials and textures when the scene ends.

## What to build (common promo 3D)
| Need | Approach |
|---|---|
| 3D logo reveal | Logo SVG → `SVGLoader` → `ExtrudeGeometry` with a small bevel. Metallic or clay material. Camera arc plus a light sweep |
| 3D title text | `TextGeometry` with a typeface JSON converted from a **licensed** font. Latin, or simple scripts only (see below) |
| Product with a real 3D model | User-supplied GLB/GLTF → `GLTFLoader`. Turntable or orbit, soft shadow plane |
| Product from photos only | **2.5D**: the cut-out image on a plane with a slight tilt, a contact shadow and camera parallax. Never fake a 3D model of a real product |
| Abstract hero backgrounds | Low-poly shapes, gradients, particles from a seeded field. Animate with sin/cos of `t` |
| Device mockup | Simple rounded-box device with the screenshot as an emissive texture on the screen face |

## Look
- Lighting: a key, fill and rim setup, or `RoomEnvironment` + `PMREMGenerator` for soft studio reflections (no external HDRI needed).
- Colour: use `THREE.NeutralToneMapping` (exposure about 0.95), as the 3D starter does, so brand colours stay true. ACES Filmic washes out saturated colours (in testing, a lime logo came out pale yellow); switch to it only for a deliberately filmic look with no brand colours at stake. sRGB output. Pull materials and lights from the brand palette; lower `scene.environmentIntensity` (about 0.7) if colours look chalky.
- Multi-colour logos: keep each SVG path's own fill and offset later paths slightly in depth (the 3D starter does this).
- Camera: ease every move (`easeInOutCubic`, `easeOutExpo`). Typical: a 20–40° orbit over 2–4 s, or a dolly-in of 10–20%. One camera idea per shot.
- Depth: fog or a gradient background, shallow contact shadows. Avoid pure-black voids unless the style calls for it.

## Text in 3D and non-Latin scripts
Three.js text geometry doesn't do complex shaping (Bengali, Devanagari, Arabic, Thai…). For those scripts, render the text with HTML/CSS layered over the 3D canvas, or draw it to a canvas texture using the browser's text engine. Never extrude complex-script text glyph by glyph.

## Performance
Keep scenes light: fewer than ~200k triangles, textures ≤ 2048 px, at most 2–3 shadow-casting lights. If a render is slow, reduce shadows first, then texture size.

On a host without a GPU (preflight's HOST line says so; cloud sandboxes usually have none) WebGL runs on the CPU. The 3D starter captures about 5 frames per second on 2 cores, so a 20 s film takes about 2 minutes. Plan for it: render with `scripts/render.py` (it resumes across calls), keep previews at draft quality, and prefer one strong 3D shot over 3D in every scene.

## Check
- `npm run check` **cannot see inside a WebGL canvas**: it won't flag a 3D object covering text. Always render stills of the 3D scene with its text layers and look at them.
Render stills at t = start, middle and end, plus one t in the middle of a move. Then render the same t twice and confirm the frames are identical (determinism check).
