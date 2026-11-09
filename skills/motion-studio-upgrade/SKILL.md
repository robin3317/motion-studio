---
name: motion-studio-upgrade
description: Upgrades the motion-studio video skill to its latest release and shows what changed. Use when the user says "upgrade motion-studio", "update motion-studio" or "motion-studio-upgrade", or accepts the upgrade offer motion-studio shows when a new version is out.
license: MIT
metadata:
  author: robin3317
  version: 0.1.0-beta
---

# Upgrade motion-studio

The check script lives in the main skill: `<skills>/motion-studio/scripts/update_check.py`, where `<skills>` is the folder that contains this skill's folder. Quote the path. Use `python`, `python3` or `py`, whichever exists.

## 1. Check
Run `python "<skills>/motion-studio/scripts/update_check.py" --force`.
- `UP_TO_DATE x`: tell the user they have the latest version (x) and stop.
- No output: GitHub couldn't be reached. Say so, and give the releases page https://github.com/robin3317/motion-studio/releases. Stop.
- `UPDATE_AVAILABLE <local> <latest> <method>`: continue.

## 2. Show what's new
Open the `NOTES:` URL (the GitHub release page) and summarise the changes in 3–5 bullets. If it can't be fetched, skip this step.

## 3. Upgrade by install method
Ask once: "Upgrade motion-studio from <local> to <latest> now?" Run the commands only after the user says yes.

| method | What to do |
|---|---|
| `plugin` | Run `claude plugin marketplace update codeonces`, then `claude plugin update motion-studio@codeonces`. Then tell the user to run `/reload-plugins` (or start a new session). |
| `git` | Run the `COMMAND:` line (`git -C "<repo>" pull --ff-only`). If it fails because of local edits, show `git status` and ask before doing anything else. Never reset or discard their changes. |
| `skills-cli` | Run `npx skills add robin3317/motion-studio` and follow its prompts. |
| `zip` | You can't replace an uploaded skill yourself. Give the steps: download `motion-studio-skill-v<latest>.zip` from the release page, then **Settings → Capabilities → Skills**, remove the old motion-studio, and upload the new ZIP. |

## 4. Confirm
Run the check again with `--force`. It should print `UP_TO_DATE <latest>` (plugin installs may need the reload first). Then run `python "<skills>/motion-studio/scripts/update_check.py" --reset` so the reminder state starts fresh.

## Other requests
- "Remind me later" → `--snooze 1d`. "Not this week" → `--snooze 7d`. "Stop asking" → `--never` (undo with `--reset`).
- Users can also turn checks off entirely with the environment variable `MOTION_STUDIO_NO_UPDATE_CHECK=1`.
