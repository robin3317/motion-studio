# Playbook: Release promo (course, movie, event, app, drop)

**Purpose:** get people to remember the **date** and take the **action**.
**Variants:** Teaser · Announcement · Countdown · Launch day. Ask which one if it's unclear (in Autopilot, infer it from the date: future and no details → Teaser; details known → Announcement; days remaining requested → Countdown; today → Launch day).

## Inputs
Title, type, date + time + **time zone**, place or platform, price (optional), up to 3 selling points, CTA + URL, poster or key art (if any). See `data-gathering.md` §5.

## Defaults
- Style by type: course → **Bold Kinetic**, **Corporate Clean** or **Isometric Kinetic** (tech/dev courses); movie → **Cinematic 3D**; event → **Bold Kinetic** or **Playful Pop**; app → **Tech Neon** or **Isometric Kinetic**; fashion drop → **Editorial** or **Minimal Luxury**.
- Music: builds tension and releases at the reveal or date. 90–140 BPM depending on energy.

## Variant structures (15–30 s)
**Teaser**: mystery, minimal information
| Beat | Notes |
|---|---|
| Hook (0–3 s) | Intriguing line or visual fragment |
| Glimpses (3–10 s) | Partial reveals: silhouettes, cropped key art, blurred title |
| Tag (last 3–5 s) | "Coming soon" / season / month + logo. **No full details** |

**Announcement**: complete information
| Beat | Notes |
|---|---|
| Hook | Title reveal (`3d-logo-reveal` or `kinetic-title`) |
| What + why | Up to 3 selling points (`feature-grid`) |
| When / where / price | Large and clear, ≥ 2.5 s on screen |
| CTA | URL / button text (`cta-end-card`) |

**Countdown**: reusable, one composition with a variable
- Make the number a **variable** (e.g. `daysLeft`, declared in `data-composition-variables`) so the same composition renders "7 days", "3 days", "1 day" without a rebuild. Render one with `--variables '{"daysLeft":3}'`, or all at once with `--batch rows.json` (one output per row). With `--batch`, put the variable in the output name, e.g. `-o "../renders/countdown-{daysLeft}days-v1.mp4"`, or the rows collide. Tested: one composition rendered both "24 days to go" and "1 day to go".
- Structure: title flash → big number (`countdown-flip`) → date line → CTA. 6–15 s is ideal.
- Wording per number: "1 day left" (singular), "Tomorrow", "Final hours". Translate correctly for the language.

**Launch day**: urgency and celebration
| Beat | Notes |
|---|---|
| Hook | "Out now" / "Live now" / "Enrolment open" |
| Reveal | Key art / product / course hero |
| Reason | 1–2 benefits |
| CTA | Strongest CTA, URL large, ≥ 2 s |

## Rules
- Dates and times exactly as given, with the time zone when the audience spans zones.
- Never invent a price, discount or deadline.
- For a movie, use only official key art the user has rights to.
