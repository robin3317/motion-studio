# Typography & any-language text

## Choosing fonts (S3, every video)
The fonts carry more of the look than the colours do. Don't ship the template's default pair, and don't reach for Inter or Poppins because they are familiar: choose for this brand.
1. **Define the roles:** display (headlines), body (support lines, labels, buttons), and mono only if the style uses code or data labels. Two families at most, plus mono.
2. **If the brand has its own font:** ask the user for the files. If they can't supply them, take the closest free one from the table below, and say in the final message which font was replaced by which.
3. **Otherwise pick 2–3 candidates per role** that fit the style preset and the script (table further down), set the hook headline in each, render stills, and choose. Step-by-step: show them at G3. Autopilot: choose and log why.
4. **Fetch the choice:** `python "<skill>/scripts/get_font.py" "Space Grotesk" --weights 500,700 --as Display` (and `--as Body`). It downloads the `.woff2` files and the licence from npm's `@fontsource` into `composition/assets/fonts/`, prints the `@font-face` rules to paste, and adds the font to `credits.json`. `--list` shows a family's weights and subsets. npm is reachable in sandboxes where font sites are blocked.
5. **For a more distinctive face** than the open-source catalogue has (Fontshare, Open Foundry and similar free foundries): download only from the font's official page, on the user's machine if the sandbox blocks the site, read the licence on that page, and save the licence text next to the font files. No licence you can point to means no font.
6. **Non-Latin text:** check that the family really has the script (`--list` shows the subsets), fetch that subset under the **same** `--as` name, and look at a still: conjuncts, vowel signs, no boxes.
7. Write the final pair into `style.md` (family, weights, files, licence).

### Brand font → closest free font
The look is close, not identical. Always tell the user about the swap.
| Brand uses | Free alternative (on @fontsource) |
|---|---|
| Helvetica, Helvetica Neue, Arial, SF Pro | Inter, Inter Tight, Arimo |
| Proxima Nova, Gotham, Montserrat-like geometric | Montserrat, Figtree |
| Circular, Gilroy, Sofia Pro | Outfit, Urbanist, Plus Jakarta Sans |
| Futura | Jost |
| Avenir, Avenir Next | Nunito Sans, Mulish |
| DIN, DIN Next | Barlow, Barlow Condensed |
| Akzidenz-Grotesk, Univers | Archivo, Public Sans |
| Graphik, Söhne, Suisse | Inter Tight, Be Vietnam Pro, Instrument Sans |
| Segoe UI, Frutiger, Myriad | Open Sans, Source Sans 3, Hind |
| Garamond | EB Garamond, Cormorant Garamond |
| Didot, Bodoni | Bodoni Moda, Playfair Display |
| Times, Georgia | Tinos, Gelasio, Source Serif 4 |
| Courier, Menlo, SF Mono | JetBrains Mono, IBM Plex Mono |

## Fonts: licence first
- Use fonts with a licence that allows video use: SIL Open Font License (most Google Fonts), Apache, or the brand's own fonts **supplied by the user**.
- Font files live inside the composition and load from disk. Never rely on a font CDN at render time.
- The two starters load their default pair from `node_modules/@fontsource/...` (installed by `npm install`). Fonts fetched with `get_font.py` live in `composition/assets/fonts/<family>/` with their licence file.
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
| Latin, Cyrillic, Greek | Manrope, Space Grotesk, Outfit, Figtree, Instrument Sans, Plus Jakarta Sans, Inter | Bricolage Grotesque, Unbounded, Bebas Neue (Latin), Anton, Fraunces, Playfair Display, DM Serif Display |
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
