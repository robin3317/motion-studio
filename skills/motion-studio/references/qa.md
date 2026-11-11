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

## 2. Visual (measure, then look)
Run `python "<skill>/scripts/visual_audit.py"` from the project folder (fill `storyboard.json` first: it samples each scene's midpoint and the closing frame). It writes a new folder `renders/checks/audit-vN/` with `audit.md`, one labelled contact sheet of the scenes, and a numbered sheet of every pill, tag, card and button enlarged.
- **Errors and warnings** come from HyperFrames' check (overflow, overlap, contrast, lint) and from the component measurements: `label_wrapped`, `text_overflow`, `text_off_centre_vertical`, `cut_by_frame`, `text_over_3d`. Fix them all.
- **Review items** (`text_off_centre_horizontal`, `tight_padding`, `inconsistent_class`, light `text_over_3d`) are candidates. Open the crop and decide.
- **Then look at both sheets yourself.** The measurements can't judge whether a border, a radius or the spacing looks right. If a component isn't measured, add its selector: `--selectors ".stat,.chip"`, or mark it with `data-audit`.
- Need a closer look? `python "<skill>/scripts/preview_sheet.py" --scene s3 --zoom ".card"` crops one element at 3× density across the scene. For a whole move: the same command without `--zoom`.
- After the render, a quick sheet of the MP4 itself: `python "<skill>/scripts/qa_check.py" <file> --sheet renders/checks/final-sheet.png`.

Check, on the sheets:
- [ ] Every text block is readable, inside the safe zone, and on screen long enough (≥ 0.4 s/word + 0.5 s)
- [ ] No overlaps, clipping, cut-off words or stray elements
- [ ] Complex scripts render correctly (no tofu boxes, conjuncts intact)
- [ ] Brand colours, logo and fonts are correct. The logo isn't stretched
- [ ] The product looks like the real product (no AI image used without consent)
- [ ] Transitions are clean: no flash frames, no blank frames at the start or end
- [ ] The CTA and closing line are on screen for ≥ 2 s at the end
- [ ] Every rule in `style.md` → Feedback rules holds in every scene, not only the one that was fixed

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

## Independent review (before every final render)
The producer shouldn't be the only reviewer: you already believe the video is fine. If the host can start a subagent, do this before the final render, every time:
1. Give a fresh subagent only the evidence, not your opinion: the newest `renders/checks/audit-vN/` folder (`audit.md` and both sheets), `brief.md`, `facts.json`, the feedback rules from `style.md`, and this checklist.
2. Ask it to list concrete problems with the time and the element, and to say what it could not judge.
3. Fix the real ones, run `visual_audit.py` again, then render.
No subagents on this host: do the same pass yourself from the sheets alone, in a separate step after a break in the work, and say in the delivery message that the review was not independent.
