# iso-orbit-hero
**Use for:** "one platform / everything in one place", a product or app at the centre of its features, a brand at the centre of its services.  **Length:** 3–5 s
**Needs:** the hero label (brand name, product name or logo SVG for the top face) and 3–5 short feature tags (1–2 words each, from `facts.json`).
**Beats**
- 0.0–0.5: plate + hero cube drop in (brand colour, logo or name on the top face via `labels.top`)
- 0.3–0.9: an elliptical orbit ring grows in around the cube's base (template: scale 0.3 → 1, `expo.out`; a stroke-dashoffset draw-on also works)
- 0.6–1.2: tags pop onto the ring, staggered 0.1 s
- 0.8 → end: tags orbit slowly (≈ 0.9 π over the scene, linear). Tags behind the cube fade to 0 and tags in front are fully opaque (opacity from sin of the angle), so the orbit reads as 3D
- Headline on the opposite side: two lines, the accent word on the benefit ("one **place**")
**Build:** template scene S2. The orbit is a tween on a plain object `{a}` with an `onUpdate` that only does arithmetic on constants computed at load (no DOM reads), so it stays seek-safe and passes lint.
**SFX:** a short whoosh as the ring draws; a light tick per tag.
**Avoid:** more than 5 tags (it becomes a list; use `iso-platform-row` or `feature-grid`); tags long enough to collide on the ring; a fast orbit (keep it under one full turn per scene).
**Registry starting points:** none. Build from the template.
