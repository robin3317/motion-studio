# Changelog

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
- 12 helper scripts (preflight, project scaffold, site capture, mix, beats, QA…)

**Known limitations**
- Visual output is still basic and flat. Better typography, motion and 3D craft is the focus of the next version
- Tested end-to-end on Linux only (5 test videos). Windows and macOS need real-world testing
- Product background removal (rembg) is untested
- Skill triggering: 20/20 in a first automated test (tests/test-report.md)
