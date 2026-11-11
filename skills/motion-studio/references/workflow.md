# Core workflow: stage by stage

Each stage lists inputs, actions, outputs and the gate. File names refer to the project folder layout in SKILL.md.

## Keeping the project resumable (every stage)
Chats get long and end. The files must carry the project, not the conversation.
- **`PROGRESS.md`**: rewrite it (short, overwrite) after every stage, every user decision and before any long render: stage, current version, the one next step, approvals with dates, open feedback, a render command to run again, the last check folder.
- **`style.md`**: real values only (hex, px, ms, easing names, dB). When an approved value changes, change it here and note why in `decisions.md`.
- **Feedback rules** (in `style.md`, append-only): after every review round write the *general* rule behind the fix. "Make the CTA bigger" becomes "CTA text ≥ 56 px at 9:16". Every new or changed scene must pass every rule.
- **`decisions.md`**: append what was decided and why. Never rewrite history.
- Starting in an existing project: follow "Resume first" in SKILL.md before anything else.

## S1: Brief & data
**Actions**
1. Write `brief.md`: goal (what the viewer should know/feel/do), audience, platform, format(s), duration (default 15–30 s), language, mode, playbook, and the CTA.
2. Gather material → `data-gathering.md`. Put files in `assets/`.
3. Write `facts.json`: one entry per fact. `{ "id": "f3", "text": "Serving 120+ clients", "source": "https://acme.com/about", "type": "stat" }`
4. Note brand basics in `style.md` (draft): logo file, brand colours (hex), brand fonts if known.
5. **If the user gave a reference video** ("make it like this"): `python "<skill>/scripts/analyze_ref.py" <file>`. It writes every frame of the first 3 s, an overview sheet per 15 s, the cut times, the sound onsets and a `recipe.md` to fill in. Open the sheets, fill the recipe, and use it at S2 (pace, shot lengths) and S3 (type, colour, depth). Learn from a reference; never copy its footage, music, logo or wording. After the first version, run the script on our render too and list the gaps.
6. Start `credits.json` for every asset collected so far.

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
2. Fonts → `typography-i18n.md`, "Choosing fonts". Choose a pair for this brand and fetch it with `scripts/get_font.py` (no fetching at render time). Don't keep the template's default pair without a reason.
3. Create the project if it doesn't exist yet: `python "<skill>/scripts/new_project.py" --name <name> --format <fmt> --duration <s> --lang <code> --install` (ask before `--install` on the user's machine). This creates the **3D starter** (`three-d.md`), the default. Add `--template starter` for a 2D video or a footage edit, or `--template isometric-kinetic` for that style; use them only when the user asked for 2D or for that style. The `isometric-kinetic` template (style `isometric-kinetic.md`) ships a 6-scene layout for all formats: edit its `C` (copy) and `BRAND` (tokens) objects first, then re-time the scenes `T` to the music beats or VO. For extra formats: `--composition-only --format <fmt>`.
4. Build only the frames needed and render **2–3 stills**: the hook, one middle beat, the CTA (`npx hyperframes snapshot --at 0,8,22` inside the composition). To check the safe zones, temporarily add `class="show-guides"` to `<html>`, and remove it before rendering finals. If the snapshot says Chrome was not found, set `HYPERFRAMES_BROWSER_PATH` to the installed Chrome that preflight prints.
5. Finalize `style.md`: 2D or 3D and why, palette (hex + role), fonts (role, weight, size scale), the component tokens (`--r-sm`, `--r-card`, `--r-pill`, `--border-w`, paddings; start from the preset's row in `styles/_index.md`), the intensity level (`craft.md`), motion feel (easing, typical durations), grain/texture, transition type.

**Gate G3: Style frames.** Show the stills and name the preset.

## S4: Build
1. Work in the project's `composition/` folder (from `templates/three-starter` by default; `templates/starter` or `templates/isometric-kinetic` for 2D). Search the `/hyperframes-registry` skill for a ready-made block before hand-building a shot (each shot card lists registry starting points). Delegate syntax to the `/hyperframes` skill.
2. Build scene by scene from `storyboard.json`. One scene = one timed group. Keep scene timing in data, not hard-coded across files.
   - **Scene pattern:** every scene is a `<section class="scene">` inside the one `index.html`, shown and hidden by the single master timeline, as the three templates do. This is the pattern the skill is tested with. Use a HyperFrames sub-composition (`compositions/*.html` mounted with `data-composition-src`) only when a registry block installs as one, and leave that block as it came.
3. **Frame 0 is the thumbnail** on social players: the hook text or key image must already be visible at 0 s, not fading in from an empty frame.
4. Determinism (required by HyperFrames): no `Date.now()`, no `requestAnimationFrame` loops, no unseeded `Math.random()`, no network fetches during the render. All assets are local and preloaded.
5. 3D → `three-d.md`. Text scenes and the timeline are in `index.html`; the 3D stage is in `lib/stage.js`. For each scene set a text zone and a pose for the object (`POSES`), so the object never sits behind text. Pills, tags, cards and buttons stay HTML and use the component classes (`craft.md`, "Components").
6. **After every scene edit, look at the whole move:** `python "<skill>/scripts/preview_sheet.py" --scene s2` (or `--from 3 --to 6`). It captures the range at 8 frames per second into labelled contact sheets in a few seconds. Open every sheet and check framing, overlaps, clipped or wrapped text, borders and easing. Fix, run it again, repeat until clean, then move to the next scene. A single still misses what happens between stills. For one element up close: add `--zoom ".btn"`.
7. Run `npm run check` (lint, runtime, layout, motion, contrast) after each major scene and fix the errors. The check never edits your files: it only writes its reports under `.hyperframes/`.
8. Before the preview render, go through the `craft.md` checklist. Fix the misses: they're what make a video look generic.

## S5: Audio
1. Lay down the voiceover first (if any), then the music bed, then SFX → `audio.md`.
2. SFX go on **visual events** (impacts, reveals, transitions, UI clicks), not on every element. Leave space around important VO words.
3. Duck the music under the voice. Final loudness and peak targets are in `audio.md`.
4. Put the finished mix in the composition: copy it to `composition/assets/mix.wav` and uncomment the template's `<audio>` example. Without that element the render is silent.
5. Record every audio file in `credits.json`.

## Rendering (S6 and S7)
Render with the script, from the project folder, **in the foreground**:
```
python "<skill>/scripts/render.py" --out renders/<file>.mp4 --quality draft|delivery --budget <seconds>
```
- **Never background a render** (`&`, `nohup`, a detached task) and never start a second one while one runs. A backgrounded render is killed when the call ends and leaves Chrome processes behind.
- `--budget` is the longest that one call may run. Give the call your shell tool's longest time limit and set `--budget` to that limit minus 60 s (a 10-minute limit → `--budget 540`). The default, 100, fits a 2-minute limit.
- `RENDER_DONE` → finished. `RENDER_INCOMPLETE` (exit code 3) → run the **same** command again: it resumes from the frames already saved and tells you how many calls are left. `RENDER_FAILED` → read the log lines it prints and fix the composition.
- Don't edit the composition between the calls of one render. If any of its files changed, the next call notices and starts again from frame 0, so old and new frames never mix.
- It handles the slow-host details itself: one worker on small machines, a longer start-up timeout for WebGL, an installed Chrome when HyperFrames can't download its own.
- Don't use `npx hyperframes render --start/--end`. That path leaves out `node_modules`, so compositions made from these templates fail after 45 s. Several formats or countdown variants: one `render.py` call per composition, one after another. `--variables` goes after `--`, e.g. `-- --variables '{"daysLeft":3}'`. Only `--batch` is called on `npx hyperframes render` directly.

## S6: Preview cut
1. Audit before rendering: make sure `storyboard.json` lists every scene (id, start, duration), then run `python "<skill>/scripts/visual_audit.py"`. Fix every error and warning, open its sheets, and judge the "review" items by eye (`qa.md` §2).
2. Render a quick preview with the full mix: `python "<skill>/scripts/render.py" --out renders/previews/<name>-preview-vN.mp4 --quality draft`.
3. Self-check before showing it: run the `qa.md` checklist on the preview (audio levels, content, rights).
4. **Gate G4: Preview + audio.** Step-by-step: share the preview and list what you checked. Autopilot: fix the issues you found and continue.

## S7: Final render & QA
1. Before rendering: run `visual_audit.py` once more on the final composition and do the independent review (`qa.md`, last section). Rendering first and reviewing after wastes the render.
2. Render each requested format at full resolution: `python "<skill>/scripts/render.py" --composition <composition folder> --out renders/<project>-<format>-vN.mp4 --quality delivery` (it refuses to overwrite). For variants of one composition (e.g. countdown days), pass `-- --variables '{…}'` with a different `--out` each time, or call `npx hyperframes render --batch` directly.
3. Run the full `qa.md` checklist on each final. Fix and re-render if anything fails.
4. Deliver: the MP4 path(s), a short summary, and any required attribution text (e.g. CC BY music) for the user to paste in the video description.

## Revisions after delivery
- Change only what was asked. Keep approved scenes, audio and style.
- Check the changed range with `preview_sheet.py` before rendering, and compare it with the sheet of the previous version if one exists.
- Write the general rule behind the request into the feedback rules in `style.md`, and check the rest of the video against it.
- Render a new version number. Keep the previous final. Update `PROGRESS.md`.
