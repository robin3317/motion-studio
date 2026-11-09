# Data gathering

Order of trust: **user-provided > official website / store page > nothing.** Never fill gaps with invented content.

## 1. User-provided material (always first)
Ask for or accept: a written brief, fact sheet, logo (SVG/PNG preferred), brand colours, brand fonts (files), product photos, screenshots, footage, voiceover, music. Copy everything into `assets/` with clear names (`logo.svg`, `product-front.png`). Never edit originals; save processed versions with a suffix (`product-front_cutout.png`).

## 2. Website extraction (company / product / release / brand)
1. **Text facts**: fetch the home, about, services/products, pricing (if relevant) and contact pages. Extract: name, tagline, what they do, services/features, numbers (clients, years, locations), notable clients/partners (only if publicly listed), CTA (URL, app links).
2. **Brand cues**:
   - Logo: inline SVG in the header, `<link rel="icon">` (SVG first), `og:image`, or `apple-touch-icon`. Prefer vector.
   - Colours: CSS custom properties (`--primary` etc.), `meta[name=theme-color]`, the dominant button/link colours. Record the hex codes.
   - Fonts: CSS `font-family`. Brand fonts are often commercial. Use the actual font only if it's freely licensed (e.g. Google Fonts) or the user supplies the files. Otherwise pick the closest free alternative (`typography-i18n.md`).
3. **Screenshots**: capture with `node "<skill>/scripts/capture_site.mjs" --url <url> --out assets/screens --formats 16:9,9:16`. It captures full-page and viewport shots at the right sizes. Hide cookie banners when possible. Use screenshots for software and web products, and as background texture for company promos.
4. Record every fact in `facts.json` with its URL. Record every image in `credits.json` (source URL, "owner: <company>", "use: promotional, provided/approved by client").

If the site blocks fetching or needs a login, ask the user for the content. Don't use cached copies or mirrors.

## 3. Product images
- Sources: user uploads, the product's own website or store page, or screenshots (software).
- **Rights**: images from a website need the user's confirmation that they may use them. Step-by-step: confirm at G1. Autopilot: include the confirmation in the one essentials batch.
- Quality bar: at least as large as the frame area it will fill. If an image is too small, use it smaller in the layout. Don't upscale by more than 1.5×.
- Background removal (optional): `python "<skill>/scripts/cutout.py" assets/product.png`. Needs `rembg`; ask before installing. Check the edges on a dark and a light background before using the cut-out.
- AI-generated images: **only with explicit user consent**, flagged `"ai_generated": true` in `credits.json`, and never used as the real product.

## 4. Footage intake (footage-edit playbook)
- Probe each clip: `ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of json <file>`
- Note: resolution, fps, rotation, audio presence, duration.
- Transcript: the user's SRT/VTT if given. Otherwise `npx hyperframes transcribe <file> --language <code>` (local and free). The first run downloads a whisper.cpp model from Hugging Face (base.en about 150 MB, small.en about 490 MB) and builds whisper.cpp unless it's installed. Behind a blocking network, the model file can be downloaded in a browser, checked against the SHA-256 that HyperFrames pins, and placed in its cache. Or use the pip package `pywhispercpp` with that model. **Read the transcript** and fix names, product terms and numbers before using it.

## 5. Release information (release-promo)
Collect: title, type (course/movie/event/app/drop), date and time with **time zone**, location or platform, price (if any), key selling points (max 3), CTA (URL, "Enroll", "Book now"…), the poster or key art if it exists, and the variant (teaser / announcement / countdown / launch day).
