# Audio: music, SFX, mix

Order of work: **voiceover → music bed → SFX → mix → check.** The voice is king: if a sound competes with speech, the sound loses.

## 1. Licence rules (all audio)
Allowed:
- **User-owned or user-licensed** files (the user states they have rights)
- **CC0 / public domain**
- **Pixabay Content License** (free commercial use, no attribution required). Some tracks can still trigger platform Content ID claims; check the track page and prefer tracks without that warning.
- **CC BY** (commercial OK, **attribution required**): give the user the exact credit line to paste in the video description
- **AI-generated** with the user's own key, after paid-call approval, following that provider's terms

Not allowed for promos: **NC** (non-commercial), **ND** (no derivatives; syncing to video and editing counts as a derivative), unknown or unclear licences, and ripped commercial music.

Record each file in `credits.json`:
```json
{ "file": "audio/music/sunrise-drive.mp3", "type": "music", "title": "Sunrise Drive",
  "author": "Artist Name", "source": "https://…", "licence": "CC BY 4.0",
  "attribution": "\"Sunrise Drive\" by Artist Name (CC BY 4.0)", "ai_generated": false }
```

## 2. Music
**Where to look (in order):**
1. The user's own track
2. Bundled CC0 tracks in `<skill>/assets/audio/music/`: 11 tracks (corporate, playful, dance, acoustic, cinematic, tech, lo-fi, piano). Pick them by `mood`, `styles` and `playbooks` in `assets/audio/catalog.json`. BPM marked "estimated" should be checked with the beat times
3. Openverse search: `python "<skill>/scripts/find_music.py" search "upbeat corporate" --min 20 --max 120`, then `python "<skill>/scripts/find_music.py" get <id> --to audio/music --credits credits.json`. It only returns CC0, Public Domain Mark and CC BY, and writes the credits entry (with the CC BY attribution line). Mostly Freesound tracks.
4. Other free libraries by hand: Pixabay Music, Free Music Archive (filter CC0 / CC BY), Incompetech (CC BY)
5. AI music (paid: ask first): e.g. ElevenLabs Music, using the user's key

**Choosing a track**
- Match the playbook mood and the style preset's suggested BPM range.
- Structure: a clear intro, so the hook lands on a downbeat; an ending you can fade or that resolves at the CTA.
- Cut, don't stretch: edit at bar boundaries and fade the last 0.5–1.5 s. Never time-stretch more than ±5%.
- Sync key moments (logo hit, reveal, CTA) to beats or downbeats when it doesn't hurt readability. Get beat times with `python "<skill>/scripts/beats.py" audio/music/track.mp3`.

**Step-by-step:** offer 3 options as a table (title · source · licence · mood · BPM · why it fits), or accept the user's file.
**Autopilot:** choose one and log why in `decisions.md`.

## 3. Sound effects
**Where to look:** the user's library → bundled CC0 pack (`<skill>/assets/audio/sfx/procedural/`, 21 sounds; look them up in `assets/audio/catalog.json` by kind, use and style) → procedural (`python "<skill>/scripts/procedural_sfx.py" --kind whoosh --dur 0.6 --seed 3 --out audio/sfx/whoosh1.wav`) → Openverse/Freesound CC0 (`find_music.py search "<sound>" --sfx --licence cc0 --min 0 --max 10`) → AI SFX (paid: ask first, e.g. ElevenLabs Sound Effects).

**Placement rules**
- One sound per **meaningful** event: reveal, impact, transition, logo hit, UI click, counter finish. Not on every letter or every element.
- Group rapid events (a cascade of 6 cards) into one texture or 2–3 hits, not 6 identical clicks.
- Put the transient (the loud start) **on** the visual frame of impact. Most whooshes peak late, so start them early so the peak lands on the cut.
- Trim tails. Fade the last 30–80 ms to avoid clicks.
- Keep SFX out of the way of important VO words (names, numbers, CTA).
- Match the style: soft, short UI ticks for Minimal Luxury and Corporate Clean; punchier hits for Bold Kinetic and Cinematic 3D.

## 4. Mix targets
| Element | Target |
|---|---|
| Voiceover | The loudest, steady element. Lightly compressed, clean |
| Music under VO | **15–20 dB below the voice** while speech is playing |
| Music without VO | Main bed. Can be full level within the final target |
| SFX | Audible but never above the voice. Usually 6–12 dB below VO peaks |
| Ducking | Attack 50–150 ms, release 300–600 ms, starting just before the first word |
| Final master | **−14 LUFS integrated**, true peak **≤ −1 dBTP**, 48 kHz stereo AAC |

Mix with `python "<skill>/scripts/mix_audio.py" --plan audio/mix_plan.json --out audio/mix.wav`. The plan lists VO, music and SFX with start times and gains. The script ducks the music under the VO segments and normalizes the master. Then put **only the final mix** in the composition as one `<audio>` element covering the whole duration (copy it into `composition/assets/`). Alternatively, place the individual tracks and let the HyperFrames audio tools in `/media-use` do the mix. Pick one approach per project, never both.

Plan example (`audio/mix_plan.json`):
```json
{ "duration": 24,
  "vo": [{ "file": "audio/vo/vo.wav", "start": 0.3 }],
  "music": { "file": "audio/music/track.mp3", "fade_out": 1.5 },
  "sfx": [{ "file": "audio/sfx/whoosh.wav", "start": 2.9, "below_ref_db": 10 }],
  "music_under_vo_db": 18 }
```
The script reports `music_below_voice_db_during_speech`. If it's under 15, raise `music_under_vo_db` and mix again to a new file name.

## 5. Check
- Listen-proxy checks: measure integrated loudness and true peak (`qa.md`). Check that the music level during speech is at least 15 dB below the voice (the script reports it).
- Check every planned SFX cue is present and none is accidentally silent.
- Be honest: measured numbers aren't a human listen. Tell the user the mix was checked by measurement and suggest they listen once.
