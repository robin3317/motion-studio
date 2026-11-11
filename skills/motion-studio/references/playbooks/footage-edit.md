# Playbook: Footage edit

**Purpose:** turn recorded video (talking head, interview, demo, event clip) into a polished piece with cuts, captions and motion graphics.
**Features:** silence & filler cuts · animated captions · overlays & lower thirds · zoom punch-ins & B-roll.

Never modify the original files. All edits produce new files in the project.

**This playbook is 2D:** create the project with `--template starter`. The footage is the picture; 3D is used only if the user asks for a 3D title or logo sting.

## 1. Intake
`data-gathering.md` §4: probe every clip, then get the transcript (the user's SRT/VTT, or `npx hyperframes transcribe <file> --language <code>`). **Read and fix the transcript**: names, terms, numbers. Speech recognition mishears names: in testing it wrote "Edmies" for a speaker's surname. Confirm a speaker's name with the user before it goes in a caption or lower third (in Step-by-step at G1; in Autopilot in the one essentials batch).

## 2. Cuts → `edl.json`
1. **Silence**: `python "<skill>/scripts/silence_cuts.py" assets/footage/a.mp4 --min 0.6 --pad 0.15 --out plan/edl.json`. The threshold is measured per recording (`--threshold auto`). It removes pauses longer than 0.6 s and keeps 0.15 s of padding on each side so speech doesn't sound clipped. If it reports 0 s removed, the clip is already tight: say so instead of forcing cuts.
2. **Fillers** (optional, ask in Step-by-step): remove transcript words matching a filler list for the language (English default: "um", "uh", "erm"). Show the list for confirmation in Step-by-step. In Autopilot, use only that safe default.
3. Never cut mid-word. Check cuts at word boundaries from the transcript.
4. Jump cuts on a talking head: alternate a subtle scale (100% ↔ 108%) across cuts to hide jumps, or cover them with B-roll.

Apply it: `python "<skill>/scripts/apply_edl.py" plan/edl.json --out assets/footage/cut-v1.mp4 --words plan/words.json`. This writes the cut video (with click-free joins) and the transcript re-timed to the new timeline. Use the cut video as **one** muted clip in the composition and take its audio from the mix, so audio and picture stay in sync. Delegate clip syntax to `/hyperframes`.

## 3. Captions
- Source: the corrected transcript, re-timed to the EDL.
- Styles (pick one): **clean subtitle** (bottom, 2 lines), **word highlight** (`caption-highlight` shot: current word coloured), **bold social** (1–3 words, large, centre-low).
- Placement: inside the safe zone (9:16: lower third, above the platform UI ≈ 72% height). Never cover faces.
- Language rules from `typography-i18n.md`. For complex scripts, highlight by **word**, never by character.

## 4. Overlays & lower thirds
- `lower-third` for names and titles the first time a speaker appears (3–4 s).
- Callouts and keyword pop-ups at emphasis points, max one every ~5 s.
- Logo bug (corner logo) only if requested.

## 5. Zooms & B-roll
- Punch-in zoom (100% → 110–118%) on emphasis words or a new point. Ease in 0.25–0.4 s. Hold or cut back. Not more than every ~4–6 s.
- B-roll: the user's clips, screenshots or images over the talking parts, with the original audio continuing underneath. Credit everything in `credits.json`.

## 6. Audio
Keep the speech primary (`audio.md`). Music only if requested, ducked well under the voice. Add SFX for pop-ups, sparingly. Light voice clean-up only (`voiceover.md`).

## Defaults
Format: keep the source aspect unless asked. For 16:9 source → 9:16, reframe on the speaker (crop window follows the face/subject) rather than letterboxing, unless the user prefers bars.
