# Motion Studio

**A Claude skill that directs motion-graphics videos.** Describe what you need ("a 20-second promo for my company", "a launch teaser for my course", "add captions to this clip") and Claude plans, designs, animates, sound-designs and renders an MP4 with [HyperFrames](https://github.com/heygen-com/hyperframes).

> **v0.1.0-beta, early test release.** It works end to end, but the visuals are still basic. Your feedback decides what improves next ([give feedback](#feedback)).

## What it makes

| Playbook | Example request |
|---|---|
| **Company promo** (facts) | "Make a 20 s promo for https://example.com" |
| **Product promo** (real product images) | "Product ad for this moisturizer, photos attached" |
| **Release promo**: teaser / announcement / countdown / launch day | "Countdown reel: 3 days until our webinar" |
| **Brand promo** (feelings) | "A brand video for my coffee shop: warm, cozy, handmade" |
| **Footage edit**: captions, pause cuts, lower thirds, zooms | "Add captions and zoom-ins to this talking-head video" |
| Anything else in motion graphics | "A logo reveal in 3D", "an explainer for our pricing" |

- **Two modes**
  - **Autopilot**: one brief in, finished MP4 out. It only stops to ask before paid API calls.
  - **Step-by-step**: you approve 4 checkpoints: brief + facts → script + storyboard → style frames → preview.
- **Formats:** 16:9, 9:16, 1:1, 4:5. Default length 15–30 s.
- **3D:** Three.js scenes (extruded logos, product turntables) rendered frame-accurately.
- **Audio:** 11 bundled CC0 music tracks, 21 CC0 sound effects, automatic ducking under voice, normalized to −14 LUFS. Bring your own music, search Openverse, or use AI music with your own key.
- **Voiceover:** optional. Use your recording, free local TTS, or a paid TTS of your choice.
- **Any language:** script and on-screen text in the language you ask for, with proper fonts (Bangla, Arabic/RTL, Hindi, CJK…).
- **Real facts only:** no invented stats, clients or prices. AI images only with your consent.

## Requirements

- **Claude Code** or the **Claude desktop app (Cowork)**. It needs terminal and file access, so rendering doesn't run in plain chat.
- **Node.js 22+**, **FFmpeg**, **Python 3.10+** (with `numpy`)
- The official **HyperFrames skills** (`/hyperframes`, `/hyperframes-cli`, `/media-use`)

You don't need to check these yourself. The skill runs a read-only check first and offers to install what's missing (with your approval).

## Install

**Easiest: let Claude do it (Claude Code)**
Paste this into Claude Code:
```
Install the motion-studio plugin from https://github.com/robin3317/motion-studio, then install the HyperFrames skills it needs.
```
Approve the commands when asked, then run `/reload-plugins` (or start a new session).

**Claude Code (plugin, manual)**
```
/plugin marketplace add robin3317/motion-studio
/plugin install motion-studio@codeonces
```

**Skills CLI**
```
npx skills add robin3317/motion-studio
```

**Claude desktop / Cowork (ZIP upload)**
1. Download `motion-studio-skill-v0.1.0-beta.zip` from [Releases](https://github.com/robin3317/motion-studio/releases).
2. In Claude, open **Settings → Capabilities → Skills**, click **Upload skill**, and choose the ZIP.

**Manual**
Copy `skills/motion-studio/` into `~/.claude/skills/motion-studio/`.

**Then install the HyperFrames skills** (one time):
```
npx hyperframes skills update
```
Or, in Claude Code: `claude plugin marketplace add heygen-com/hyperframes` then `claude plugin install hyperframes@hyperframes`. Start a new session afterwards.

## Updating

motion-studio checks for a new release at most **once a day** when it starts. It stays silent when offline and sends nothing about you. When a new version is out, it asks: **Upgrade now / Remind me tomorrow / Snooze a week / Don't ask again**.

To upgrade at any time, say **"upgrade motion-studio"** (plugin users: `/motion-studio:motion-studio-upgrade`), or by hand:

| Installed with | Upgrade |
|---|---|
| Plugin | `/plugin marketplace update codeonces`, then `/reload-plugins`. Or turn on auto-update: `/plugin` → Marketplaces → codeonces → Enable auto-update |
| Skills CLI | `npx skills add robin3317/motion-studio` |
| ZIP upload | Download the new ZIP from [Releases](https://github.com/robin3317/motion-studio/releases) and upload it again |

To turn the check off, set `MOTION_STUDIO_NO_UPDATE_CHECK=1`.

## Quick start

Open a folder for your video, start Claude, and ask:

- `Make a 20-second promo video for https://your-company.com on autopilot`
- `Create a 15 s vertical product ad for this product, step by step` (attach photos)
- `Make a countdown reel for my course launch on Dec 15, 9:16`
- `Edit talking-head.mp4: remove long pauses, add captions and a name title`

You get a versioned MP4 in `renders/`, plus a project folder you can ask Claude to tweak and re-render.

## How it works

```
brief & facts → script & storyboard → style frames → build (HyperFrames + Three.js)
→ audio (VO, music, SFX, ducking) → preview → final render → QA checks → MP4
```

`skills/motion-studio/SKILL.md` is the entry point. Detailed guides live in `references/` and load only when needed. Scripts are in `scripts/`, project starters in `templates/`, and audio in `assets/audio/`.

## Licences and credits

- **Code and docs:** MIT © 2026 Robin Rahman (Codeonces)
- **Bundled audio:** all CC0 1.0. Music by Bertsz, Drakensson, code_box, evanjones4, guitarman213, BurghRecords, szegvari, klaudux and deadrobotmusic (via Freesound). Sound effects generated by this project. See [`assets/audio/CREDITS.md`](skills/motion-studio/assets/audio/CREDITS.md).
- **Rendering:** [HyperFrames](https://github.com/heygen-com/hyperframes) by HeyGen (Apache-2.0), installed separately
- **Fonts:** none bundled. The skill fetches open-licence fonts (e.g. Google Fonts via `@fontsource`) per project.
- Videos you make are yours. Check the licences of any music, images or footage *you* add (the skill records them in your project's `credits.json`).

## Feedback

This is a beta and feedback shapes v0.2. After you try it, please [open a feedback issue](https://github.com/robin3317/motion-studio/issues/new?template=feedback.yml) (it takes 2 minutes) or message me directly. Most useful: your prompt, OS, what broke, and how the video looked.

## Known limitations (v0.1.0-beta)

- The visual style is still fairly flat. Stronger typography, animation and 3D craft is the next focus.
- Tested end to end on Linux. Windows and macOS reports are very welcome.
- Product background removal (`rembg`) is untested.

---
Made by **Robin Rahman**: [Codeonces on YouTube](https://www.youtube.com/@codeonces) · [robinrahman.me](https://robinrahman.me)
