## Skills come from the claude-skills repo `skills.store`

- All global skills on this machine come from one public repo, https://github.com/Ronitron007/claude-skills. The clone on this machine is `{{REPO}}`.
- Before a task, find skills as `{{REPO}}/registry/FIND-SKILLS.md` says. Tell the user which skills you found and which you used.
- To add a skill that you write, create `~/.claude/skills/<name>/SKILL.md`. Do not put it in the clone by hand. The sync adds it to the repo.
  - On the main machine (the Mac), `export.py` exports it and pushes to `main`.
  - On other machines, `./sync.sh` commits it to a `sync/<host>` branch and opens a PR. Never push to `main` from there.
- To add a skill from a public repo, add an entry to `{{REPO}}/sources.json`. Do not copy the skill.
- Do not edit the generated files: `INDEX.md`, `manifest.json`, `restore.sh`. On the main machine, `export.py` also rebuilds `authored/` and `vendored/` from `~/.claude/skills`, so edit a skill there.
- The repo is public. Never put a key, a token, a password, or personal data in a skill.
- This block comes from `{{REPO}}/rules/agents.md`. Change that file, not this block. `rules.py` writes it again on the next sync.
