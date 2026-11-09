# Changelog

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
