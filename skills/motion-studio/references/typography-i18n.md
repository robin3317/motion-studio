# Typography & any-language text

## Fonts: licence first
- Use fonts with a licence that allows video use: SIL Open Font License (most Google Fonts), Apache, or the brand's own fonts **supplied by the user**.
- Download font files into `assets/fonts/` and load them locally. Never rely on a font CDN at render time.
- Easiest source of OFL fonts: npm `@fontsource/<family>` packages (e.g. `npm i @fontsource/space-grotesk @fontsource/noto-sans-bengali`). Copy the needed `.woff2` files from `node_modules/@fontsource/<family>/files/` into `assets/fonts/`. They work offline, and the licence file sits next to them. Alternative (used by `templates/isometric-kinetic`): list the `@fontsource` packages in the composition's `package.json` and point `@font-face` at `node_modules/@fontsource/<family>/files/...`; `npm install` then fetches them once, before rendering.
- Symbols from another script (e.g. the taka sign ৳ inside English text): add a second `@font-face` with the **same family name** and a `unicode-range` (e.g. `U+0980-09FF` for Bengali). The browser then uses it only for those characters.
- Don't use `-webkit-text-stroke` for caption outlines: on fonts with overlapping contours it draws lines through the letters. Use layered `text-shadow` instead.
- Record each font in `credits.json` (name, source, licence).

## Size and layout (at the format's full resolution)
| Format | Headline | Body / support | Minimum |
|---|---|---|---|
| 16:9 1920×1080 | 90–160 px | 42–60 px | 36 px |
| 9:16 1080×1920 | 100–170 px | 48–64 px | 42 px |
| 1:1 / 4:5 | 90–150 px | 44–60 px | 38 px |

- Max ~7 words per line, 2 lines per text block (3 for small support text).
- Contrast ≥ 4.5:1 between text and its background. Add a scrim, shadow or panel over busy images.
- **Safe zones**: keep key text and the CTA inside them.
  - 16:9: 5% margin on all sides.
  - 9:16: x 8%–88%, y 12%–72% (the platform UI covers the top, bottom and right edge).
  - 1:1 and 4:5: 6% margin.

## Script → font suggestions (free, OFL)
| Script / languages | Sans | Display / serif |
|---|---|---|
| Latin, Cyrillic, Greek | Inter, Manrope, Space Grotesk, Poppins | Bebas Neue (Latin), Anton, Playfair Display, Fraunces, DM Serif Display |
| Bengali (Bangla) | Hind Siliguri, Noto Sans Bengali, Anek Bangla | Tiro Bangla, Noto Serif Bengali, Baloo Da 2, Galada |
| Devanagari (Hindi, Marathi, Nepali) | Noto Sans Devanagari, Mukta, Hind | Tiro Devanagari Hindi, Yatra One |
| Arabic, Urdu, Persian (RTL) | Noto Sans Arabic, Cairo, IBM Plex Sans Arabic, Tajawal | Amiri, Noto Nastaliq Urdu (Urdu) |
| Chinese / Japanese / Korean | Noto Sans SC / TC / JP / KR | Noto Serif SC / JP / KR |
| Thai | Noto Sans Thai, Prompt | Noto Serif Thai |
| Code / mono | JetBrains Mono, IBM Plex Mono | – |

Pair a display font for headlines with a sans for support text. When two scripts appear together (e.g. Bangla + English), choose fonts with matching weight and x-height, or a family that covers both (e.g. Noto Sans + Noto Sans Bengali).

## Complex-script rules (Bengali, Devanagari, Arabic, Thai…)
- **Never split text into individual characters** for animation: it breaks conjuncts, matras and letter joining. Animate by **word** or by line.
- No letter-spacing (`letter-spacing: 0`). No `text-transform: uppercase` outside Latin, Cyrillic and Greek.
- Line height 1.35–1.6 (stacked marks need room).
- Set `lang` on the text element (`lang="bn"`, `lang="ar"`…). For RTL, set `dir="rtl"`, mirror the layout direction, and animate from the right.
- Don't extrude complex scripts in 3D (see `three-d.md`).
- Always render a still and **look at it**. Check conjuncts, vowel signs, joining and that no glyph shows as a box (tofu).

## Numbers & dates
Use the locale's numerals and date format when the user's language expects them (e.g. Bengali digits ০–৯ for a Bangla audience, if the user prefers). Ask in Step-by-step; in Autopilot follow the brief's own usage.
