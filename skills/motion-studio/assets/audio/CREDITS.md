# Bundled audio: credits & licences

Everything in `assets/audio/` may be used in commercial and non-commercial videos **and** redistributed with this skill.
Before adding a file here, it must be CC0 / public domain or made by this project. "Free to use" licences that forbid redistributing the files themselves (e.g. the Pixabay Content License) are **not** allowed in this folder. Those tracks can still be used inside a user's project (see `references/audio.md`).

`catalog.json` lists every file with its kind, duration, suggested use, matching style presets and licence. Search it before picking a sound.

## Sound effects: `sfx/procedural/` (21 files)
- **Source:** synthesized from code by `scripts/procedural_sfx.py` (fixed seeds; regenerate any file with the command below).
- **Author:** motion-studio contributors.
- **Licence:** CC0 1.0 Universal (public domain dedication). No attribution required.
- **Format:** 48 kHz, 16-bit, stereo WAV, peak −3 dBFS, dense sounds capped at −16 dBFS RMS.
- These are designed sounds, not realistic Foley. Audition them in context. Realistic Foley (footsteps, doors, paper) should come from the user's library or a CC0 source.

| File | Command |
|---|---|
| whoosh-short / -medium / -long | `--kind whoosh --dur 0.45/0.7/1.1 --seed 1/2/3` |
| swish-1 / -2 | `--kind swish --dur 0.3/0.4 --seed 4/5` |
| riser-1-5s / -3s | `--kind riser --dur 1.5/3.0 --seed 6/7` |
| hit-punch / -long | `--kind hit --dur 0.5/0.9 --seed 8/9` |
| boom-short / -deep | `--kind boom --dur 1.2/2.2 --seed 10/11` |
| click-ui, tick-soft | `--kind click --dur 0.05 --seed 12`, `--kind tick --dur 0.04 --seed 13` |
| pop-high / -low | `--kind pop --dur 0.12/0.2 --seed 14/15` |
| shimmer-short / -long | `--kind shimmer --dur 1.0/2.0 --seed 16/17` |
| glitch-short / -long | `--kind glitch --dur 0.25/0.5 --seed 18/19` |
| typing-1s / -2s | `--kind typing --dur 1.0/2.0 --seed 20/21` |

## Music: `music/` (11 tracks)
- **Licence:** all CC0 1.0 Universal (public domain dedication), as marked on each Freesound page and in the Openverse catalogue (checked 2026-11-09). No attribution required. Crediting the creators is still appreciated.
- **Files:** Freesound "HQ preview" MP3s (128 kbps), which anyone can download. Original uploads can be downloaded from each page with a free Freesound account if higher quality is needed.
- **Loudness varies** (−28 to −11 LUFS) because these are the creators' own masters. `scripts/mix_audio.py` normalizes the final mix.
- BPM and mood for each file are in `catalog.json`.

| File | Title | Author | Source | Mood |
|---|---|---|---|---|
| `corporate-intro_bertsz.mp3` | Corporate company introduction video | Bertsz | [freesound.org/…/524308](https://freesound.org/people/Bertsz/sounds/524308) | clean, light piano, quiet |
| `unpretentious-reveal_drakensson.mp3` | Unpretentious Reveal (no drums) | Drakensson | [freesound.org/…/529381](https://freesound.org/people/Drakensson/sounds/529381) | synth, business, building reveal |
| `full-of-energy_code-box.mp3` | Full of Energy | code_box | [freesound.org/…/520192](https://freesound.org/people/code_box/sounds/520192) | bright, glockenspiel, energetic |
| `fun-dancetrack_evanjones4.mp3` | fun dancetrack | evanjones4 | [freesound.org/…/320089](https://freesound.org/people/evanjones4/sounds/320089) | dance, acid bass, upbeat |
| `tropicorp-advertisement_code-box.mp3` | Tropicorp Advertisement | code_box | [freesound.org/…/561190](https://freesound.org/people/code_box/sounds/561190) | light, flute, claps, ad-style |
| `upbeat-acoustic-guitar-orchestra_guitarman213.mp3` | Upbeat Acoustic Guitar With Orchestra | guitarman213 | [freesound.org/…/709034](https://freesound.org/people/guitarman213/sounds/709034) | warm, motivational, acoustic |
| `cinematic-dramatic-buildup_burghrecords.mp3` | Cinematic Dramatic Buildup | BurghRecords | [freesound.org/…/456102](https://freesound.org/people/BurghRecords/sounds/456102) | dramatic build-up, climax |
| `electronic-cinematic_szegvari.mp3` | Electronic Cinematic Music | szegvari | [freesound.org/…/579825](https://freesound.org/people/szegvari/sounds/579825) | dark electronic, action |
| `retro-synth-pop-dance_szegvari.mp3` | Retro Vintage Synth Pop Dance Cinematic Music | szegvari | [freesound.org/…/614197](https://freesound.org/people/szegvari/sounds/614197) | retro synth, happy, dance |
| `hiphop-chill-calm_klaudux.mp3` | Hip Hop beat Chill, calm, music | klaudux | [freesound.org/…/264081](https://freesound.org/people/klaudux/sounds/264081) | chill hip-hop / lo-fi |
| `upbeat-piano-loop-87bpm_deadrobotmusic.mp3` | Upbeat Piano Loop [87bpm] [c# major] | deadrobotmusic | [freesound.org/…/583698](https://freesound.org/people/deadrobotmusic/sounds/583698) | soulful piano loop |

Note: CC0 is the uploader's own declaration. If a rights holder ever disputes a track, remove it from this folder and the catalogue.
