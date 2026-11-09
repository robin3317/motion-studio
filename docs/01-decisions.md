# motion-studio — Foundational Decisions (Step 1)

Locked: 2026-11-08

## Reference rules
- **motion-video-director**: commercial single-user licence. It forbids redistributing its materials, including modified versions. **Ideas only**: no text, scripts or templates copied.
- **video-shotcraft**: Apache-2.0. Code may be reused with attribution in a NOTICE file. Its audio (Mixkit) has per-file licences, so **don't bundle** it. It's built on Remotion, so its code isn't directly portable to our engine.

## Platform
| Decision | Choice |
|---|---|
| Render engine | **HyperFrames** (HTML/CSS/JS scenes, rendered to MP4) |
| Hosts | **Claude Code** + **Claude Cowork/Desktop** (needs terminal and file access) |
| 3D | **Three.js in the browser**, rendered frame by frame inside HyperFrames scenes |
| Setup | **Guided install**: read-only preflight, then offer to install HyperFrames/FFmpeg/Node with the user's approval |
| Licence | **MIT** |
| Repo | https://github.com/robin3317 |

## Output
| Decision | Choice |
|---|---|
| Formats | 16:9 (1920×1080), 9:16 (1080×1920), 1:1 (1080×1080), 4:5 (1080×1350) |
| Default duration | **15–30 s** when not specified |
| Languages | **Any language**: detect or ask, choose suitable fonts (incl. Bangla, RTL, CJK) |
| Deliverable | **Final MP4 only** |

## Content sourcing
- **Company data**: fetch website text and take headless screenshots. The user confirms the extracted facts (guided mode).
- **Product images**: user uploads, the product website (user confirms rights), screenshots for software products.
- **AI images**: allowed **with user consent**, and labelled internally.
- **Voiceover**: optional, any source: none, the user's recording, or AI TTS (e.g. ElevenLabs).

## Audio
- **Music sources**: user's own files, bundled CC0 tracks, free-library search (licence shown), AI-generated (user's key).
- **SFX sources**: bundled CC0 pack, procedural (code-synthesized), user's own library, AI-generated (user's key).
- **Music rule**:
  - Guided mode: the user points to their own music OR picks from free licensed tracks the skill shows.
  - Autopilot: the skill auto-selects licensed music to match the brief and scenario.
- **Mix rule**: background music sits low and ducks under the voice, so the narration is always clearly intelligible.

## Modes
- **Autopilot**: hands-off. Stops **only for paid API calls**.
- **Step-by-step (guided)**: four approval gates:
  1. Brief + facts
  2. Script + storyboard
  3. Style frames (2–3 stills)
  4. Preview cut + audio (low-res) → final render
