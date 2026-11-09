# Isometric Kinetic: style analysis (v0.2 input, 2026-11-09)

Sources: Robin's personal skill `isometric-kinetic` (rules) + frame study of a reference explainer
(".NET in 5 Minutes", 116 s, 16:9). We copy *techniques*, not the reference's look or assets.

## Observed (about 30 frames)
- **Frame furniture**: HUD top-left `● <SERIES> · <EPISODE>` (tiny mono caps); top-right `SCENE 07 / <SCENE NAME>` + running timecode. Small creator badge bottom-right.
- **Captions**: bottom-centre dark pill, 2–4 words, the spoken word on a yellow block with dark text.
- **Headlines**: large geometric sans, regular weight, lowercase/sentence case, 1–3 lines, left-aligned; ONE accent word in bold + brand colour. Each line appears when it's spoken (line mask rise).
- **Eyebrow**: `—— MONO CAPS · CONTEXT` above the headline, ~45% opacity.
- **Palette rhythm**: charcoal dark (most scenes) → paper off-white every few scenes → solid brand colour for big moments. Never gradients-everywhere.
- **Isometric objects**: flat 3-tone faces (top lightest, left mid, right darkest), thin dark outlines; neutral white/grey objects + brand-coloured hero object with a logo on its top face. Plates/platforms under objects, dashed-outline placeholders that "fill in", stacked layers with labels on leader lines, numbered tiles in a row (chapter list), server racks, laptop, orbit ring (ellipse) around a hero cube, traveling pills (`GET /`, `200 OK`) along paths.
- **Templates seen**: terminal window, number + ruler axis, giant year with a cube replacing a digit, flip-clock cards, document card, timeline axis with version flags, exploded stack, platform comparison (3 plates), chapter tiles, checklist, browser mock, perspective road for "a date".
- **Pace**: cuts every ~3–4 s (32 scenes in ~115 s), hard cuts, motion = fast in → hold → cut. Objects drop in with slight overshoot; ambient float/travel during holds.

## Rules taken from Robin's skill (generalised)
headline ≤ 6 words with exactly one accent word · every abstract idea gets a physical metaphor · never the same template twice in a row · background rhythm dark→light every 3–4 scenes→solid for big numbers · auto-fit headlines + descender padding · 2:1 isometric projection, flat fills, outline 3–4 px · line-mask reveal expo-out 0.5–0.6 s, 0.1 s stagger · counters ease-out · ambient loops · every frame a pure function of t.

## For motion-studio (brand-neutral)
Charcoal/paper/brand-solid trio derived from the brand palette; HUD = brand · campaign (optional); captions only when there is a voice; headline lines sync to VO words, or to music beats when there's no VO.
