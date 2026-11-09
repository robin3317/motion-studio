# 3d-logo-reveal
**Use for:** premium brand openings and closings, release title reveals.  **Length:** 2.5–4 s
**Needs:** logo SVG (clean paths). Follow `three-d.md`.
**Beats**
- 0.0–1.5: camera arcs 25–40° around the extruded logo, starting close or in darkness
- 0.8–1.6: rim light sweeps across the bevel. Haze or particles drift
- 1.5–2.5: camera settles front-on and the logo rests at its final scale
- 2.2+: tagline (HTML layer) fades in under it
**Ease:** `easeInOutCubic` camera, `easeOutExpo` settle.  **SFX:** low riser → impact/boom on settle, metallic shimmer on the light sweep.
**Material ideas:** brushed metal, glossy plastic in the brand colour, frosted glass.
**Avoid:** extruding wordmarks in complex scripts (use an HTML overlay); camera spins over 90°.
**Registry starting points:** extruded-logo, light-sweep-pass, lens-flare. Check availability with the `/hyperframes-registry` skill (the catalogue changes). Restyle the block to the preset; don't ship it unchanged.
