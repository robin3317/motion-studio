# Changelog

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
