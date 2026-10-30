# claude-skills

This repo keeps an export of all global Claude Code skills from one machine. Clone it on a new machine, run one script, and the skills are ready to use.

The script `export.py` sorts each skill by its source. Then it copies the skill or records how to install it again.

## How this works `readme.how`

This repo is the one source of truth for skills. Two kinds of machine use it:

| Machine | Its truth | Runs | Writes to GitHub |
|---|---|---|---|
| Main machine (the Mac) | `~/.claude` | `python3 export.py`, by hand | commits to `main` |
| Other machines (the box, others) | this clone | `./sync.sh`, by hand | a `sync/<host>` branch and a PR, never `main` |

On an other machine, `~/.claude/skills/<name>` and `~/.claude/commands/<file>` are links into the clone, so there is one copy to edit. Cursor also reads `~/.claude/skills`, so `link.py` puts no links in `~/.cursor/skills`. Cursor does not remove duplicates, so a link in both folders would show the skill twice.

`./sync.sh` does these steps:

1. It commits local edits to the `sync/<host>` branch.
2. It merges `origin/main`.
3. It runs `./restore.sh`.
4. It runs `link.py`. `link.py` moves real folders in `~/.claude/skills` into the clone, makes the links, and applies `fixes.json`.
5. It runs the host file `hosts/<host>.sh`, if there is one.
6. If the branch differs from `main`, it runs gitleaks, pushes the branch, and opens or updates the PR.

Where a skill folder lives in the clone (the first match wins): `extra/skills` (declared in `sources.json`), `installed/` (put there by `npx skills`, not committed), `vendored/skills`, `authored/skills`. `npx skills add` writes only to `~/.claude/skills`. This is why `restore.sh` can make a copy there, and the next `link.py` moves that copy to `installed/`. Run `./sync.sh` again at any time; each run gives the same result.

The two writers do not conflict:

- `export.py` on the main machine first runs `git pull --rebase` from `origin main`. It copies the merged changes to `authored/` and `vendored/` into `~/.claude`, then exports. So a merged sync PR is not undone, and the push is not rejected.
- `export.py` stops on a machine where `link.py` ran. Do not run it there.
- Merge sync PRs soon. Until you merge it, a PR that changes `authored/` or `vendored/` can conflict with the next export.
- No schedules. A full `./sync.sh` (pull, restore, link) runs only by hand. `install.sh` (below) is an optional launchd agent, and it runs only the Mac export.

### Hooks: record local changes when a session ends `readme.hooks`

`bin/install-hooks.sh` adds `bin/skill-sync-hook.sh` to Claude Code `SessionEnd` (`~/.claude/settings.json`) and to Cursor `stop` and `sessionEnd` (`~/.cursor/hooks.json`). Run it again at any time; each run gives the same result. `--uninstall` removes the hooks. mr calls the same hook at run start and after `_finalize`.

1. The hook does a dirty check, which takes about 15 ms. It looks for a real folder in `~/.claude/skills`, a real file in `~/.claude/commands`, a change in the clone, or an earlier record that did not finish. If it finds none, it stops.
2. If it finds a change, it starts `./sync.sh --record` in the background with `setsid`, because `claude -p` kills hook child processes when it exits.
3. `--record` runs `link.py` and commits to the sync branch. It then runs gitleaks, pushes and opens or updates the PR. It does not pull or run `restore.sh`.
4. The hook writes nothing to stdout and always exits 0, so it never blocks a session. It never calls a model and never runs `export.py`.
5. In an agent that mr starts, pushes are blocked. There the hook only marks the change as pending. mr's own process then records it.
6. A new `npx skills add` goes to `sources.json` (source + skillPath). This makes it reach GitHub and other machines.

Log: `~/.local/state/skill-sync/sync.log`. Turn the hook off for one command with `SKILL_SYNC_DISABLE=1`. To commit without a push, set `SYNC_NO_PUSH=1`. A `.sync-branch` file, which is not committed, sets the branch (for example the branch of an open PR). A full sync deletes the file after that PR is closed.

To add a skill from a public repo, add it to `sources.json` (`readme.sources`). To add a skill you write on an other machine, create `~/.claude/skills/<name>/SKILL.md` and run `./sync.sh`. On the main machine, create the skill as before; the export finds it.

`fixes.json` corrects frontmatter in each copy. It renames `user-invokable` to `user-invocable`, and it keeps `find-skills` slash-only.

## Use on a new machine `readme.restore`

You need `git` and Claude Code. You also need Node.js for the `npx` installs.

1. Clone this repo.

2. Run `./restore.sh` in the repo folder.

3. Start Claude Code.

The script works on macOS and Linux. You can run it again at any time. It does not delete files. If one install fails, the script shows a warning and continues. At the end, it shows the number of failed steps.

The script does these steps:

1. It copies the authored and vendored skills into `~/.claude/skills` and `~/.claude/commands`.

2. It adds the plugin marketplaces and installs the plugins.

3. It installs the `skills` CLI skills from GitHub.

4. It installs the claude.ai skills that Anthropic also publishes in `anthropics/skills`. It skips this step on a machine where the Claude desktop app syncs them.

## Classes `readme.classes`

| Class | Meaning | What the export keeps |
|---|---|---|
| authored | You wrote the skill. | A full copy in `authored/` |
| vendored | A third party wrote the skill. The export cannot install it again from its source. | A full copy in `vendored/` and a provenance file |
| cli | The `skills` CLI installed the skill, and the source still has it. | An `npx skills add` line in `restore.sh` |
| plugin | A Claude plugin supplies the skill. | A `claude plugin install` line in `restore.sh` |
| account | claude.ai syncs the skill to this machine. | An install line if `anthropics/skills` has it, else a row in `INDEX.md` |
| junk | The entry is not a valid skill. | A row in `INDEX.md` only |

## How the script finds the class `readme.rules`

The script applies these rules in this order. The first rule that matches sets the class.

1. If `overrides.json` names the skill, the script uses that class.

   Then, if `sources.json` names the skill, the script uses that entry. See `readme.sources`.

2. If the folder has no `SKILL.md`, the class is junk.

3. If `~/.agents/.skill-lock.json` has the skill, the class is cli. But if the GitHub source does not have the skill now, the class is vendored.

4. If the `SKILL.md` file is identical to a file in the plugin cache, the class is plugin.

5. If a plugin skill has the same name but different content, the class is vendored.

6. If the frontmatter has an `author` or a `license` field, the class is vendored.

7. If three or more skills have a `SKILL.md` time within two seconds, the class is vendored. One installer run makes this pattern. A person does not.

8. All other skills are authored.

The script also exports commands in `~/.claude/commands` as authored. Rule 7 is an inference. Each row in `INDEX.md` shows the evidence for its class.

The source check in rule 3 sends one request for each skill to GitHub. The script keeps the results for one day in `.cache/`.

## Fix a wrong class `readme.overrides`

1. Open `overrides.json`.

2. Add the skill name and the correct class, for example `{"supabase-edge-functions": "vendored"}`.

3. Run `python3 export.py`.

## Skills from other machines `readme.sources`

The export reads only the machine that runs it. To keep a skill that is on another machine, add it to `sources.json`. The script keeps each entry on every machine, also when the skill is not installed there.

1. For a skill with a public source, add the source and the path, for example `{"eas-update": {"source": "https://github.com/expo/skills.git", "skillPath": "plugins/expo/skills/eas-update/SKILL.md"}}`. The class is cli. `restore.sh` installs the skill with `npx skills add`.

2. For a skill without a source, put a copy in `extra/skills/<name>` and add `{"<name>": {"vendored_from": "<url>"}}`. The class is vendored.

3. Run `python3 export.py` on the main machine.

Do not run `export.py` on a second machine. It rebuilds the export from that machine only, so it removes the skills that are only on the main machine.

## Automatic updates `readme.auto`

The script `install.sh` installs a launchd agent on macOS. The agent runs `export.py` when a skill folder, the lock file, or the plugin list changes. The agent also runs one time each hour. This catches edits inside a skill folder, because launchd does not watch subfolders.

Each run first runs `git pull --rebase --autostash` from `origin main`, when the clone is on `main` and has a remote. It copies the merged skill changes into `~/.claude`, then builds the generated files again. So a PR merged from another machine does not make the push fail. If the pull fails, the run continues without it and logs a warning. Use `--no-pull` to skip it. If no skill changed, the run makes no commit. If the repo has a remote, the script pushes the commit.

1. Run `./install.sh` to install or update the agent.

2. Run `./install.sh --uninstall` to remove the agent.

3. Read `.logs/export.log` to see the result of each run.

## Secret check `readme.secrets`

This repo is public. Each run checks for secrets before it makes a commit. The check has two parts:

1. A regex looks for API keys and private keys in each copied file.

2. If the machine has `gitleaks`, it scans the staged changes with `.gitleaks.toml`.

If a check finds a possible secret, the script makes no commit. It shows the file in `.logs/export.log` and shows a macOS notification. Remove the secret from the skill, and the next run continues.

The file `.gitleaks.toml` lists placeholder values from vendored docs, such as `YOUR_API_TOKEN`. Read a value before you add it to this list. Add it only if it is not a real key.
