# Releasing (maintainer notes)

Run in PowerShell from `D:\self\claude\motion-studio`. Needs Git and the GitHub CLI (`winget install GitHub.cli`, then `gh auth login`).

## First release (v0.1.0-beta)
```powershell
git init
git add .
git commit -m "motion-studio v0.1.0-beta"
git branch -M main
gh repo create robin3317/motion-studio --public --source . --push --description "Claude skill that directs motion-graphics videos with HyperFrames"
git tag v0.1.0-beta
git push origin v0.1.0-beta
gh release create v0.1.0-beta dist\motion-studio-skill-v0.1.0-beta.zip dist\motion-studio-plugin-v0.1.0-beta.zip --prerelease --title "motion-studio v0.1.0-beta" --notes-file CHANGELOG.md
```
Without the GitHub CLI: create the repo on github.com, then run `git remote add origin https://github.com/robin3317/motion-studio.git` and `git push -u origin main`, and upload the two ZIPs under Releases → "Draft a new release" (tag `v0.1.0-beta`, tick "pre-release").

## Later releases
1. Bump the version in `.claude-plugin/plugin.json` and the SKILL.md `metadata.version`. Add a CHANGELOG entry.
2. Rebuild the ZIPs into `dist/` (skill ZIP = the `motion-studio/` folder; plugin ZIP = the repo without dist/, tests/renders/, docs/_references-bundle.md).
3. Commit, tag `vX.Y.Z`, push, then run `gh release create`.
Plugin users update with `/plugin marketplace update codeonces`.

### Example: v0.2.0-beta
```powershell
git add -A
git commit -m "motion-studio v0.2.0-beta"
git push origin main
git tag v0.2.0-beta
git push origin v0.2.0-beta
gh release create v0.2.0-beta dist\motion-studio-skill-v0.2.0-beta.zip dist\motion-studio-plugin-v0.2.0-beta.zip --prerelease --title "motion-studio v0.2.0-beta" --notes-file dist\release-notes-v0.2.0-beta.md
```

### Example: v0.2.1-beta
```powershell
python tests\test_update_check.py
python tests\regression.py
git add -A
git commit -m "motion-studio v0.2.1-beta"
git push origin main
git tag v0.2.1-beta
git push origin v0.2.1-beta
gh release create v0.2.1-beta dist\motion-studio-skill-v0.2.1-beta.zip dist\motion-studio-plugin-v0.2.1-beta.zip --prerelease --title "motion-studio v0.2.1-beta" --notes-file dist\release-notes-v0.2.1-beta.md
```

## How users get notified
`skills/motion-studio/scripts/update_check.py` compares the installed `metadata.version` in SKILL.md with the newest version it can find. It tries two sources, in order:
1. The GitHub **Releases** API of robin3317/motion-studio (pre-releases included).
2. `raw.githubusercontent.com/robin3317/motion-studio/main/.claude-plugin/plugin.json` (its `version` field). This is the fallback for sandboxes that block `api.github.com`, such as Claude Cowork's cloud. Release notes then come from `CHANGELOG.md` on `main` (`update_check.py --notes`).

So every release needs:
- a **tag in the form vX.Y.Z[-pre]** that is higher than the last one (e.g. v0.1.0-beta → v0.2.0-beta → v1.0.0)
- a **published GitHub Release** for that tag (`gh release create …`). Tags alone and drafts are ignored
- `metadata.version` in BOTH skills' SKILL.md and `version` in `.claude-plugin/plugin.json` set to the same number
- a `## X.Y.Z` section at the top of `CHANGELOG.md` (the upgrade skill summarises it for users)

**Release rule: the version on `main` changes only in the release commit.** Source 2 reads `plugin.json` from `main`, so bumping the version there before the release is published would tell users about a release that doesn't exist yet. Keep unreleased work under `## Unreleased` in the changelog and bump the three version fields in the same commit you tag.

Timing: a successful check is cached for 24 h per machine, so users can see a new release up to a day late. `python update_check.py --force` checks at once.

## Before each release: test the update check
```powershell
python tests\test_update_check.py
$env:MS_LIVE_TESTS = "1"; python tests\test_update_check.py
```
Run the live test on your machine **and** in a Claude Cowork cloud session (ask Claude to run it there). It must report a `source`: `releases` on a normal machine, `manifest` where the API is blocked. If both fail in the cloud, users there get no update popup.
