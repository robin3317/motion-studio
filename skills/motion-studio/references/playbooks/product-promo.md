# Playbook: Product promo

**Purpose:** make the **real product** the hero and show why it's worth having.
**Use when:** product ads, launch videos, feature showcases, e-commerce promos, app or SaaS promos.

## Inputs
Required: the product name and real images (user uploads, product page, or screenshots for software). Helpful: key features (max 3–4), the USP, price/offer, CTA, a GLB model if one exists.
- Image rights confirmed (`data-gathering.md` §3).
- Cut-outs via `scripts/cutout.py` for physical products on busy backgrounds.

## Defaults
- Physical products: **Cinematic 3D** or **Minimal Luxury** (premium), **Playful Pop** (consumer, fun).
- Software/apps: **Tech Neon** or **Corporate Clean**, built around `device-mockup-screens`.
- Music: energetic, 110–130 BPM. Hit the product reveal on a downbeat.

## Beat structures
**15 s**
| Time | Beat | Shot ideas |
|---|---|---|
| 0–2 | Hook: the problem, or a bold teaser of the product | `kinetic-title` / `parallax-push` |
| 2–5 | Product reveal | `product-hero-orbit` |
| 5–11 | 2–3 features | `product-float-callouts` |
| 11–15 | Offer + CTA | `cta-end-card` |

**30 s**
| Time | Beat | Shot ideas |
|---|---|---|
| 0–3 | Hook | `kinetic-title` |
| 3–7 | Reveal | `product-hero-orbit` / `3d-logo-reveal` (brand) |
| 7–19 | Features (3 × ~4 s), each with a visual proof | `product-float-callouts`, `device-mockup-screens`, `feature-grid` |
| 19–24 | Social proof / spec highlight / price | `stat-counter` |
| 24–30 | Product + offer + CTA | `cta-end-card` |

## Rules
- The product must look exactly like itself: true colours, no shape distortion, no AI replacement (unless consented and not presented as the real product).
- No real 3D model → use 2.5D (`three-d.md`). Never invent a 3D model of a real product.
- One feature per beat, shown, not just written.

## Pitfalls
Low-resolution product images blown up. Callouts that cover the product. Too many features.
