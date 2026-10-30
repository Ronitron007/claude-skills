# claude-skills

This repo keeps an export of all global Claude Code skills from one machine. Clone it on a new machine, run one script, and the skills are ready to use.

The script `export.py` sorts each skill by its source. Then it copies the skill or records how to install it again.

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

## Automatic updates `readme.auto`

The script `install.sh` installs a launchd agent on macOS. The agent runs `export.py` when a skill folder, the lock file, or the plugin list changes. The agent also runs one time each hour. This catches edits inside a skill folder, because launchd does not watch subfolders.

Each run builds the generated files again. If no skill changed, the run makes no commit. If the repo has a remote, the script pushes the commit.

1. Run `./install.sh` to install or update the agent.

2. Run `./install.sh --uninstall` to remove the agent.

3. Read `.logs/export.log` to see the result of each run.

## Secret check `readme.secrets`

This repo is public. Each run checks for secrets before it makes a commit. The check has two parts:

1. A regex looks for API keys and private keys in each copied file.

2. If the machine has `gitleaks`, it scans the staged changes with `.gitleaks.toml`.

If a check finds a possible secret, the script makes no commit. It shows the file in `.logs/export.log` and shows a macOS notification. Remove the secret from the skill, and the next run continues.

The file `.gitleaks.toml` lists placeholder values from vendored docs, such as `YOUR_API_TOKEN`. Read a value before you add it to this list. Add it only if it is not a real key.
