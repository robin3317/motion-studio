# Step 8: End-to-end test report (2026-11-09)

All runs: Autopilot, HyperFrames 0.9.23, rendered in a Linux cloud sandbox, delivery quality. Renders are in `tests/renders/`.
(They contain third-party brands, Optimizely and CeraVe/KMS: internal tests only, don't publish.)

| # | Playbook | Subject | Format / length | Style | QA |
|---|---|---|---|---|---|
| 1 | Company (facts) | optimizely.com | 16:9 · 20 s | Corporate Clean (dark), brand palette | all pass, −14.1 LUFS / −1.0 dBTP |
| 2 | Brand (feelings) + 3D | optimizely.com | 9:16 · 15 s | Bold Kinetic, cuts on music bars, 3D extruded logo | all pass, −14.0 / −1.4 |
| 3 | Product (real photos) | CeraVe cream @ kmsmarketplace.com | 4:5 · 15 s | Corporate Clean (light), ৳ prices | all pass, −14.0 / −1.0 |
| 4a | Release: Announcement | Optimizely webinar "agent-ready website", Dec 3 | 16:9 · 20 s | Tech Neon | all pass |
| 4b | Release: Countdown ×2 (variables + batch) | same | 9:16 · 6 s | Tech Neon | all pass; "24 days to go" / "1 day to go" |
| 5 | Footage edit | Talking Head Sample.mp4 | 16:9 · 33 s | captions + lower third + zooms | all pass, −14.1 / −1.1, A/V offset 0.0 ms |

## Bugs found by the tests, and fixed
1. Shape-wipe bars stayed visible on screen (caught by `hyperframes check`) → hidden outside the wipe, moved vertically
2. Closing URL on screen < 2 s (HyperFrames rule) → CTA rule raised to ≥ 2 s in cta-end-card + qa.md
3. Repeated `fromTo` on one element (GSAP warning) → second tween uses `to`
4. 3D logo too big, covering the tagline (the check can't see WebGL) → added a stills-review rule to three-d.md
5. ACES tone mapping washed out the brand lime → NeutralToneMapping guidance + template supports multi-colour SVG logos
6. Hook text too faint on frame 0, a hyphenated word broke across lines → fixed (frame-0 rule already existed; nowrap)
7. Batch countdown outputs collided → documented `{daysLeft}` in the output name
8. silence_cuts: a fixed −35 dB threshold doesn't fit quiet recordings → auto threshold measured per recording
9. Transcript re-timing dropped sentence-final words (whisper stretches them over pauses) → match on word start
10. Caption outline (`-webkit-text-stroke`) drew lines inside the letters → text-shadow only
11. Reading-time rule pushed the 15 s release video to 20 s → working as designed (more time, not crammed text)

## New / changed files from testing
- scripts/apply_edl.py (new): applies the EDL, cuts the video with click-free joins, re-times the transcript
- scripts/silence_cuts.py: auto threshold
- templates/three-starter: per-path SVG colours
- references: typography-i18n (npm @fontsource, unicode-range fallback, no text-stroke), three-d (tone mapping, check blind spot),
  qa (caption warnings, snapshot), footage-edit (apply_edl, name confirmation), release-promo (batch naming), data-gathering (whisper model)

## Environment notes (sandbox only, not skill bugs)
- Websites, Hugging Face and music CDNs were blocked in the sandbox → data was gathered through the built-in browser and the whisper model downloaded by browser (SHA-256 verified)
- Background removal (rembg) not tested: its model download was blocked. Product shown in a photo card instead (2.5D)

## Open items for Robin
- Confirm the speaker's name: the transcript heard "Eric Edmies"; I used "Eric Edmeades"
- Watch all 7 renders and judge taste: pacing, music choice, SFX levels (measured, not heard)
- Run tests/triggers.md in Claude Code (triggering can't be measured from here)
- Test on Windows natively (all runs were Linux)

## Trigger test (2026-11-09, Claude Code 2.1.319, plugin installed from the release ZIP)
Result: **20 / 20**. All 12 "should trigger" prompts loaded `motion-studio:motion-studio`, and none of the 8 "should not" prompts did
("Design a thumbnail for my video" correctly went to a thumbnail skill instead).
Method: `claude -p "<prompt>" --max-turns 2 --allowedTools Skill`, checking which skill was invoked. The official HyperFrames skills were not installed in this run.

## Release checks (v0.1.0-beta)
- `claude plugin validate .` → passed. `claude plugin validate .claude-plugin/marketplace.json` → passed
- `claude plugin marketplace add` + `claude plugin install motion-studio@codeonces` → installed, version 0.1.0-beta, Skills (1): motion-studio
- Skill ZIP: 93 files, 19.7 MB (most of it is music). Upload in the Claude desktop app is not tested yet
