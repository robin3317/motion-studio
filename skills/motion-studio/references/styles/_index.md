# Style presets

A preset is a **starting point**: keep its motion and typography rules, and swap in the brand's colours and a font pair chosen for this brand (`../typography-i18n.md`; never just the template's default). Step-by-step: offer the playbook's default plus 1–2 alternatives at G3. Autopilot: choose by playbook + tone, then log why.

| Preset | Feel | Best for |
|---|---|---|
| `corporate-clean.md` | Clear, trustworthy, calm | Company promos, B2B, finance, services |
| `bold-kinetic.md` | Loud, fast, typographic | Social ads, events, courses, brand manifestos |
| `cinematic-3d.md` | Epic, dimensional, premium | Product reveals, movie and game releases, logo reveals |
| `minimal-luxury.md` | Quiet, elegant, spacious | Premium products, fashion, real estate, beauty |
| `playful-pop.md` | Fun, bouncy, colourful | Consumer apps, food, kids/edu, casual brands |
| `tech-neon.md` | Dark, glowing, futuristic | SaaS, AI, dev tools, gaming, crypto/fintech |
| `editorial.md` | Magazine, artful, grid-based | Agencies, media, culture, fashion drops, brand stories |
| `isometric-kinetic.md` | Smart, crisp, explainer-tech: isometric objects + kinetic headlines, dark/paper/solid rhythm | SaaS & tech company promos, digital products, courses, explainers, B2B, announcements with facts. Has its own template: `--template isometric-kinetic` |

## Every preset in 3D (the default), and its tokens
Videos are 3D unless the user asks for 2D (`../three-d.md`). Each preset keeps its type, colour and motion rules; this table adds its 3D treatment and its component tokens (`../craft.md`, "Components"). Sizes are for 1080p.

| Preset | Object and material | Light and depth | Object motion | `--r-sm / --r-card / --r-pill` | `--border-w` | Intensity |
|---|---|---|---|---|---|---|
| corporate-clean | Logo or simple solids, matte or satin plastic in brand colours | Soft studio light, light or mid background, faint glow | Slow turn 15–25°, gentle float | 8 / 20 / 999 | 2 px | 1–2 |
| bold-kinetic | Chunky extruded shapes, flat-shaded or glossy, strong colour | Hard key light, solid colour background | Fast turns that stop dead on beats | 6 / 16 / 999 | 3 px | 4–5 |
| cinematic-3d | Metal or glass logo and product, fine bevels | Low key, coloured rim, haze, dust | Slow turns 20–40°, dolly-ins | 4 / 12 / 999 | 2 px | 2–3 |
| minimal-luxury | One object, satin or brushed metal, lots of empty space | Soft top light, gradient background, no dust | Very slow turn, almost still | 2 / 6 / 999 | 2 px | 1 |
| playful-pop | Rounded, clay-like solids in 3–4 colours | Bright even light, soft shadow under objects | Bouncy pops and spins (`back.out`) | 16 / 32 / 999 | 3 px | 3–4 |
| tech-neon | Dark metal or glass with bright edges, UI as HTML cards | Dark stage, accent rim light, `glowPlane`, dust | Precise turns, parts orbiting | 10 / 20 / 999 | 2 px | 3 |
| editorial | One sculptural object or a framed image plane | Flat even light, paper or solid background | Slow drift, hard cuts | 0 / 0 / 0 | 2 px | 2 |
| isometric-kinetic | 2D by design (drawn isometric objects, own template). Use it only when the user asks for it, for 2D, or for a flat explainer look | – | – | 10 / – / 999 | 2 px | 3 |

Whatever the preset, apply `../craft.md` (one accent word, a metaphor per scene, background rhythm, sync text to VO or beats).

Adapting colours: map the brand's primary to the preset's **accent**, keep the preset's background logic (light/dark), and check text contrast (≥ 4.5:1). If the brand's primary fails contrast as a text colour, use it for shapes and highlights only.
