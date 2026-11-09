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

## How users get notified
`skills/motion-studio/scripts/update_check.py` reads the GitHub **Releases** of robin3317/motion-studio (pre-releases included) and compares the newest tag with the installed `metadata.version` in SKILL.md. So every release needs:
- a **tag in the form vX.Y.Z[-pre]** that is higher than the last one (e.g. v0.1.0-beta → v0.2.0-beta → v1.0.0)
- a **published GitHub Release** for that tag (`gh release create …`). Tags alone and drafts are ignored
- `metadata.version` in BOTH skills' SKILL.md and `version` in `.claude-plugin/plugin.json` set to the same number
Write good release notes: the upgrade skill summarises them for users.
