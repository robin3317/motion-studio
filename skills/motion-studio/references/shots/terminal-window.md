# terminal-window
**Use for:** dev tools, APIs, CLIs, "install in one line", a code or config snippet, a chatbot prompt. Also works for a search bar or prompt box in non-dev videos.  **Length:** 2.5–4 s
**Needs:** the real command or snippet (≤ 3 short lines) and its real output (1–2 lines), from the product's docs. Never invent commands.
**Beats**
- 0.0–0.4: the window (rounded card, three dots, mono title) scales 0.96 → 1 and fades in on dark; on paper it gets a hard offset shadow
- 0.3 → : the command types in (`IsoKit.type`, 18–28 chars/s) with a block caret
- end of typing + 0.2: "enter": output lines appear at once; success text in the accent colour (`✓ deployed`)
- Optional: a short headline beside or above it with the accent word on the outcome
- Hold ≥ 1 s on the output
**Build:** HTML card + mono text; `IsoKit.type(tl, el, text, t, cps)` is seek-safe (it sets the text from the clock, no intervals).
**SFX:** soft key ticks during typing (one texture, not one click per key), a confirm blip on output.
**i18n:** keep commands in Latin; translate only the surrounding headline.
**Avoid:** fake or unrunnable commands; long lines that need to scroll; text below 28 px (it's often read on phones).
**Registry starting points:** search the registry for terminal / code-block / typewriter blocks and restyle. Check with the `/hyperframes-registry` skill.
