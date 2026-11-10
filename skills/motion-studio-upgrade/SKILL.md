---
name: motion-studio-upgrade
description: Upgrades the motion-studio video skill to its latest release and shows what changed. Use when the user says "upgrade motion-studio", "update motion-studio" or "motion-studio-upgrade", or accepts the upgrade offer motion-studio shows when a new version is out.
license: MIT
metadata:
  author: robin3317
  version: 0.2.1-beta
---

# Upgrade motion-studio

The check script lives in the main skill: `<skills>/motion-studio/scripts/update_check.py`, where `<skills>` is the folder that contains this skill's folder. Quote the path. Use `python`, `python3` or `py`, whichever exists.

## 1. Check
Run `python "<skills>/motion-studio/scripts/update_check.py" --force`.
- `UP_TO_DATE x`: tell the user they have the latest version (x) and stop.
- `UPDATE_AVAILABLE <local> <latest> <method>`: continue.
- `CHECK_FAILED <why>`: neither GitHub source could be reached from here (the line says why). If the session runs in a cloud sandbox and the user's computer is linked, run the same command on their computer. Otherwise say so and give the releases page https://github.com/robin3317/motion-studio/releases. Stop.

## 2. Show what's new
Run `python "<skills>/motion-studio/scripts/update_check.py" --notes`. It prints the changelog entries that are newer than the installed version. Summarise them in 3–5 bullets. If it prints `NOTES_UNAVAILABLE`, open the `NOTES:` URL instead, or skip this step.

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
