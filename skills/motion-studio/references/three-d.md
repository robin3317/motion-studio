# 3D with Three.js (inside HyperFrames)

## 3D is the default
Build every video on the 3D starter (`templates/three-starter`, what `new_project.py` creates) **unless** the user asks for 2D or flat, names a 2D style (`isometric-kinetic`), or the job is a footage edit. Don't ask "2D or 3D?". Decide, log it in `decisions.md`, and tell the user in one line that saying "2D" switches it.

"3D" means **one real 3D stage with depth, light and a moving object under sharp HTML text**. It does not mean every element is a mesh:
- In 3D: the hero object (logo, product, device, abstract shape), its supporting parts, light, camera and depth.
- In HTML, on top: every headline, label, pill, card, button and caption. Text stays sharp and any language shapes correctly.

## The one rule that makes it render
HyperFrames renders by **seeking** each frame in headless Chrome, in any order. Every 3D scene must be a pure function of time:

> `state = f(t)` where `t = frame / fps`. Same `t` → same pixels, always.

- No `requestAnimationFrame` loops, no `Date.now()`/`performance.now()`, no `THREE.Clock` driving motion.
- No physics or simulations that depend on earlier frames. Compute positions from `t`.
- Randomness only from a seeded generator (`rng(seed)` in `lib/ms3d.js`), generated once at setup.
- Load every model, texture and font **before** the first frame. Keep 3D assets in `assets/3d/`.
- `renderer.setPixelRatio(1)`, the composition's exact size, antialiasing on. Keep `preserveDrawingBuffer: true`: `visual_audit.py` reads the canvas.

## The 3D starter, and where to edit it
| File | Holds | Edit for |
|---|---|---|
| `index.html` | Tokens, the HTML text scenes, the one timeline. Its linear clock calls `host.render(t)` | Copy, scene times, text motion, colours, fonts |
| `lib/stage.js` | Everything drawn in WebGL: object, parts, light, glow, dust, camera | `POSES`, the object, materials, what happens in each scene |
| `lib/ms3d.js` | Helpers: `screenToWorld`, `worldSize`, `pin`, `glowPlane`, `labelTexture`, `rng`, eases, `quality` | Rarely |
| `assets/logo.svg` | Placeholder logo | Replace with the real logo (clean paths) |

**Layout poses.** The camera stays on the z axis and the object moves between poses, one per scene: `[x, y, size, yaw]`, with x and y as fractions of the frame and size as a fraction of the shorter side. Poses are set per format in `POSES`. This is how the object stays out of the text: when you move a text zone, move the pose. A new scene = a new pose plus one blend line.

## Keep 3D out of the text zones
- Give each scene a text zone and an object zone before building: text low and object high (the starter's default), or text on one half and the object on the other (16:9, `.safe.side`).
- Nothing bright or detailed may pass behind text. Parts that orbit must stay inside the object zone at every `t`.
- `npm run check` **cannot see inside a WebGL canvas**. `scripts/visual_audit.py` can: it reports `text_over_3d` when more than 15% of the area behind a text block is not background. Run it before every preview and look at the sheets.

## Text and UI in 3D
Borders, rounded corners and small text are where 3D videos look cheap. Use the first option that works:

1. **HTML over the canvas (default).** Pills, tags, cards and buttons use the template's component classes (`craft.md`, "Components"). Always sharp.
2. **HTML pinned to a 3D object.** `pin(el, camera, worldPosition, W, H, dx, dy)` moves an absolutely positioned element to follow a point in the scene (the starter's `#callout`). Use it for callouts, labels on parts and prices next to a product.
3. **HTML with a CSS 3D tilt**, for a panel that should look like it stands in the scene: `transform: perspective(1400px) rotateY(-14deg) rotateX(4deg)` on the card, the angle matching the object's yaw. Keep the tilt at 20° or less so text stays readable.
4. **A canvas texture inside the scene**, only when the label must turn with an object or pass behind something: `labelTexture(text, { font, fill, stroke, color, heightWorld })`. It insets the stroke by half its width (so the border is never clipped), centres the text on its real letter shapes, and builds mipmaps. Rules: load the font first (`await document.fonts.load('700 96px "Body"')`); make the font size in the texture at least 2× the size it will have on screen; `toneMapped: false`; no bloom, scanlines or glitch over it; Latin and simple scripts only when the label is turned more than a few degrees.

Never draw a rounded border with a thin `TubeGeometry` or line loop, and never extrude small text.

## Glow, not bloom
A post-processing bloom pass blurs text edges, eats saturated brand colours and is the most expensive thing on a CPU. Default: **no bloom**. For glow use `glowPlane(color)`: one additive plane with a radial gradient behind the object. If a style really needs bloom (rare): half resolution, threshold high enough that only lights and emissive edges pass, and never over the logo wordmark or any text.

## What to build
| Need | Approach |
|---|---|
| 3D logo reveal | Logo SVG → `SVGLoader` → `ExtrudeGeometry` with a small bevel, depth about 9% of the logo's size (the starter). It turns in and **rests about 10° off-axis**, so the bevel catches light. Front-on looks flat |
| 3D title text | `TextGeometry` from a **licensed** font's typeface JSON. Latin or simple scripts only. No emissive face, no bloom on a wordmark |
| Product with a real 3D model | User-supplied GLB/GLTF → `GLTFLoader`. Turntable or orbit, soft shadow plane |
| Product from photos only | **2.5D**: the cut-out image on a plane with a slight tilt, a contact shadow and parallax. Never fake a 3D model of a real product |
| Screens and UI | A rounded-box device with the real screenshot as the screen texture (`toneMapped: false`, so colours stay true) |
| Ideas without a picture | A metaphor built from simple solids (`craft.md` rule 6): parts orbiting a hero, a stack coming apart, columns growing. Animate with eases and sin/cos of `t` |

## Look
- Light: key, fill and rim, or `RoomEnvironment` + `PMREMGenerator` for soft studio reflections (no external HDRI). Sweep the rim light once after the entrance and once on the end card.
- Colour: `THREE.NeutralToneMapping` (exposure about 0.95) keeps brand colours true. ACES Filmic washes out saturated colours. sRGB output. Take materials and lights from the brand palette.
- Multi-colour logos: each SVG path keeps its own fill; later paths sit slightly in front.
- Motion: ease every move (`easeInOutCubic`, `easeOutExpo`). One idea per shot: a turn of 20–40° over 2–4 s, or a dolly of 10–20%. During holds the object floats a little, so the frame is never frozen.
- Frame 0: the object is already in place and lit at `t = 0` (it turns and grows the last 20%). Never start on an empty stage.
- Depth: a glow or gradient behind the object, sparse seeded dust. Avoid a pure-black void unless the style asks for it.

## Text in 3D and non-Latin scripts
Three.js text geometry doesn't shape complex scripts (Bengali, Devanagari, Arabic, Thai…). Keep that text in HTML (options 1–3 above). Never extrude complex-script text glyph by glyph.

## Quality profile and speed
`<html data-quality="cpu|standard">` is set by `new_project.py` (`cpu` on hosts with 4 cores or fewer, or `--quality`). `quality()` in `lib/ms3d.js` returns the counts to use: particles, curve and bevel segments, glow texture size. Read from it when you add geometry; the look must be the same in both profiles.

On a host without a GPU (preflight's HOST line) WebGL runs on the CPU: about 5 frames per second on 2 cores, so a 20 s film takes a few minutes. That is fine: `scripts/render.py` resumes across calls. Keep the scene light anyway: under ~200k triangles, textures ≤ 2048 px, no shadow maps unless a shot needs one, no bloom, no CSS `backdrop-filter` over the canvas.

## Check
- After each scene: `python scripts/preview_sheet.py --scene s2` and look at the whole move.
- Before every preview: `python scripts/visual_audit.py` (text over 3D, component borders and centring).
- Determinism: render the same `t` twice and confirm the frames are identical.
