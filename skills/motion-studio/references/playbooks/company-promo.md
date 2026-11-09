# Playbook: Company promo (FACTS)

**Purpose:** the viewer should *know* who the company is, what it does and why to trust it, then act.
**Use when:** a company intro, corporate promo, "about us" video, or a video from a company website.

## Inputs
Required: company name, and a website or written brief. Helpful: logo, brand colours, services, numbers, client logos (public only), offices, CTA.
Gather with `data-gathering.md` §1–2. Every fact goes in `facts.json`.

## Defaults
- Style: **Corporate Clean**. Alternatives: Editorial (agencies, media), Tech Neon (tech/SaaS), **Isometric Kinetic** (tech/SaaS/B2B with a clear "how it works"), Minimal Luxury (premium services).
- Music: confident, modern, 100–125 BPM. Builds gently, no drops.
- VO: optional. Strong fit for 30–60 s.

## Beat structures
**15 s**
| Time | Beat | Shot ideas |
|---|---|---|
| 0–2.5 | Hook: the bold promise or tagline | `kinetic-title` |
| 2.5–8 | What they do: 2–3 services | `feature-grid` |
| 8–12 | Proof: one strong stat or client logos | `stat-counter` / `logo-wall` |
| 12–15 | Logo + CTA | `cta-end-card` |

**30 s**
| Time | Beat | Shot ideas |
|---|---|---|
| 0–3 | Hook | `kinetic-title`, `logo-assemble` |
| 3–8 | The problem or need they solve | `parallax-push` over a screenshot or imagery |
| 8–16 | Services / how it works (3 items) | `feature-grid`, `device-mockup-screens` |
| 16–23 | Proof: stats, clients, years, locations | `stat-counter`, `logo-wall` |
| 23–27 | Why them: one differentiator line | `kinetic-title` |
| 27–30 | Logo + CTA + URL | `cta-end-card` |

**60 s**: the 30 s structure, with team/culture or process (2 beats) and a second proof block. Keep one idea per beat.

## Copy rules
- Verbs and outcomes over adjectives ("Ship apps 2× faster" beats "innovative solutions").
- Stats only from `facts.json`. Round only as the source does.
- Client logos only if the company lists them publicly. Never imply endorsement.

## Pitfalls
Too many services crammed in (max 3 per beat). Tiny screenshot text. Generic stock-feeling visuals. Use the company's real screenshots and colours.
