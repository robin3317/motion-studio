# caption-highlight
**Use for:** word-timed captions on talking footage or VO videos.  **Length:** continuous
**Needs:** a corrected transcript with word timings (re-timed to the EDL for footage edits).
**Behaviour**
- Show 1 line (bold social: 1–3 words) or 2 lines (clean subtitle) at a time; break lines at phrase boundaries
- The current word gets the accent: colour change, background pill, or scale 1.0 → 1.08
- Groups change on sentence/phrase ends, never mid-word
- Text: high contrast, stroke or shadow for legibility over footage
**Placement:** 9:16 ≈ 62–72% height (above the platform UI); 16:9 bottom 12% margin.
**i18n:** highlight by **word**; never split complex-script words into characters. RTL order respected.
**Avoid:** covering faces or on-screen graphics; caption sizes below the minimum (`typography-i18n.md`).
**Registry starting points:** caption-highlight, caption-pill-karaoke, caption-kinetic-slam, caption-editorial-emphasis. Check availability with the `/hyperframes-registry` skill (the catalogue changes). Restyle the block to the preset; don't ship it unchanged.
