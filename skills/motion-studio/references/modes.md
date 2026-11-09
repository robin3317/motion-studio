# Modes: Autopilot vs Step-by-step

## Choosing
- If the user named a mode, use it. Don't ask again.
- Otherwise ask **once**, in the same message as any missing essentials:
  > "Do you want **Autopilot** (I make every decision and deliver the MP4) or **Step-by-step** (you approve the brief, script, style frames and preview)?"
- If the user ignores the question but gives the essentials, use **Step-by-step**: it's the safer default when intent is unclear.

## Autopilot
**Goal:** one brief in, finished MP4 out.

Allowed stops (only these):
1. **The one essentials batch**, at the start, if something essential is missing and can't be found (subject, source, format, language). Also include image-rights confirmation here if product images will come from a website.
2. **Paid API calls.** State the service, what it will generate, the quantity and the approximate cost, then wait.

Everything else is decided by you:
- Playbook, style preset, structure, copy, shots, music track, SFX, pacing.
- Facts: use only facts taken directly from the user's input or the source website, each recorded in `facts.json` with its URL. Omit anything you can't source.
- Music: choose a licensed track that matches the playbook mood and pacing (see `audio.md`). Free sources first. Never call a paid music API without asking.
- Voiceover: if the user gave none and didn't ask for one, make the video **without** voiceover (music + SFX + on-screen text). Free local TTS is allowed only if the user asked for a voiceover.

Logging: at each point where Step-by-step would stop, append to `decisions.md`:
```
## G2 Script + storyboard (auto)
- Chose 5-beat structure (hook / problem / product / proof / CTA), 24 s
- Why: product promo, 9:16, social audience
```
Final message: link the MP4, list the key decisions in 3–6 bullets, give any attribution text that licences require (e.g. CC BY music credits for the video description), and say how to request changes.

## Step-by-step
Four gates. At each one, show the work **compactly**, give your recommendation, and wait.

| Gate | Show | User can |
|---|---|---|
| **G1 Brief + facts** | Goal, audience, format(s), duration, language, playbook, and a numbered list of facts with sources | Correct facts, change any brief field |
| **G2 Script + storyboard** | Beat table: time · on-screen text · visual/shot · VO line · SFX. Plus 3 music options (or their own) | Edit copy, reorder beats, pick music |
| **G3 Style frames** | Preset name + 2–3 rendered still frames (the hook, a middle beat, the CTA) | Pick a different preset, tweak colours, fonts, layout |
| **G4 Preview + audio** | Low-res preview MP4 with the full mix | Request timing, motion or mix changes |

Rules:
- Offer options with a recommendation; don't make the user design from scratch.
- Keep each gate to one message. Don't ask follow-ups between gates unless something is genuinely blocked.
- After G4 approval, render the finals and run QA without stopping again (except for paid calls).
- Changes requested at a gate: apply them, then re-show only what changed.

## Switching mid-project
- "Go autopilot", "decide the rest", "skip confirmations" → continue in Autopilot from the current stage and log decisions from here on.
- "Step by step", "let me check first" → stop at the next gate.
- Never redo approved work just because the mode changed.
