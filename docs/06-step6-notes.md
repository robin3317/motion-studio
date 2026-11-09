# Step 6: Engine (scripts + templates) (done 2026-11-08)

## Built
- scripts/: _common.py, preflight.py, new_project.py, capture_site.mjs, cutout.py, beats.py,
  procedural_sfx.py, mix_audio.py, silence_cuts.py, qa_check.py, requirements.txt (numpy only)
- templates/starter: 3-scene GSAP composition with design tokens, per-format safe zones, guides toggle
- templates/three-starter: seek-safe Three.js extruded-SVG logo reveal (RoomEnvironment, seeded particles, HTML tagline)

## Tested (cloud sandbox, Linux, HyperFrames 0.9.23)
- new_project.py: 9:16 + 16:9, refuses overwrites, --composition-only works
- `hyperframes check`: both templates pass
- Render: starter 1080x1920 9 s, three-starter 1920x1080 5 s; frames inspected visually
- procedural_sfx --pack: 11 sounds; beats.py: 124 BPM test track → 123.6 BPM, beat grid within ~20 ms
- mix_audio.py: music 16.4 dB under voice during speech, -14.0 LUFS, -1.0 dBTP
- silence_cuts.py: correct EDL incl. extra cut ranges; qa_check.py: all checks on silent + muxed renders
- capture_site.mjs: exact 1920x1080 / 1080x1920 / 1080x1350 shots, cookie banner hidden, brand.json colours/fonts/logo
- Not tested: native Windows/macOS runs, rembg (optional), live websites

## Learned from HyperFrames (applied)
- CDN scripts fail where the network is locked down → GSAP/Three vendored via npm (node_modules + importmap)
- `check` flags nested timeline sections → scenes toggled with GSAP autoAlpha instead
- `first_frame_empty` warning → rule: frame 0 is the thumbnail
- HyperFrames asks agents not to install its skills → setup gives the user the command
- Registry has ready blocks (extruded-logo, product-turntable, count-up, lt-*, caption-*) → added to shot cards
- `--variables` / `--batch` for countdown variants; HYPERFRAMES_BROWSER_PATH when the Chrome download is blocked
