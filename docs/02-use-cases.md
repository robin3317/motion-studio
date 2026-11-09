# motion-studio — Use Cases & Success Criteria (Step 2)

Locked: 2026-11-08

## Scope
A **general motion-graphics skill** that ships with predefined **playbooks**. More playbooks will be added later (e.g. explainer videos, stickman shorts).
Visual **style presets** (e.g. Corporate Clean, Bold Kinetic, Cinematic 3D, Minimal Luxury, Playful Pop) are starting points that adapt to the brand's colours and fonts. Autopilot picks one; guided mode lets the user choose.

## Playbooks v1

### UC1 — Company promo (FACTS)
- Trigger: "promo video for [company]", "company intro video from [website]"
- Flow: user data → website fetch + screenshots → fact confirmation (guided) → script → storyboard → build → audio → render
- Content: services, stats, clients, offices, achievements
- Result: informative, on-brand company video

### UC2 — Product promo
- Trigger: "promo video for my product", "product launch ad for [product]"
- Flow: real product images (upload / product site / screenshots) → cut-out and crop → features and USP → 3D/2.5D hero shots → feature beats → CTA
- Result: product video with the real product as the hero

### UC3 — Release promo (courses, movies, events…)
- Variants: **Teaser**, **Announcement**, **Countdown**, **Launch day**
- Inputs: what, when, where, price, CTA
- Flow: hook → reveal → details → date/countdown → CTA
- Result: video centred on the date and the CTA

### UC5 — Footage edit (added in Step 4)
- Cuts, captions, overlays, lower thirds on recorded video

### UC4 — Brand promo (FEELINGS)
- Trigger: "brand video", "brand story / identity reel"
- Content: values, mood, tone, identity. Few facts.
- Flow: emotional narrative → kinetic type, logo animation, 3D logo reveal → tagline end card

### General motion graphics (no playbook match)
- Any other motion-graphics request runs through the same core workflow without a playbook.

## Success criteria
- Triggers on ≥ 9/10 relevant requests; doesn't trigger on unrelated video questions
- Autopilot: one brief → finished MP4, asks only for paid API calls
- Guided: exactly 4 gates, no extra back-and-forth
- QA passes on every video: text readable and inside safe zones, no overlaps, voice intelligible over the music, correct duration/format/fps, every asset's licence recorded
