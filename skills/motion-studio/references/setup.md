# Setup: preflight & guided install

## 1. Preflight (read-only)
Run from the video project folder:
```
python "<skill>/scripts/preflight.py"
```
`<skill>` = the folder that contains this skill's SKILL.md. Quote paths that contain spaces. On some systems Python is `python3` or `py`.

Preflight reports: OS, Node version, npm/npx, FFmpeg/ffprobe, Python version and packages, HyperFrames CLI reachability, HyperFrames skills, and optional tools. It installs nothing and never prints secret values.

## 2. Requirements

| Tool | Needed for | Required? |
|---|---|---|
| Node.js **22+** | HyperFrames CLI, site capture | Yes |
| FFmpeg + ffprobe | Rendering, audio mixing, QA | Yes |
| Python **3.10+** | Helper scripts (audio, SFX, QA) | Yes |
| HyperFrames skills (`/hyperframes`, `/hyperframes-cli`, `/media-use`) | Composition authoring, preview, render | Yes |
| Playwright Chromium | Website screenshots | For company/product promos from a website |
| `rembg` (Python) | Product background removal | Optional |
| Docker | Pixel-identical renders across machines | Optional |

## 3. Guided install
Ask once, listing exactly what's missing and the commands you'll run. Install only after the user says yes, and only what's missing.

**Node.js 22+**
- Windows: `winget install OpenJS.NodeJS.LTS`
- macOS: `brew install node`
- Linux: use the distro's package manager or nodesource. Check with `node -v`.

**FFmpeg**
- Windows: `winget install Gyan.FFmpeg` (restart the terminal afterwards so PATH updates)
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg` (or the distro equivalent)

**Python packages** (only those preflight reports missing):
```
python -m pip install -r "<skill>/scripts/requirements.txt"
```

**HyperFrames skills**: HyperFrames asks agents **not** to install its skills themselves, so give the user the command and let them run it:
- Claude Code plugin: `claude plugin marketplace add heygen-com/hyperframes` then `claude plugin install hyperframes@hyperframes`
- Standalone: `npx hyperframes skills update` (installs or refreshes the core set). `npx skills add heygen-com/hyperframes` also works.
- New skills load in a **new session**. If preflight can't find them but the host lists `/hyperframes` among its available skills, treat them as installed.

**HyperFrames CLI**: runs through `npx hyperframes …`. No global install needed; the first run downloads it. Each project pins an exact version in its `package.json` (this skill was tested with 0.9.23). To move up, run `npx hyperframes@latest upgrade --project . --check` first.

**Chrome for rendering**: HyperFrames downloads `chrome-headless-shell` on first render (`npx hyperframes browser ensure`). If that download is blocked, point it at an installed Chrome/Chromium with the `HYPERFRAMES_BROWSER_PATH` environment variable. `npx hyperframes doctor` shows what it found.

**Project libraries**: compositions load GSAP and Three.js from the project's `node_modules` (no CDN at render time). `python "<skill>/scripts/new_project.py" ... --install` runs `npm install` for them. Ask first; it downloads from npm.

**Playwright Chromium** (screenshots): `npx playwright install chromium`

**rembg** (optional): `python -m pip install rembg`. Its first run downloads a model (~170 MB), so mention that before installing.

## 4. Smoke test
After installing, scaffold a throwaway project and render it:
```
python "<skill>/scripts/new_project.py" --name smoke-test --format 16:9 --duration 6 --install
cd smoke-test/composition && npm run check && npx hyperframes render -q draft -o ../renders/previews/smoke.mp4
``` Delete nothing the user owns. If it fails, hand the error to `/hyperframes-cli` and report plainly.

## Notes
- Never change system-wide settings or shared environments without asking.
- Never store API keys in project files that could be shared. Use environment variables (e.g. `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY`).
- Windows: prefer PowerShell. Quote every path. `python` may be `py`.
