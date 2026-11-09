#!/usr/bin/env node
// motion-studio: capture website screenshots + brand cues with Playwright.
//
// Usage:
//   node capture_site.mjs --url https://example.com --out assets/screens [--formats 16:9,9:16] [--full]
//
// Writes per format: <slug>_<fmt>_viewport.png (and _full.png with --full),
// plus brand.json: title, description, og:image, icons, theme-color, CSS colour variables,
// dominant UI colours, font families, logo candidates. Facts still need human/agent review.
// Needs Playwright resolvable from the project (npm i -D playwright && npx playwright install chromium).
// Only capture sites the user has asked about. Respect logins/paywalls: never bypass them.
import { createRequire } from "node:module";
import { mkdir, writeFile, access } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf("--" + k); return i < 0 ? d : args[i + 1]; };
const flag = (k) => args.includes("--" + k);
const url = opt("url");
const out = path.resolve(opt("out", "assets/screens"));
const formats = String(opt("formats", "16:9")).split(",").map((s) => s.trim()).filter(Boolean);
if (!url || !/^https?:\/\//i.test(url)) { console.error("Usage: --url https://… --out <dir> [--formats 16:9,9:16] [--full]"); process.exit(2); }

const VIEWPORTS = {
  "16:9": { width: 1920, height: 1080, deviceScaleFactor: 1, isMobile: false },
  "9:16": { width: 360, height: 640, deviceScaleFactor: 3, isMobile: true },      // 1080×1920 output
  "1:1": { width: 1080, height: 1080, deviceScaleFactor: 1, isMobile: false },
  "4:5": { width: 360, height: 450, deviceScaleFactor: 3, isMobile: true },       // 1080×1350 output
};

function loadPlaywright() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  for (const base of [process.cwd(), here, path.dirname(here)]) {
    try { return createRequire(path.join(base, "package.json"))("playwright"); } catch { /* try next */ }
  }
  console.error("Playwright not found. Ask the user, then run in the project: npm i -D playwright && npx playwright install chromium");
  process.exit(3);
}

const HIDE_CSS = `
  [id*="cookie" i], [class*="cookie" i], [id*="consent" i], [class*="consent" i],
  [id*="gdpr" i], [class*="gdpr" i], [aria-label*="cookie" i] { display: none !important; }
  * { animation-play-state: paused !important; caret-color: transparent !important; }
`;

const { chromium } = loadPlaywright();
const browser = await chromium.launch(process.env.HYPERFRAMES_BROWSER_PATH ? { executablePath: process.env.HYPERFRAMES_BROWSER_PATH } : {});
await mkdir(out, { recursive: true });
const slug = new URL(url).hostname.replace(/^www\./, "").replace(/[^a-z0-9]+/gi, "-");
const files = [];
let brand = null;

for (const fmt of formats) {
  const vp = VIEWPORTS[fmt];
  if (!vp) { console.error(`Unknown format ${fmt}`); continue; }
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.deviceScaleFactor, isMobile: vp.isMobile, hasTouch: vp.isMobile });
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: "networkidle", timeout: 45000 }).catch(() => page.goto(url, { waitUntil: "load", timeout: 45000 }));
  await page.addStyleTag({ content: HIDE_CSS }).catch(() => {});
  await page.waitForTimeout(800);

  const vpFile = path.join(out, `${slug}_${fmt.replace(":", "x")}_viewport.png`);
  try { await access(vpFile); console.error(`exists, skipping: ${vpFile}`); } catch { await page.screenshot({ path: vpFile }); files.push(vpFile); }
  if (flag("full")) {
    const fullFile = path.join(out, `${slug}_${fmt.replace(":", "x")}_full.png`);
    const h = await page.evaluate(() => Math.min(document.documentElement.scrollHeight, 8000));
    await page.setViewportSize({ width: vp.width, height: Math.max(vp.height, Math.floor(h)) });
    try { await access(fullFile); } catch { await page.screenshot({ path: fullFile, fullPage: false }); files.push(fullFile); }
  }

  if (!brand) {
    brand = await page.evaluate(() => {
      const meta = (sel) => document.querySelector(sel)?.getAttribute("content") || null;
      const abs = (u) => { try { return new URL(u, location.href).href; } catch { return null; } };
      const colourRe = /^(#[0-9a-f]{3,8}|rgba?\(|hsla?\(|oklch\()/i;
      const vars = {};
      for (const sheet of Array.from(document.styleSheets)) {
        let rules; try { rules = sheet.cssRules; } catch { continue; }
        for (const r of Array.from(rules || [])) {
          if (r.selectorText && /:root|html/.test(r.selectorText) && r.style) {
            for (const name of Array.from(r.style)) {
              if (name.startsWith("--")) { const v = r.style.getPropertyValue(name).trim(); if (colourRe.test(v)) vars[name] = v; }
            }
          }
        }
      }
      const tally = {};
      const bump = (c, w) => { if (!c || c === "rgba(0, 0, 0, 0)" || c === "transparent") return; tally[c] = (tally[c] || 0) + w; };
      document.querySelectorAll("a, button, [class*=btn], header, nav, h1, h2").forEach((el) => {
        const cs = getComputedStyle(el); bump(cs.backgroundColor, 3); bump(cs.color, 1);
      });
      const colours = Object.entries(tally).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([c]) => c);
      const fonts = [...new Set(["body", "h1", "h2", "button"].map((s) => document.querySelector(s)).filter(Boolean).map((el) => getComputedStyle(el).fontFamily))];
      const icons = Array.from(document.querySelectorAll('link[rel*="icon"]')).map((l) => ({ rel: l.rel, href: abs(l.getAttribute("href")), sizes: l.getAttribute("sizes") }));
      const logos = [];
      document.querySelectorAll("header img, nav img, a[href='/'] img, img[alt*=logo i], img[src*=logo i]").forEach((img) => logos.push({ type: "img", src: abs(img.getAttribute("src")), alt: img.alt || "" }));
      document.querySelectorAll("header svg, nav svg, a[href='/'] svg").forEach((svg, i) => { if (i < 3 && svg.outerHTML.length < 60000) logos.push({ type: "inline-svg", svg: svg.outerHTML }); });
      return {
        url: location.href, title: document.title, description: meta('meta[name="description"]') || meta('meta[property="og:description"]'),
        og_image: abs(meta('meta[property="og:image"]') || ""), theme_color: meta('meta[name="theme-color"]'),
        css_colour_vars: vars, dominant_ui_colours: colours, font_families: fonts, icons, logo_candidates: logos.slice(0, 8),
        lang: document.documentElement.lang || null,
      };
    });
  }
  await ctx.close();
}
await browser.close();

const brandFile = path.join(out, `${slug}_brand.json`);
await writeFile(brandFile, JSON.stringify({ captured_at: new Date().toISOString(), ...brand }, null, 2));
console.log(JSON.stringify({ screenshots: files, brand: brandFile }, null, 2));
