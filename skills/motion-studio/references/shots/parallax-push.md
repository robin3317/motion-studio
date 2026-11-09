# parallax-push
**Use for:** making stills feel alive: screenshots, photos, key art, scenes.  **Length:** 2–4 s
**Needs:** an image split into 2–4 depth layers (background, mid, subject, text), or separate assets.
**Beats**
- 0.0–end: a virtual camera pushes in (scale 1.0 → 1.12) while the layers move at different rates (background slowest)
- Optional subtle rotation (≤ 2°) or a lateral drift
- Text layer on top, entering at 0.3 s
**Ease:** `sine.inOut` or linear with ease at the ends.  **SFX:** soft air whoosh or room tone swell (optional).
**Avoid:** scaling low-res images past their resolution; layer edges showing gaps (overscan the layers by 10%).
**Registry starting points:** parallax-zoom, push-in, camera-rig-depth-stack, pull-back-reveal. Check availability with the `/hyperframes-registry` skill (the catalogue changes). Restyle the block to the preset; don't ship it unchanged.
