# Reference study: ClickUp 4.0 launch film (v0.2 input, 2026-11-09)

The source is ClickUp's official 60 s launch film for ClickUp 4.0 (released around Dec 10, 2025): [ClickUp 4.0: The End of Work Sprawl](https://clickup.com/blog/clickup-4-0/). The video and frames are **not** included in this repo (copyright). We study *techniques*, not the look or assets.

## Measured
- 60.1 s, 3840×2160, 29.97 fps, with a voiceover and a music bed. The voiceover has 95 words (about 100 wpm), and every key word appears on screen.
- On-screen words land within about 0.0–0.3 s of the spoken word, often slightly ahead. Timings come from a word-level transcript (whisper.cpp base.en).
- Only about 5 hard cuts in 60 s (scene-detect hits at 24.1, 38.9, 40.4, 49.4 and 50.3 s). Every other change is a camera move, a morph or a word swap.
- Music is about 86 BPM (the beat tracker reports 172, double time). It fades out from 56.5 s while the end card holds.
- Loudness is -13.5 LUFS integrated with an LRA of 5 LU. True peak is +0.2 dBTP, which is over 0 (a small technical flaw).

## Structure (acts)
| Time | Act | VO (paraphrased) | Visual device |
|---|---|---|---|
| 0–7 s | Problem: types of sprawl | work / app / AI / context sprawl | One pink **line** that the camera follows. It tangles around app icons, makes arches carrying AI logos, and loops around chat bubbles. Labels ride on the line |
| 7–14.5 s | Cost | sprawl kills productivity, collaboration, visibility | The same line becomes a chart curve going up and down. Words sit at the peaks and troughs. The colour shifts pink → purple → blue |
| 14.5–17.5 s | Turn | time to kill sprawl | The line straightens, ends in a dot, and a typewriter with a cursor types the sentence |
| 17.5–24 s | Reveal | product name + positioning | The brand gradient appears for the first time. Words swap in place centre-screen (the key phrase in italics). Real UI is shown in 3D perspective with depth of field |
| 24–33 s | Promise + features | built to kill sprawl, everything you need | Curved text. A redaction bar censors "Sprawl", then a giant X. A prompt box, then floating feature cards, then a wall of cards |
| 33–38 s | Convergence made physical | converge into one workspace | Isometric gradient plate; cards stack onto it and collapse into the logo. Then a full UI screen under a title |
| 38–47 s | Benefits | maximum productivity, visibility… | UI screen in perspective with a callout. A slot-machine word list ("Maximum [productivity / visibility / collaboration / …]") with fading neighbours. A cursor bar morphs it into the next word |
| 47–56 s | New era | a new era of … | A donut chart with the text in its centre morphs into a gradient blob, then floating phones, then a white fade, then cards fanning out |
| 56–60 s | End card | brand | Logo + tagline; a version badge slides in; the CTA line. Holds about 4 s |

## What makes it work
1. **One through-line object** carries the whole 17 s problem act. It's the metaphor, the transition and the camera path at once.
2. **The VO is the typography**: the keywords are on screen, synced to the word, and swapped in place. Almost no text beyond the VO.
3. **Colour tells the story**: problem = cold, neutral light + an alarm-coloured line. The brand gradient is held back until the product is named.
4. **Continuous motion instead of cuts**: whip pans with motion blur, morphs, match moves.
5. **Type that acts out the word**: typewriter, redaction on "kill", curved text, slot-machine list, cursor-bar morph, italics for the key phrase.
6. **Real product UI** in perspective with depth of field, soft shadows and a gradient plate, plus an isometric stack for "converge".
7. **Shape morph chain** (donut → blob → phones) carries a spoken list.

## Weak spots (don't copy these)
- Many UI shots are unreadable texture: four feature cards go by in about 4 s, and the product is never shown working.
- Frame 0 is grey text fading in on white: a weak thumbnail (our critical rule 8).
- Tiny, low-contrast lines and grey fading list words (our contrast and 28 px rules would flag these).
- 38–47 s is words on blank white and sags.
- Jargon-heavy, repetitive copy.
- True peak over 0 dBTP.
- 16:9 only; the centred small text won't survive a 9:16 crop.

## Implications for motion-studio (v0.2 candidates, not started)
- **Light "launch film" style preset + template**: a through-line object, a continuous camera (one wide world layer panned by the clock), and the brand palette held back until the reveal.
- **VO keyword track**: on-screen words generated from the word-level transcript, swapped in place on the spoken word.
- **Shot cards**: through-line, word-swap, slot-list, redaction-kill, text-on-path, morph-chain, ui-perspective-dof.
- **Seek-safe motion blur and depth of field** (CSS/SVG blur driven by tween velocity or time).
- MorphSVG, DrawSVG, MotionPath, SplitText, Flip and CustomEase all ship in the npm `gsap` 3.15 package we already use (all GSAP plugins have been free since 3.13), so no new dependency is needed.
