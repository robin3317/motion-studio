# stat-counter
**Use for:** a key number (clients, users, years, %).  **Length:** 2–3.5 s
**Needs:** the number + label from `facts.json` (exact value, suffix like "+", "%").
**Beats**
- 0.0–0.3: label and container appear
- 0.2–1.4: number counts up from 0 (or a lower round value) with ease-out, so it slows near the end
- 1.4: lands on the exact value + accent (underline, glow, scale tick 1.0 → 1.05 → 1.0)
- Hold ≥ 1 s at the final value
**Ease:** `power3.out` (count), `back.out` (tick).  **SFX:** subtle ticking texture during the count (optional) + a hit on landing.
**i18n:** format with the locale's digits and separators if the brief uses them.
**Avoid:** counting to a number that isn't sourced; decimals flickering unreadably.
**Registry starting points:** count-up, number-pop-in, number-wheel, mk-progress-stat. Check availability with the `/hyperframes-registry` skill (the catalogue changes). Restyle the block to the preset; don't ship it unchanged.
