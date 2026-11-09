# Step 5: Playbooks & references (done 2026-11-08)

Decisions:
- 7 style presets: Corporate Clean, Bold Kinetic, Cinematic 3D, Minimal Luxury, Playful Pop, Tech Neon, Editorial
- 5 playbooks: company, product, release (teaser/announcement/countdown/launch), brand, footage-edit
- Footage edit v1: captions, silence & filler cuts, overlays & lower thirds, zooms & B-roll
- Captions: user SRT if given, else `npx hyperframes transcribe` (local Whisper/Parakeet, free)
- 15 core shot cards

HyperFrames facts used (from the official docs):
- Determinism: no Date.now / rAF / timers, no unseeded Math.random, no mid-render fetches; time = frame/fps
- The runtime seeks Three.js. A custom FrameAdapter is only needed for custom hosts
- `npx hyperframes transcribe <file> --language <code>` (also imports SRT/VTT)
- Free local TTS (Kokoro) via /media-use; HeyGen voices with a key
- `npx hyperframes render --docker` for reproducible renders

Scripts referenced (to build in Step 6):
preflight.py, capture_site.mjs, cutout.py, beats.py, procedural_sfx.py, mix_audio.py, qa_check.py, silence_cuts.py, requirements.txt
