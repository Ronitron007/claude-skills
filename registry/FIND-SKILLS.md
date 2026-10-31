# How to find skills for a task

Every bot follows this before starting a task (Rohan's standing rule points here).
Update this file when the method changes, for example when sk ships. Don't edit the memory rule.

## Current method (until sk ships)

1. Look in the single skills store: `/home/box/shared-skills` (a link to `/home/box/skills/view`,
   one folder per skill, resolved from the claude-skills repo).
2. Scan `/home/box/shared-skills/REGISTRY.md` and each skill's `SKILL.md` description for the task's
   keywords, for example `rg -il "<keyword>" /home/box/shared-skills/*/SKILL.md`.
3. Load and follow the skills that fit. Tell Rohan which skills you found and which you used.

Installing new skills from outside the store is a separate job, covered by SELECTION-METHOD.md.
