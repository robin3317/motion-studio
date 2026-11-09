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

## Checklist before the preview render
- [ ] Every headline ≤ 6 words, one accent word, one idea
- [ ] Every scene's metaphor is written in `storyboard.md`
- [ ] Line reveals land on VO words or beats (list the times)
- [ ] No two consecutive scenes share a shot card or the same background + scale
- [ ] Frame 0 shows the hook; the end card holds ≥ 2 s
- [ ] Text ≥ 28 px at render size; contrast ≥ 4.5:1 (`npm run check`)
- [ ] Every number and claim comes from `facts.json`
