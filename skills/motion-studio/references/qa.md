# QA: preview and final checks

Run on the preview (S6) and on every final (S7). Fix failures and re-render. Report honestly what was **measured** and what was **visually inspected**.

## 0. HyperFrames check
Inside the composition: `npm run check`. It covers lint, runtime errors, layout, motion and contrast. Fix every error. Read the warnings (e.g. `first_frame_empty`).
- `line_unread` warnings on **speech-synced captions** are expected: captions follow the speaker's pace. Keep caption groups to 5 words or fewer and ignore those warnings. Fix them for any other text.
- The check can't see inside WebGL/3D canvases, so overlaps there only show up in stills.
- `npx hyperframes snapshot --at <times>` writes full-size frames plus a contact sheet. The contact sheet is compressed and small details can mislead: zoom into the full-size frame before you call something a bug.
- The check is read-only for your files. It writes only its reports, under `.hyperframes/` in the composition (tested with HyperFrames 0.9.23, 0.9.26 and 0.9.28, including runs that reported errors). If `index.html` changed, something else changed it.
- On a machine without a GPU, a 3D scene adds `console_warning … GPU stall due to ReadPixels` lines. They describe the host, not the composition: ignore them.
- Don't check a time range with `npx hyperframes render --start/--end`: that path leaves out `node_modules`, so these templates fail with "Composition setup did not finish within 45000ms". Use `snapshot --at` for stills and `scripts/render.py` for video.

## 1. Technical (measured)
Run `python "<skill>/scripts/qa_check.py" renders/<file>.mp4 --expect-format 9:16 --expect-duration 24`. It checks:
- Resolution and aspect match the requested format
- fps (default 30) and duration (±0.1 s of the plan)
- Codec: H.264 video, AAC audio, yuv420p (plays everywhere)
- Loudness: integrated ≈ −14 LUFS (±1), true peak ≤ −1 dBTP. Both are measured on the MP4's AAC track, which peaks higher than the WAV it was made from. If the peak fails, mix again with `mix_audio.py` (it masters to −1.5 dBTP and checks the AAC peak)
- No silent gaps where audio is expected. No digital clipping

Manual equivalents:
```
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt:format=duration -of json file.mp4
ffmpeg -i file.mp4 -af ebur128=peak=true -f null -
```

## 2. Visual (inspect stills)
Make a contact sheet: `ffmpeg -i file.mp4 -vf "fps=2,scale=480:-1,tile=6x5" -frames:v 1 renders/previews/sheet.png`, then **look at it**. Also extract full-size stills at each scene's midpoint.
- [ ] Every text block is readable, inside the safe zone, and on screen long enough (≥ 0.4 s/word + 0.5 s)
- [ ] No overlaps, clipping, cut-off words or stray elements
- [ ] Complex scripts render correctly (no tofu boxes, conjuncts intact)
- [ ] Brand colours, logo and fonts are correct. The logo isn't stretched
- [ ] The product looks like the real product (no AI image used without consent)
- [ ] Transitions are clean: no flash frames, no blank frames at the start or end
- [ ] The CTA and closing line are on screen for ≥ 2 s at the end

## 3. Content
- [ ] Every claim on screen or in the VO exists in `facts.json`, with its source
- [ ] Names, numbers, dates, time zones, prices and URLs are spelled exactly right
- [ ] Language and tone match the brief

## 4. Audio
- [ ] The voice is intelligible throughout. The music is ≥ 15 dB below the voice during speech
- [ ] Every planned SFX cue is present and lands on its visual event
- [ ] No abrupt music ending. No clicks at cuts

## 5. Rights
- [ ] Every asset is in `credits.json` with a licence that allows this use
- [ ] Attribution text is ready for the user if any licence needs it (CC BY)

## Independent review (recommended)
If the host supports subagents, give a fresh subagent the final MP4's contact sheet, stills, `brief.md`, `facts.json` and this checklist, and ask it to find problems. Fix real issues before delivering. The producer shouldn't be the only reviewer.
