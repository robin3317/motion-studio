# motion-studio — Architecture (Step 3)

Locked: 2026-11-08

## Role split
- **motion-studio = director**: brief, facts, story, style, shot plan, audio rules, QA, mode and gate control.
- **Official HyperFrames skills = engine know-how** (`/hyperframes`, `/hyperframes-cli`, `/media-use`). This is a **dependency**: setup installs them, and motion-studio delegates composition syntax and rendering to them.

## Runtimes
- Node.js 22+ (HyperFrames, site capture), FFmpeg, **Python** (audio analysis/mixing, procedural SFX, QA helpers)

## Distribution (all four)
1. Claude Code plugin: `claude plugin marketplace add robin3317/motion-studio`
2. `npx skills add robin3317/motion-studio`
3. ZIP from GitHub Releases → upload in desktop/Cowork
4. Git clone into `~/.claude/skills`

## Layout
```
motion-studio/                    repo root
├── .claude-plugin/               plugin.json + marketplace.json
├── README.md  LICENSE (MIT)
├── docs/                         build notes (not shipped)
├── tests/                        trigger + functional tests
└── skills/motion-studio/
    ├── SKILL.md
    ├── references/
    │   ├── modes.md  workflow.md  three-d.md  audio.md  voiceover.md
    │   ├── typography-i18n.md  data-gathering.md  setup.md  qa.md
    │   ├── playbooks/  company-promo  product-promo  release-promo  brand-promo  footage-edit
    │   ├── styles/     preset cards
    │   └── shots/      shot recipe cards
    ├── scripts/        preflight, site capture, audio mix/duck, procedural SFX, QA
    ├── templates/      HyperFrames starters (16:9, 9:16, 1:1, 4:5) + 3D starter
    └── assets/audio/   music/ sfx/ CREDITS.md (CC0 only)
```
Rule (from the guide): no README.md inside `skills/motion-studio/`.
