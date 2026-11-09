# device-mockup-screens
**Use for:** apps, websites, SaaS, digital products.  **Length:** 3–6 s
**Needs:** real screenshots (`capture_site.mjs`) at device resolution; a device frame (CSS-drawn or simple 3D, no trademarked device artwork unless the user supplies it).
**Beats**
- 0.0–0.6: device slides or tilts in (2.5D perspective)
- 0.6–end: screen content scrolls smoothly or swaps screens with a crossfade; a cursor or tap ripple highlights one action
- Optional: zoom into a UI detail (scale 1.0 → 1.6) with a label
**Ease:** `power2.inOut` scroll, `power3.out` entrance.  **SFX:** soft UI clicks on taps, a light whoosh on the entrance.
**Avoid:** tiny unreadable UI (zoom in instead); private user data in the screenshots (blur it).
**Registry starting points:** device-frame-stage, browser-device-stage, parallax-device-dive, multi-device-splay. Check availability with the `/hyperframes-registry` skill (the catalogue changes). Restyle the block to the preset; don't ship it unchanged.
