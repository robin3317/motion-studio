# logo-assemble
**Use for:** opening brand moment, or the logo at the end.  **Length:** 1.5–3 s
**Needs:** logo as SVG (preferred; separable paths) or PNG.
**Beats**
- 0.0–0.6: logo pieces (paths, or slices of the PNG) fly or scale in from offset positions, staggered 0.05 s
- 0.6–1.0: pieces settle into the final logo with a slight overshoot
- 1.0–1.3: accent flash or light sweep across the logo. Optional tagline fades up underneath
- Hold to the end
**Ease:** `expo.out` for the fly-in, `back.out(1.2)` to settle.  **SFX:** soft whoosh (start 0.1 s early) + a hit on settle.
**Variants:** stroke draw-on (SVG strokes), then a fill fade; particles converging (seeded).
**Avoid:** distorting logo proportions; changing brand colours mid-animation.
**Registry starting points:** logo-sting, wordmark-tiles, outline-draw, svg-stroke-trace. Check availability with the `/hyperframes-registry` skill (the catalogue changes). Restyle the block to the preset; don't ship it unchanged.
