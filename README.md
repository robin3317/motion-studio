# Motion Studio

**A Claude skill that directs motion-graphics videos.** Describe what you need ("a 20-second promo for my company", "a launch teaser for my course", "add captions to this clip") and Claude plans, designs, animates, sound-designs and renders an MP4 with [HyperFrames](https://github.com/heygen-com/hyperframes).

> **v0.3.0-beta, test release.** New in v0.3: videos are **3D by default**, pills, cards and buttons are drawn cleanly, fonts are chosen per video, and the skill checks its own frames ([changelog](CHANGELOG.md)). Your feedback decides what improves next ([give feedback](#feedback)).

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
- **3D by default:** every video gets a real Three.js stage (logo, product or shapes with light and depth) under sharp HTML text, rendered frame-accurately. Say "2D" if you want it flat.
- **Audio:** 11 bundled CC0 music tracks, 21 CC0 sound effects, automatic ducking under voice, normalized to −14 LUFS. Bring your own music, search Openverse, or use AI music with your own key.
- **Voiceover:** optional. Use your recording, free local TTS, or a paid TTS of your choice.
- **Any language:** script and on-screen text in the language you ask for, with proper fonts (Bangla, Arabic/RTL, Hindi, CJK…).
- **Real facts only:** no invented stats, clients or prices. AI images only with your consent.

## Styles

Every video starts from a style preset, which the skill adapts to your brand colours and fonts. Step-by-step mode offers 2–3 styles with preview frames. Autopilot picks one from the playbook and your tone, and writes down why. You can also just ask: *"make it in the Tech Neon style"*.

| Style | Feel | Best for |
|---|---|---|
| **Corporate Clean** | Clear, trustworthy, calm | Company promos, B2B, finance, services |
| **Bold Kinetic** | Loud, fast, typographic | Social ads, events, courses, brand manifestos |
| **Cinematic 3D** | Epic, dimensional, premium | Product reveals, movie and game releases, logo reveals |
| **Minimal Luxury** | Quiet, elegant, spacious | Premium products, fashion, real estate, beauty |
| **Playful Pop** | Fun, bouncy, colourful | Consumer apps, food, kids/edu, casual brands |
| **Tech Neon** | Dark, glowing, futuristic | SaaS, AI, dev tools, gaming, fintech |
| **Editorial** | Magazine, artful, grid-based | Agencies, media, culture, fashion drops, brand stories |
| **Isometric Kinetic** *(new in v0.2)* | Smart, crisp, explainer-tech: isometric objects + kinetic headlines | Tech/SaaS promos, digital products, courses, explainers, announcements with facts |

Each style comes with its own typography, motion, transition, music and SFX rules. Every style also follows shared craft rules: one accent word per headline, a visual metaphor per scene, and text synced to the voice or the beat. Scenes are built from **21 shot recipes** (kinetic title, stat counter, 3D logo reveal, product orbit, isometric stack, terminal window, timeline, countdown, captions, end card…). See [`references/styles/`](skills/motion-studio/references/styles/) and [`references/shots/`](skills/motion-studio/references/shots/).

## Requirements

- **Claude Code** or the **Claude desktop app (Cowork)**. It needs terminal and file access, so rendering doesn't run in plain chat.
- **Node.js 22+**, **FFmpeg**, **Python 3.10+** (with `numpy`)
- The official **HyperFrames skills** (`/hyperframes`, `/hyperframes-cli`, `/media-use`)

You don't need to check these yourself. The skill runs a read-only check first and offers to install what's missing (with your approval).

## Install

> ## **IMPORTANT: Claude Code and the Claude desktop app (Cowork) are two separate places**
>
> **Installing motion-studio in one does NOT add it to the other, even on the same computer with the same account.**
>
> **Install it once in every place where you want to use it:**
>
> | **You want to use it in…** | **Install it with…** |
> |---|---|
> | **Claude Code** (terminal or IDE) | **the plugin steps below** |
> | **Claude desktop app / Cowork** | **the ZIP upload below** |
>
> **If motion-studio is "missing", you are in the place where it was not installed yet. Updates are separate too: update it in each place.**

**Easiest: let Claude do it (Claude Code)**
Paste this into Claude Code:
```
Install the motion-studio plugin from https://github.com/robin3317/motion-studio, then install the HyperFrames skills it needs.
```
Approve the commands when asked, then run `/reload-plugins` (or start a new session). In the Claude desktop app (Cowork) use the ZIP upload below instead: Cowork can't run `/plugin` commands.

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
1. Download `motion-studio-skill-v0.3.0-beta.zip` (the newest version) from [Releases](https://github.com/robin3317/motion-studio/releases).
2. In Claude, open **Settings → Capabilities → Skills**, click **Upload skill**, and choose the ZIP.

**Manual**
Copy `skills/motion-studio/` into `~/.claude/skills/motion-studio/`.

**Then install the HyperFrames skills** (one time):
```
npx hyperframes skills update
```
Or, in Claude Code: `claude plugin marketplace add heygen-com/hyperframes` then `claude plugin install hyperframes@hyperframes`. Start a new session afterwards.

## Updating

**Each place updates by itself.** Updating motion-studio in Claude Code does not update it in the Claude desktop app (Cowork), and the other way round.

motion-studio checks for a new release at most **once a day** when it starts. It stays silent when offline and sends nothing about you. It also works where the GitHub API is blocked (for example in Claude Cowork's cloud): it then reads the version from `raw.githubusercontent.com`. When a new version is out, it asks: **Upgrade now / Remind me tomorrow / Snooze a week / Don't ask again**.

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

**It checks its own work.** After each scene it makes a contact sheet of the whole move, and before rendering it runs a visual audit that measures every pill, tag, card and button (wrapped labels, off-centre text, clipped boxes, text over 3D) and crops them for review. Projects keep a `PROGRESS.md` and a list of feedback rules, so a new chat continues where the last one stopped.

**Slow or locked-down machines** (for example Claude Cowork's cloud: 2 CPU cores, no GPU, most sites blocked) are supported: the preflight reports the limits up front, and `scripts/render.py` renders in foreground calls that resume where the last one stopped.

`skills/motion-studio/SKILL.md` is the entry point. Detailed guides live in `references/` and load only when needed. Scripts are in `scripts/`, project starters in `templates/`, and audio in `assets/audio/`.

## Licences and credits

- **Code and docs:** MIT © 2026 Robin Rahman (Codeonces)
- **Bundled audio:** all CC0 1.0. Music by Bertsz, Drakensson, code_box, evanjones4, guitarman213, BurghRecords, szegvari, klaudux and deadrobotmusic (via Freesound). Sound effects generated by this project. See [`assets/audio/CREDITS.md`](skills/motion-studio/assets/audio/CREDITS.md).
- **Rendering:** [HyperFrames](https://github.com/heygen-com/hyperframes) by HeyGen (Apache-2.0), installed separately
- **Fonts:** none bundled. The skill fetches open-licence fonts per project from npm's `@fontsource` (`scripts/get_font.py`), with their licence files.
- Videos you make are yours. Check the licences of any music, images or footage *you* add (the skill records them in your project's `credits.json`).

## Feedback

This is a beta and feedback shapes v0.2. After you try it, please [open a feedback issue](https://github.com/robin3317/motion-studio/issues/new?template=feedback.yml) (it takes 2 minutes) or message me directly. Most useful: your prompt, OS, what broke, and how the video looked.

## Known limitations (v0.2.1-beta)

- v0.2 adds Isometric Kinetic and shared craft rules. The older presets still look plainer than it does; continuous-camera "launch film" motion (morphs, motion blur) is planned next.
- The Isometric Kinetic template is tested with music only. Headlines synced to a voiceover, in 9:16, still need real-world testing.
- Tested on Linux and Windows (all templates build, render and pass QA). Stopping and resuming a long render is untested on Windows, and nothing is tested on macOS: reports are very welcome.
- Product background removal (`rembg`) is untested.

---
Made by **Robin Rahman**: [Codeonces on YouTube](https://www.youtube.com/@codeonces) · [robinrahman.me](https://robinrahman.me)
