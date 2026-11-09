# Core workflow: stage by stage

Each stage lists inputs, actions, outputs and the gate. File names refer to the project folder layout in SKILL.md.

## S1: Brief & data
**Actions**
1. Write `brief.md`: goal (what the viewer should know/feel/do), audience, platform, format(s), duration (default 15–30 s), language, mode, playbook, and the CTA.
2. Gather material → `data-gathering.md`. Put files in `assets/`.
3. Write `facts.json`: one entry per fact. `{ "id": "f3", "text": "Serving 120+ clients", "source": "https://acme.com/about", "type": "stat" }`
4. Note brand basics in `style.md` (draft): logo file, brand colours (hex), brand fonts if known.
5. Start `credits.json` for every asset collected so far.

**Gate G1: Brief + facts.** Step-by-step: show the brief summary and the numbered facts. Autopilot: log to `decisions.md`.

## S2: Script & storyboard
**Actions**
1. Pick the beat structure from the playbook for the chosen duration.
2. Write `script.md`: per beat, the on-screen text (short: ≤ 7 words per line, ≤ 2 lines on screen), VO line if any, and its purpose.
3. Reading time check: each text block must stay on screen ≥ **0.4 s per word + 0.5 s** (minimum 1.2 s). If it doesn't fit, cut words, not time.
4. Choose a shot recipe for each beat from `shots/`. Mix scales and motions; don't repeat the same card back to back.
5. Write `storyboard.json`:
```json
{ "fps": 30, "duration": 24, "formats": ["9:16"],
  "scenes": [
    { "id": "s1", "start": 0, "duration": 2.5, "shot": "kinetic-title",
      "text": ["Stop guessing.", "Start knowing."], "vo": null,
      "assets": [], "sfx": [{ "t": 0.1, "kind": "whoosh" }], "transition_out": "shape-wipe" }
  ] }
```
6. Music: Step-by-step → offer 3 licensed tracks (title, source, licence, mood, BPM) or the user's own. Autopilot → choose one. See `audio.md`.
7. If there's a voiceover, get or generate it **now** (`voiceover.md`) and retime the storyboard to its real word timings.
8. Apply `craft.md`: ≤ 6 words and one accent word per headline, and write a physical metaphor next to every scene. Note when each headline line appears (the VO word, or the beat if there's no VO).

**Gate G2: Script + storyboard.** Show it as a beat table.

## S3: Style direction
1. Pick a preset from `styles/` (the playbook suggests defaults). Adapt it: replace the preset's accent colours with the brand palette, keep the preset's motion rules.
2. Fonts → `typography-i18n.md`. Download the font files into `assets/fonts/` (no fetching at render time).
3. Create the project if it doesn't exist yet: `python "<skill>/scripts/new_project.py" --name <name> --format <fmt> --duration <s> --lang <code> [--template three-starter|isometric-kinetic] --install` (ask before `--install`). The `isometric-kinetic` template (style `isometric-kinetic.md`) ships a 6-scene layout for all formats: edit its `C` (copy) and `BRAND` (tokens) objects first, then re-time the scenes `T` to the music beats or VO. For extra formats: `--composition-only --format <fmt>`.
4. Build only the frames needed and render **2–3 stills**: the hook, one middle beat, the CTA (`npx hyperframes snapshot --at 0,8,22` inside the composition). To check the safe zones, temporarily add `class="show-guides"` to `<html>`, and remove it before rendering finals.
5. Finalize `style.md`: palette (hex + role), fonts (role, weight, size scale), motion feel (easing, typical durations), grain/texture, transition type.

**Gate G3: Style frames.** Show the stills and name the preset.

## S4: Build
1. Work in the project's `composition/` folder (from `templates/starter`, `templates/three-starter` or `templates/isometric-kinetic`). Search the `/hyperframes-registry` skill for a ready-made block before hand-building a shot (each shot card lists registry starting points). Delegate syntax to the `/hyperframes` skill.
2. Build scene by scene from `storyboard.json`. One scene = one timed group. Keep scene timing in data, not hard-coded across files.
3. **Frame 0 is the thumbnail** on social players: the hook text or key image must already be visible at 0 s, not fading in from an empty frame.
4. Determinism (required by HyperFrames): no `Date.now()`, no `requestAnimationFrame` loops, no unseeded `Math.random()`, no network fetches during the render. All assets are local and preloaded.
5. 3D scenes → `three-d.md` (start from `templates/three-starter`).
6. Run `npm run check` (lint, runtime, layout, motion, contrast) after each major scene and fix the errors.
7. Before the preview render, go through the `craft.md` checklist. Fix the misses: they're what make a video look generic.

## S5: Audio
1. Lay down the voiceover first (if any), then the music bed, then SFX → `audio.md`.
2. SFX go on **visual events** (impacts, reveals, transitions, UI clicks), not on every element. Leave space around important VO words.
3. Duck the music under the voice. Final loudness and peak targets are in `audio.md`.
4. Record every audio file in `credits.json`.

## S6: Preview cut
1. Render a quick preview with the full mix: `npx hyperframes render -q draft -o ../renders/previews/<name>-preview-vN.mp4`.
2. Self-check before showing it: run the `qa.md` checklist on the preview (contact sheet + audio levels).
3. **Gate G4: Preview + audio.** Step-by-step: share the preview and list what you checked. Autopilot: fix the issues you found and continue.

## S7: Final render & QA
1. Render each requested format at full resolution: `npx hyperframes render -q delivery -o ../renders/<project>-<format>-vN.mp4` (never overwrite). For variants of one composition (e.g. countdown days), use `--variables` or `--batch`.
2. Run the full `qa.md` checklist on each final. Fix and re-render if anything fails.
3. Deliver: the MP4 path(s), a short summary, and any required attribution text (e.g. CC BY music) for the user to paste in the video description.

## Revisions after delivery
- Change only what was asked. Keep approved scenes, audio and style.
- Render a new version number. Keep the previous final.
