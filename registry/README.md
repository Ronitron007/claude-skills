# Shared skills (box view)

`/home/box/shared-skills` is a link to `/home/box/skills/view`. The real skills live in the
`claude-skills` repo clone at `/home/box/skills`, which is the only copy on this box.
`view/` holds one link per skill, plus these registry files. `link.py` rebuilds it, and `sync.sh` runs `link.py`.

- `REGISTRY.md`, `registry.json`, `SELECTION-METHOD.md`: the vetted list of public skill packs, with scores.
- `bin/log-skill-use.sh`: Claude Code hook that writes one line per skill use to `.usage.log`.
  The log is not committed, because the repo is public.

## Add a skill
- From a public repo: add it to `sources.json` with `source` and `skillPath`, then run `./sync.sh`.
- A skill you write: create `~/.claude/skills/<name>/SKILL.md`. The next `./sync.sh` moves it to
  `extra/skills/<name>`, adds it to `sources.json` and opens a PR.

Usage log line format: `ISO-timestamp<TAB>agent<TAB>skill-slug`. Agents other than Claude Code append by hand:

    printf '%s\t%s\t%s\n' "$(date -Iseconds)" cursor-agent expo-design-system >> /home/box/shared-skills/.usage.log
