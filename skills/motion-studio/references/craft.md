# Craft: rules that stop a video looking like AI slop

These apply to **every style**. Read this at S2 (storyboard) and S4 (build), and run through the checklist at the end before the preview render. Most "flat, generic" results break 3 or more of these.

## Words on screen
1. **≤ 6 words per headline, one idea per scene.** If a line needs more, split the scene or move the detail to VO.
2. **Exactly one accent word** per headline: the word that carries the meaning ("built in **layers**", not "**Built** in **Layers**"). Use bold + accent colour, never a second effect on top.
3. **Hierarchy has 3 levels at most:** eyebrow (small, mono or caps, dimmed) → headline → one supporting line or label. No paragraphs.
4. **Sync text to sound.** Each headline line appears on the word that says it (VO word times from `transcribe`). With music only, put lines on beats (`scripts/beats.py`). Text that appears at random times reads as decoration.
5. **Auto-fit, don't guess.** Fit headlines to their box once at load (`IsoKit.fit` or the same idea), and pad the line mask by about 0.12 em so descenders (g, y, p) don't clip.

## Pictures
6. **Every abstract idea gets a physical metaphor.** "Scalable" → columns that grow; "all-in-one" → a hero object with things orbiting it; "secure" → a box closing; "integrations" → plates connected by travelling pills; "layers" → an exploded stack. Write the metaphor into the storyboard next to each line.
7. **One object group per scene,** standing on something (a plate, tile, floor line or card). Floating clip-art reads as slop.
8. **Real assets beat drawn ones.** Use the real logo, screenshot or product cut-out when the brief has them. Draw objects only for ideas that have no picture.

## Rhythm
9. **Fast in → hold → cut.** Entrances 0.3–0.6 s, hold at least 1 s once everything is on screen, then a hard cut or a short transition on a beat. Don't animate out unless the style demands it.
10. **Change something at every cut:** background (dark → paper → solid), scale (wide ↔ close), or direction. **Never the same shot card twice in a row.**
11. **Background rhythm:** don't run the whole video on one background. Change the base colour every 3–4 scenes, and save the loudest colour for the one or two biggest moments.
12. **Ambient life during holds.** Give each hold a slow float, orbit, counter tick or pill travel, so the frame is never frozen for more than about 1.5 s. Keep it subtle: it's there to keep the frame alive, not to entertain.

## Frames that sell
13. **Frame 0 is the thumbnail:** headline line 1 and the main object are already visible at t = 0 (critical rule 8).
14. **The end card holds ≥ 2 s** with logo, CTA and URL fully visible and nothing moving except a small ambient loop.
15. **Make the brand obvious without logos everywhere:** use the brand colours as the solid scene and accent, and the logo only on the hero object and the end card.

## Components (pills, tags, cards, buttons)
Uneven borders, cramped labels and off-centre text are the fastest way to look cheap. The templates' classes (`.pill`, `.tag`, `.btn`, `.card`) follow these rules; keep them when you restyle.
16. **One scale for the whole video,** set as tokens in `:root` and written into `style.md`: `--r-sm`, `--r-card`, `--r-pill`, `--border-w`, `--pad-x`, `--pad-y`, `--pad-card`. Every component reads the tokens. No one-off radius or border in a scene.
17. **Labels never wrap and are never squeezed:** `white-space: nowrap`, padding from the tokens, no fixed width. If a label doesn't fit, shorten the words.
18. **Borders go inside the box:** `box-shadow: inset 0 0 0 var(--border-w) <colour>`, not `border` plus `overflow: hidden` (which clips the corners) and never `outline`. Border width 2–3 px at 1080p; under 2 px it flickers in video.
19. **Centre text by its letters, not its line box:** `line-height: 1` with `text-box: trim-both cap alphabetic` and equal top and bottom padding. Horizontal padding is 1.6–2× the vertical padding. Nested corners: inner radius = outer radius − the gap.
20. **Radius by size:** pills fully round, cards 2–3% of the frame's shorter side, small tags about half the card radius. Mixed radii on one screen need a reason.
21. **In 3D videos components stay HTML** (over the canvas or pinned to an object), unless a label must turn with an object (`three-d.md`, "Text and UI in 3D").

`scripts/visual_audit.py` measures 17–19 (`label_wrapped`, `text_off_centre_*`, `tight_padding`, `inconsistent_class`) and crops every component for you to look at.

## Kinetic type: numbers that work
Start from these, then tune by eye on a contact sheet. Times are at 30 fps.
| Move | Values |
|---|---|
| Word blur-in | blur 12 px → 0 and opacity 0 → 1 over 180–250 ms, `easeOutCubic`; words 60–90 ms apart |
| Per-letter stagger (Latin only) | 20–40 ms per letter, 12–24 px rise, whole word done within 400 ms |
| Slam-in | scale 2.4 → 1 in 150–200 ms (`expo.out`), then a squash of 4–6% for 2 frames. One per video, on the biggest word |
| In-place word swap | old word up and out in 120 ms, new word in from below in 180 ms, both inside a line mask |
| Tracking collapse into the logo | letter-spacing 0.4 em → 0 over 500–700 ms, `easeInOutCubic`, ending on a beat |
| Echo trail on a fast word | 2–3 copies behind it, 40 ms apart, opacity 40%, 25%, 12%, gone within 200 ms |
| Smear frames | stretch 120–160% along the move for 2–4 frames (about 0.1–0.15 s), only on moves faster than half the frame per second |
| Glow on text | a blurred copy behind the word (blur 8–24 px, opacity 60–80%), never a filter on the sharp text |
| Gradient fill | two stops from the palette, angle 90–120°, on the accent word only |

**Intensity** (pick one level per video, in `style.md`):
| Level | Feels | Moves allowed | Typical use |
|---|---|---|---|
| 1 restrained | calm, premium | fades, short rises, blur-in | luxury, finance, B2B |
| 2 clear | confident | + line masks, word swap | company and product promos |
| 3 lively | energetic | + stagger, one slam-in, tracking collapse | launches, SaaS, courses |
| 4 loud | fast, social | + echo trails, smears, beat cuts | social ads, events |
| 5 hyper | maximal | everything, cut on every beat | hype edits, short teasers |

**Readability pass, word by word.** For each headline, look at what is really behind every word at the moment it is on screen (the 3D object, a photo, a gradient). Under 4.5:1 there: move the word, add a solid backing or scrim, or add a 2–3 px dark outline with layered `text-shadow`. `npm run check` tests contrast on flat backgrounds only.

## Checklist before the preview render
- [ ] Every headline ≤ 6 words, one accent word, one idea
- [ ] Every scene's metaphor is written in `storyboard.md`
- [ ] Line reveals land on VO words or beats (list the times)
- [ ] No two consecutive scenes share a shot card or the same background + scale
- [ ] Frame 0 shows the hook; the end card holds ≥ 2 s
- [ ] Text ≥ 28 px at render size; contrast ≥ 4.5:1 (`npm run check`), and against the 3D or image really behind it
- [ ] Every pill, tag, card and button uses the tokens; `visual_audit.py` shows no component findings
- [ ] One intensity level, written in `style.md`
- [ ] Every number and claim comes from `facts.json`
