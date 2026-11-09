# timeline-axis
**Use for:** company history ("since 2009"), release dates, a roadmap, version history, "3 steps in 5 minutes".  **Length:** 3–4.5 s
**Needs:** 2–5 dated points (year/date + 1–3 word label), all from `facts.json`.
**Beats**
- 0.0–0.6: a horizontal axis line draws left → right (vertical in 9:16), with mono tick marks
- 0.3 → : flags or tiles pop up at each point in order (`drop`, staggered 0.15–0.25 s, on beats if you can); each carries the date (mono) + label
- Last point: the "now" or launch date. It's bigger, in the brand colour, and can be a flip-clock (`IsoKit.flip(tl, el, "2024", "2026", t)`) or a big year with a cube replacing one digit
- Hold ≥ 1 s on the final point
**Build:** SVG line + ticks (draw with `stroke-dashoffset`), flags as small `box`/`tile` objects or HTML tags; `flip()` builds its cards once, so it's seek-safe.
**SFX:** a tick per point, a whoosh on the axis draw, a hit on the final point.
**i18n:** dates in the brief's locale and digits (`typography-i18n.md`).
**Avoid:** more than 5 points; dates that aren't sourced; even spacing when the real intervals are very uneven (space them proportionally, or label the gap).
**Registry starting points:** search for timeline blocks in the registry and restyle. Check with the `/hyperframes-registry` skill.
