# product-float-callouts
**Use for:** showing 1–3 features on the product.  **Length:** 3–5 s
**Needs:** product image or 3D; short feature labels (≤ 4 words) from `facts.json`.
**Beats**
- 0.0–0.4: product shifts to one side (or scales down) to make room
- 0.3–1.2: callout lines draw from feature points on the product, labels pop in at the line ends (stagger 0.25 s)
- Hold for reading time; gentle product float (±6 px sine)
- Exit: lines retract, or a cut to the next feature
**Ease:** `power3.out` lines, `back.out(1.4)` labels.  **SFX:** small tick per label (max 3), or one soft swell.
**Avoid:** labels covering the product; more than 3 labels at once.
**Registry starting points:** hw-callout-circle, cursor-annotate, mk-callout-highlight. Check availability with the `/hyperframes-registry` skill (the catalogue changes). Restyle the block to the preset; don't ship it unchanged.
