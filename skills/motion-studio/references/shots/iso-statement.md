# iso-statement
**Use for:** the hook or any claim scene: a headline next to (16:9) or above (9:16, 1:1) one isometric object group that shows the claim as a physical metaphor.  **Length:** 2.5–4 s
**Needs:** a headline of ≤ 6 words with one accent word; a metaphor (growth → rising columns, choice → three doors, speed → a pill racing along a track).
**Beats**
- 0.0: eyebrow + headline line 1 + plate + first object already visible (frame 0 = thumbnail when this opens the video)
- 0.0–0.6: line 1 settles (small y rise, `expo.out`)
- on the next VO word or beat: line 2 rises out of its mask (0.55 s); the accent word is in this line when possible
- 0.3–1.4: the remaining objects drop in, staggered 0.08 s (`back.out(1.6)`); the hero object (brand colour) lands last
- Hold ≥ 1 s with an ambient float (hero ±6 px, 2 s period); hard cut
**Build:** template scene S1 (`templates/isometric-kinetic`). `IsoKit.plate` + `box` (hero `color: BRAND.accentOnDark` or `solid`), `prepLines` / `revealLines`, `drop`.
**SFX:** soft click per line, "tok" per object landing (keep 3 at most; layer the rest at −6 dB).
**i18n:** non-Latin headlines reveal by line (no letter splitting); allow 15–20% more width.
**Avoid:** objects overlapping the headline column; more than 5 objects; a metaphor that needs a caption to explain it.
**Registry starting points:** none fit exactly. Build from the template.
