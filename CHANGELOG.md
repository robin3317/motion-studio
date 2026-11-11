# Changelog

## 0.3.0-beta (2026-11-11): 3D by default, cleaner components, tools for checking work
Steps two and three of the plan from the first outside test run: first see and measure quality, then raise it.

**Look**
- **Videos are 3D by default.** Unless you ask for 2D (or for a footage edit, or the Isometric Kinetic style), the skill builds on a real Three.js stage with sharp HTML text on top. It doesn't ask "2D or 3D?"; say "2D" to switch
- **New 3D starter, now the default template.** One 3D stage under three text scenes. The object moves between layout poses per scene and per format, so it never sits behind the text; it is already on screen at frame 0 and rests about 10° off-axis on the end card. Small parts orbit it in the middle scene and an HTML label stays pinned to it. 3D code lives in `lib/stage.js`, helpers in `lib/ms3d.js`. `new_project.py --template starter` gives the 2D starter
- **Clean pills, tags, cards and buttons.** Both starters have one set of component tokens (radius, border, padding) and component classes: labels never wrap, borders are drawn inside the box so they can't be clipped, and text is centred on its letters (`text-box` trim). New "Components" rules in `craft.md`. The Isometric Kinetic template reads the same radius and border tokens
- **Text and UI in 3D** (`three-d.md`): keep it in HTML, pin HTML to a 3D object (`pin()`), tilt an HTML card with CSS, or, when a label must turn with an object, `labelTexture()` with an inset stroke and centred text. Glow comes from `glowPlane()`; a bloom pass is off by default because it blurs text and brand colours
- **CPU profile for 3D.** `data-quality="cpu"` (set by `new_project.py` on hosts with 4 cores or fewer) lowers particle and geometry counts with the same look. A host without a GPU is no longer a reason to drop 3D
- **Every style preset has a 3D treatment and its own component tokens** (`styles/_index.md`)
- **Kinetic type numbers** in `craft.md`: blur-in, stagger, slam-in, word swap, tracking collapse, echo trail, smear frames, an intensity scale from 1 to 5, and a word-by-word readability pass
- **Fonts are chosen per video.** New `scripts/get_font.py` fetches a free font and its licence from npm into the composition, prints the `@font-face` rules and adds the font to `credits.json`; it handles extra scripts such as Bangla under the same family name. New font workflow and a brand-font → free-font table in `typography-i18n.md`. Both starters now ship a real font pair (Space Grotesk + Manrope) instead of naming a font that may not be installed
- **New `scripts/analyze_ref.py`: learn from a reference video.** Every frame of the first 3 seconds, an overview sheet per 15 seconds, cut times, sound onsets, loudness, and a recipe to fill in

**Checking work**
- **Projects can be resumed in a new chat.** New `PROGRESS.md` in every project (stage, next step, approvals, open feedback, a render to run again), a **feedback rules** table in `style.md` (one general rule per review round, append-only), and a "Resume first" section in SKILL.md. New critical rule 11
- **New `scripts/preview_sheet.py`: contact sheet of a scene or time range in seconds.** About 8 frames per second through HyperFrames' own stills, tiled with the time under each frame, into a new folder under `renders/checks/`. `--zoom ".pill"` follows one element at 3× density. To be run after every scene edit (workflow S4)
- **New `scripts/visual_audit.py`: measured visual QA.** At each scene's midpoint it runs HyperFrames' check and measures every pill, tag, card and button inside the real page: a wrapped label, overflowing text, text not centred in its box (measured on the letter shapes), a box cut by the frame, one class drawn in different sizes, and text over a busy part of a 3D canvas, which `check` can't see. Writes `audit.md`, a scene sheet and a numbered sheet of enlarged component crops. The composition is not touched; the measuring runs in a temporary copy
- **Independent review is now the default** before every final render (qa.md): a fresh reviewer gets the audit folder, not the producer's opinion
- **Release checks:** `tests/RELEASE_CHECKS.json` lists what was tested on which machine and what was not; `regression.py --record` writes its part. New `tests/acceptance.md` with 14 behaviour prompts (stay narrow, resume, no paid call or install without a yes, ignore instructions hidden in files)
- The regression now also runs the contact sheet and the audit for every template, and stops a 3D render part-way (once 60 frames are saved) to prove stop and resume on that machine. Stop and resume pass on Windows 11 and in the cloud sandbox
- **`render.py` fix for machines with more than 4 CPU cores.** With several workers, several segments are in work at once, so a call stopped early could save nothing. After such a call the next one uses one worker, which finishes segments one after another
- New `tests/test_visual_audit.py`. The regression also checks the default template, the font fetcher and the reference analysis
- Tested in a 2-core, no-GPU cloud sandbox: all 3 templates × 16:9 and 9:16 build, pass the checks, render and pass QA, and a stopped render resumes. `tests/RELEASE_CHECKS.json` lists every machine the regression ran on and what was not tested: macOS, a full project made with the 3D default, the acceptance prompts, bloom, GLB product models

## 0.2.1-beta (2026-11-10): reliability patch
Fixes from the first outside test run (a 3D promo made in a Claude Cowork cloud session: 2 CPU cores, no GPU, most sites blocked).
- **New `scripts/render.py`: renders that survive short time limits.** It renders in the foreground inside a `--budget`, stops cleanly before the limit and prints `RENDER_INCOMPLETE`; the same command then resumes from the frames already saved (HyperFrames segmented capture). It uses one worker on small machines, a longer start-up timeout for WebGL, and an installed Chrome when HyperFrames can't download its own. If a composition file changed between two calls it starts again from frame 0, so old and new frames never mix. It ends processes left by a killed render (only its own) and refuses to overwrite an output. New critical rule 10: never background a render
- **Found the real cause of the "45000 ms" render failure.** `hyperframes render --start/--end` leaves out `node_modules`, so GSAP and Three.js never load and the composition never becomes ready. It was not a slow-machine timeout. The skill no longer suggests range renders
- **Update notices now work in sandboxes that block the GitHub API.** `update_check.py` falls back to `raw.githubusercontent.com` (`plugin.json` on `main`). New `--notes` prints the changelog entries newer than the installed version; `--force` now says `CHECK_FAILED` and why instead of printing nothing
- **Audio mix checks itself.** `mix_audio.py` measures the real music-to-voice gap and deepens the duck until it is at least 17 dB (one test went from 13.8 dB to 17.6 dB). It masters to −1.5 dBTP, encodes to AAC, and turns the mix down if the MP4 would pass −1 dBTP
- **No more silent videos.** Every template carries a commented `<audio>` example with all required attributes; `audio.md` and the troubleshooting list explain it
- Scripts print UTF-8 on every console, so characters like "≥" no longer stop a script on Windows when its output is piped
- **Preflight reports the host's limits:** CPU cores, memory, GPU, an installed Chrome, and which sites are reachable (npm, Chrome download, GitHub API, raw GitHub, Hugging Face, the open web). It finds the HyperFrames skills bundled inside the CLI and every cached CLI version
- 3D starter uses `NeutralToneMapping` (exposure 0.95), as `three-d.md` already advised. Brand colours stay true
- Install rule reworded (critical rule 6): ask before changing the user's computer; in a throwaway cloud sandbox install what's needed and log it in `decisions.md`
- Checked: `npm run check` never rewrites `index.html`. It only writes reports under `.hyperframes/`
- Scene pattern made official: `<section class="scene">` blocks in one `index.html`; sub-compositions only for registry blocks
- HyperFrames pin 0.9.23 → **0.9.26**. Projects made with 0.9.23 keep working
- New tests: `tests/regression.py` (builds, checks, renders and QA-checks every template in 16:9 and 9:16 with a real audio mix) and `tests/test_update_check.py`
- Tested in a 2-core, no-GPU cloud sandbox: all 3 templates × 16:9 and 9:16 pass check, render and QA at −14.1 to −14.2 LUFS and −1.4 to −1.5 dBTP in the MP4 (also with HyperFrames 0.9.28). Renders stopped by their budget, and one killed outright, resumed and finished. The same regression passes on Windows 11; every render there finished in one call, so stopping and resuming is untested on Windows. Not tested on macOS

## 0.2.0-beta (2026-11-09): Isometric Kinetic style + craft rules
Aimed at the "flat, AI-slop" feedback from v0.1 testing.
- New style preset `isometric-kinetic` (8th): kinetic headlines with one accent word, cut-paper isometric objects, dark → paper → brand-solid background rhythm, optional HUD, hard cuts on beats. Brand-adaptable, so it works for normal promos, not only dev explainers
- New template `templates/isometric-kinetic` (`--template isometric-kinetic`): 6 scenes for 16:9, 9:16, 1:1 and 4:5, with one `BRAND` token object and one `C` copy object. Ships `lib/iso-kit.js` (isometric boxes, plates, tiles, orbit ring, face text, line-mask reveals, auto-fit, counter, typewriter, flip-clock, HUD, hard cuts), all seek-safe. Fonts: Outfit + JetBrains Mono via `@fontsource`
- New `references/craft.md`: anti-slop rules for every style (≤ 6 words + one accent word, a physical metaphor per scene, text synced to VO or beats, background rhythm, fast in → hold → cut, frame 0, checklist). Wired into storyboard (S2) and build (S4)
- 6 new shot cards: `iso-statement`, `iso-orbit-hero`, `iso-platform-row`, `exploded-stack`, `terminal-window`, `timeline-axis`
- Playbooks suggest Isometric Kinetic for tech/SaaS company promos, software products, apps and tech courses
- README: new **Styles** section listing all 8 presets and the 21 shot recipes
- docs: reference study of a 60 s SaaS launch film (techniques for a future continuous-camera "launch film" style)
- Tested: Optimizely company-promo remake (24 s, 16:9, 7 beat-cut scenes, music + 26 SFX). `hyperframes check` passes; QA passes at -14.0 LUFS / -1.0 dBTP. The template passes check in 16:9, 9:16, 1:1 and 4:5 with 0 lint warnings

## 0.1.0-beta (2026-11-09): first test release
First version for private testing and feedback.

**What's in it**
- Director skill for HyperFrames with two modes: **Autopilot** (brief → MP4) and **Step-by-step** (4 approval gates)
- 5 playbooks: company promo, product promo, release promo (teaser / announcement / countdown / launch day), brand promo, footage edit
- 7 style presets and 15 shot recipe cards (each with HyperFrames registry starting points)
- Three.js 3D: seek-safe 3D starter template (extruded SVG logos, multi-colour)
- Audio: 11 CC0 music tracks, 21 code-made CC0 sound effects, a catalogue, auto-ducking mixer (-14 LUFS / -1 dBTP), Openverse music search
- Footage tools: adaptive silence cuts, EDL apply with transcript re-timing, word-highlight captions
- Any-language text rules (Bengali, Arabic/RTL, CJK…), safe zones for 16:9 / 9:16 / 1:1 / 4:5
- 13 helper scripts (preflight, project scaffold, site capture, mix, beats, QA, update check…)
- Update notifications: a daily, silent-offline check offers Upgrade now / Remind me tomorrow / Snooze a week / Don't ask again, plus a `motion-studio-upgrade` skill

**Known limitations**
- Visual output is still basic and flat. Better typography, motion and 3D craft is the focus of the next version
- Tested end-to-end on Linux only (5 test videos). Windows and macOS need real-world testing
- Product background removal (rembg) is untested
- Skill triggering: 20/20 in a first automated test (tests/test-report.md)
