---
name: paxel-remote-setup
description: Set up Paxel transcript capture for remote dev boxes. Adds one line to whatever provisions the user's boxes (a dotfiles install script, a devcontainer postCreateCommand, cloud-init runcmd, a box image entrypoint, the app code that creates sandboxes, or a T3 Code or Conductor setup script) so every box copies its Claude Code and Codex sessions, with known credential formats removed, into a private paxel-transcripts repo the user owns, and the Paxel upload on the user's main machine includes them. Use when the user asks to set up Paxel on remote boxes, capture remote or devbox agent sessions for Paxel, or enable the Paxel transcript store.
---

# Paxel setup for remote boxes

Paxel reports cover the agent sessions on the machine that runs the upload. Sessions on remote dev boxes are missed. This skill fixes that with one line in whatever provisions the boxes:

```sh
curl -fsSL https://paxel.ycombinator.com/paxel.sh | bash -s -- setup
```

On each box, `setup` registers Claude Code and Codex hooks. After each agent turn, the box copies new session lines, with known credential formats removed, plus git history snapshots, into a private repo the user owns: `<login>/paxel-transcripts` on GitHub or GitLab, found through the box's logged-in `gh` or `glab`, or, on a box with a git login but no `gh` or `glab`, named with `PAXEL_STORE` on the setup line. This skill recommends creating that repo from the main machine first; otherwise setup creates it on a box with `gh` or `glab`. Paxel never reads the repo and holds no credential for it. The normal Paxel upload on the user's main machine (the machine that runs the upload: a laptop, a desktop or a dev box) pulls it.

Setup is safe to rerun, never prompts without a terminal, and always exits 0.

## Checklist

Start your first reply with this sentence: "Remote-box capture is in alpha, so it may change." Then copy this checklist into it, inside a code block. Tick each item when it is done. Do not skip ahead.

```
Paxel setup (alpha)
- [ ] Step 1. Ask: is this machine a remote box or the main machine
- [ ] Step 2. Ask how much history the first push copies: recent, all or nothing old (remote box only)
- [ ] Step 3. Find your box setup (what sets up a new box)
- [ ] Step 4. Offer to create the store now (recommended) or later (main machine only)
- [ ] Step 5. Ask how long the boxes live, show the change and get approval
- [ ] Step 6. Update your box setup to install Paxel
- [ ] Step 7. Run setup on this box (remote box only)
- [ ] Step 8. Check with paxel status --json (remote box only)
- [ ] Step 9. Run the first push with paxel push --now (remote box only; skip for "nothing old")
- [ ] Step 10. Send the final message with the next steps
```

After step 1 you copy a shorter checklist with only this machine's steps (step 1).

## 1. Ask where you are running

Ask the user: "Is this machine a remote box whose agent sessions you want in Paxel, or your main machine, the one where you run the Paxel upload?" Do not guess from the hostname or OS: a main machine can be a laptop, a desktop or a dev box, and can run Linux.

- **Remote box:** do every step except step 4.
- **Main machine:** offer to create the store (step 4, recommended), then edit the provisioning file. Never run `setup` on the main machine: it would copy its whole agent history into the store, and its upload already reads its local sessions. Steps 2, 7, 8 and 9 do not apply.

Then, before you do anything else, copy the checklist for this machine into your reply, inside a code block, with step 1 ticked. Keep the step numbers, so they match the steps below.

On a remote box:

```
Paxel setup (alpha, remote box)
- [x] Step 1. This machine: remote box
- [ ] Step 2. Ask how much history the first push copies: recent, all or nothing old
- [ ] Step 3. Find your box setup (what sets up a new box)
- [ ] Step 5. Ask how long the boxes live, show the change and get approval
- [ ] Step 6. Update your box setup to install Paxel
- [ ] Step 7. Run setup on this box
- [ ] Step 8. Check with paxel status --json
- [ ] Step 9. Run the first push with paxel push --now (skip for "nothing old")
- [ ] Step 10. Send the final message with the next steps
```

On the main machine:

```
Paxel setup (alpha, main machine)
- [x] Step 1. This machine: main machine
- [ ] Step 3. Find your box setup (what sets up a new box)
- [ ] Step 4. Offer to create the store now (recommended) or later
- [ ] Step 5. Ask how long the boxes live, show the change and get approval
- [ ] Step 6. Update your box setup to install Paxel
- [ ] Step 10. Send the final message with the next steps
```

## 2. Ask about the first push (remote box only)

Ask the user this one question, with these three answers, and wait for the answer:

"What should the first push from this box copy to your store?
1. Recent sessions only (last 7 days — quick to test)
2. All history (can take a long time)
3. Nothing old (only sessions active from now on, this one included)"

The answer sets the `--since` flag of the setup line you run in step 7:

| Answer | Flag |
|---|---|
| Recent sessions only | `--since 7d` |
| All history | `--since all` |
| Nothing old | `--since none` |

A session counts when it was active in that window, and then all of it is copied. With "nothing old", only sessions active after setup are copied, in full, this one included. The choice holds for this box, and a later setup run without `--since` keeps it. The provisioning line you add in step 6 has no `--since`, so a new box copies its full history, which is usually small. To add the older sessions later: `~/.paxel/bin/paxel setup --since all`.

## 3. Find the provisioning entry point

Find what sets up the user's boxes. Search and read only; run nothing. Search the repo the user names, `~/dotfiles`, `~/.dotfiles` and the current repo for the patterns below. `LINE` stands for the setup line at the top of this file, adapted in step 5. When the boxes are a platform under "Not supported today" (end of this step), stop there.

**Dotfiles.** Codespaces, Coder, DevPod and Ona run the first of `install.sh`, `install`, `bootstrap.sh`, `bootstrap`, `setup.sh`, `setup` (some also look under `script/`) from the user's dotfiles repo on each new box. Dotfiles also run on the main machine, so the line always gets a host guard (step 5).

| Manager | Look for | Where the line goes |
|---|---|---|
| Install script | one of the files above | the end of that file |
| chezmoi | `.chezmoiscripts/`, `run_once_`, `.chezmoi.toml.tmpl` | a new `run_once_after_paxel.sh` (in a `.tmpl`, write the URL out in full) |
| yadm | `.config/yadm/bootstrap` | the end of `bootstrap` |
| Dotbot | `install.conf.yaml` | a `- shell:` entry with `stdout: true` and `stderr: true` |
| rcm | `hooks/post-up` | the end of `post-up` |
| GNU Stow | `.stowrc`, `stow` in `install.sh` or a `Makefile` | the script that calls `stow`, after the `stow` calls |
| Nix home-manager | `home.nix`, `home.activation`, `homeConfigurations` | `home.activation.paxelSetup = lib.hm.dag.entryAfter [ "writeBoundary" ]`, calling `${pkgs.curl}/bin/curl` and `${pkgs.bash}/bin/bash` (activation runs with a short PATH). With `programs.claude-code` or `programs.codex`, the settings files are read-only links: step 8 |
| Ansible | `ansible.cfg`, `playbook.yml`, `roles/*/tasks/main.yml` | an `ansible.builtin.shell` task after the task that logs in `gh` or `glab` or installs the SSH key, with `become_user` set to the agents' account |

**Dev containers and cloud dev environments**

| Platform | Look for | Where the line goes |
|---|---|---|
| Dev container | `.devcontainer/devcontainer.json`, `.devcontainer.json` | `postCreateCommand` (step 5). Every contributor shares this file: when the user has a dotfiles repo, prefer it |
| GitHub Codespaces | `"codespaces"` in `devcontainer.json`, `CODESPACES` in dotfiles | the dotfiles install script, with the `CODESPACES` guard. Needs a token (step 5) |
| DevPod | `devpod up`, `DOTFILES_URL` | the dotfiles install script (`DEVPOD` guard), or `postCreateCommand` |
| Ona (Gitpod) | `.ona/config.yaml`, `.ona/automations.yaml`, `.gitpod/automations.yaml`, each also as `.yml` (Ona reads only the first that exists, in this order, each `.yaml` before its `.yml`: edit that one) | a task under `tasks:` with `command: LINE` and `triggeredBy: [postDevcontainerStart]` |
| Coder | `resource "coder_agent"`, `coder_script`, `startup_script` | a `coder_script` with `run_on_start = true`, or the end of `startup_script`. Without template rights: `~/personalize`, or dotfiles with the `CODER` guard |
| Google Cloud Workstations | `/etc/workstation-startup.d/` in the image's Dockerfile | a new `/etc/workstation-startup.d/250_paxel-setup.sh` in the image (runs as root: `--user user`) |
| Google Cloud Shell | `~/.customize_environment` | no file: the home persists, so treat Cloud Shell as a remote box and run setup there once |
| Docker Sandboxes | `sbxenv.yaml` | `lifecycle.postCreate`: `sbx exec "$SBX_SANDBOX_NAME" sh -c 'LINE'` (it runs on the host, so it execs into the sandbox) |

**VMs, containers and infrastructure**

| Platform | Look for | Where the line goes |
|---|---|---|
| cloud-init | `#cloud-config` with `runcmd:` (EC2 or launch template user data, Azure custom data, Hetzner or DigitalOcean user data) | the last `runcmd` item: `- [ sh, -c, "LINE" ]` (root: `--user`) |
| GCP startup script | `metadata_startup_script`, `startup-script` | the end of the script (root, every boot: `--user`) |
| Terraform, Pulumi | `user_data`, `custom_data`, `metadata_startup_script`, `templatefile(` | inside the cloud-init or startup script they carry; in `templatefile`, `${...}` becomes `$${...}` |
| Packer, image builds | `*.pkr.hcl`, `provisioner "shell"`, a Dockerfile `RUN`, an SDK image or template definition | not there: a build has no git credential. Use launch-time user data, the entrypoint, or a per-boot script the image ships (`/var/lib/cloud/scripts/per-boot/50-paxel.sh`) |
| Vagrant | `config.vm.provision "shell"` | a provisioner with `privileged: false` (a privileged one runs as root: `--user vagrant`) |
| Lima, Colima | `provision:` in `lima.yaml` or `colima.yaml` | a `mode: user` entry |
| systemd | `Type=oneshot` units, `systemd.services.` in Nix | `ExecStart=/bin/sh -c 'LINE'` with `User=` set to the agents' account, after `network-online.target` |
| Image entrypoint, Fly.io Machines | `ENTRYPOINT`, `docker-entrypoint.sh`, `fly.toml` | the entrypoint script, before `exec "$@"` (root: `--user`). Not Fly's `release_command`, which runs on a throwaway Machine |
| docker compose | `compose.yaml`, `docker-compose.yml`, `post_start:` | `post_start: - command: sh -c 'LINE'` (Compose 2.30 or later) |
| Kubernetes | `lifecycle:`, `postStart:` in a pod spec or Helm values | `lifecycle.postStart.exec.command: ["/bin/sh", "-c", "LINE"]`. Not an `initContainer`, which is a separate container |

**SDK sandboxes.** The line goes in the app code that creates each sandbox, right after the create call, run as a command in the sandbox. Not in the sandbox's image or template, which is built with no credential.

| SDK | Look for | Run `LINE` after the create call |
|---|---|---|
| Vercel Sandbox | `@vercel/sandbox`, `Sandbox.create(`, `Sandbox.getOrCreate(` | in `onCreate`, or after create: `await sandbox.runCommand('bash', ['-lc', 'LINE'])` |
| E2B | `e2b`, `Sandbox.create(` | `await sandbox.commands.run('LINE', { timeoutMs: 300_000 })` (the 60 s default is too short) |
| Modal | `modal.Sandbox.create(` | `sb.exec('bash', '-lc', 'LINE').wait()`, with `--user root` |
| Daytona | `daytona.create(`, `@daytona/sdk` | Python `sandbox.process.exec('LINE')`, TypeScript `await sandbox.process.executeCommand('LINE')` |
| Runloop | `devbox.create(`, `launch_parameters` | add `'LINE'` to `launch_parameters.launch_commands` |
| Upstash Box | `@upstash/box`, `Box.create(` | `initCommand: 'LINE'` |
| Blaxel | `SandboxInstance.create(`, `createIfNotExists(` | `await sandbox.process.exec({ command: "bash -lc 'LINE'", waitForCompletion: true })`, with `--user root` |
| Freestyle | `freestyle.vms.create(` | `await vm.exec('LINE')` |
| Northflank | `@northflank/js-client`, `create.service.deployment(` | an exec session (`execServiceSession`) once the service runs, with `--user root` |
| Morph | `morphcloud`, `instances.start(` | `instance.exec('LINE')` |

**Agent apps and boxes with no provisioning file**

| Platform | Look for | Where the line goes |
|---|---|---|
| Conductor | `.conductor/settings.toml` (`[scripts] setup`), legacy `conductor.json` | Local workspaces run on the Mac, usually the main machine: no line there. Cloud workspaces run the organization's Cloud Computer setup script, kept in Conductor's settings: give the user the line to paste there, or add it to a committed script both setups call, with the `CONDUCTOR_IS_LOCAL` guard |
| T3 Code | `~/.t3/` | Its setup script lives in T3's project settings, not in a file: prefer the host's own provisioning (dotfiles, cloud-init). Otherwise give the user the line, with a host guard, to paste there |
| Persistent boxes: Fly.io Sprites, exe.dev, Namespace devboxes, Daytona sandboxes used over SSH, NVIDIA Brev | `sprite`, `exe.dev`, `devbox`, `daytona ssh`, `brev` | Nothing to edit: run the setup line once on each box, after `gh auth login` there. Running this skill on the box does that (steps 7 to 9) |

Stop and ask the user when:

- you find more than one candidate: list each path and what it runs, and ask which one provisions the boxes;
- you find none: ask where their boxes are set up. When `~/dotfiles`, `~/.dotfiles` or the repo the user named holds scripts that are not in the tables above, name them in the question ("~/dotfiles has box-setup.sh and links.sh. Does one of them set up your boxes?");
- the only candidate runs at image build time (a Dockerfile `RUN`, Packer, an SDK image definition): no box and no git credential exist yet. Ask for a step that runs when the box starts.

**Not supported today.** For these, edit nothing: end with Blocked (step 10), with the reason below.

| Platform | Why |
|---|---|
| Claude Code on the web | cloud sessions do not run hooks from the user's settings, and their GitHub access covers only the session's repos |
| OpenAI Codex cloud | its VMs have no documented session files, hooks or git credential |
| Cursor cloud agents | they run Cursor's own agent, so there are no Claude Code or Codex sessions |
| GitHub Copilot cloud agent | the runner is gone before the push starts, and its token reaches only that repo |
| Google Jules | it runs Google's own agent, so there are no Claude Code or Codex sessions |
| Devin | it runs Cognition's own agent, so there are no Claude Code or Codex sessions |
| Factory remote workspaces | they run Droid, so there are no Claude Code or Codex sessions |
| Cloudflare Sandbox reference runners | they save no sessions (`--no-session-persistence`, `codex exec --ephemeral`) and keep git credentials out of the container |
| Claude Code self-hosted runners | each session uses its own `CLAUDE_CONFIG_DIR`, which Paxel does not read |
| Daytona tier 1 and 2 organizations | their sandboxes cannot reach the Paxel host |

## 4. Offer to create the store (main machine only)

Skip this step on a remote box: setup creates the store there, unless the box has no `gh` or `glab` login (step 5).

First find the login, with the CLI only and without printing a token: `gh api user --jq .login` for GitHub (`<host>` is `github.com`); when `gh` is not logged in, the `username` field of `glab api user` for GitLab (`<host>` is the host `glab auth status` names, usually `gitlab.com`). When neither is logged in and the boxes have no `gh` or `glab` login either (step 5), ask the user to log in here with `gh auth login` (or `glab auth login`), as the account that should own the store, then find the login again: only a `gh` or `glab` login can create the store. When neither is logged in otherwise, do not ask: the first box's setup creates the store, and the final message uses the no-login Store line and Upload lines (step 10). Otherwise ask the user this one question, with these two answers, and wait for the answer:

"Create your private store now? It will be <login>/paxel-transcripts on <host> (via <gh|glab> as <login>).
1. Yes (recommended)
2. No"

Yes is recommended: the store then exists before the first box starts, so no box needs a login that can create repos. Boxes with no `gh` or `glab` login (step 5) cannot create it at all.

- **Yes:** run
  ```sh
  curl -fsSL https://paxel.ycombinator.com/paxel.sh | bash -s -- --create-store --yes
  ```
  It creates the private repo and seeds it, or finds the one that exists (and finishes seeding it when an earlier run stopped). It writes no hooks or skill on this machine and pushes nothing. With `PAXEL_STORE` it saves that store in this machine's `~/.paxel/config`, so the usual upload finds it; without, it clears a store saved there before.
- **The user names another store:** set it as `PAXEL_STORE` on the `bash` side (`curl -fsSL https://paxel.ycombinator.com/paxel.sh | PAXEL_STORE=github.com/acme/paxel-transcripts bash -s -- --create-store --yes`), and use the same `PAXEL_STORE` on the provisioning line in step 5. That run saves the store here, so this machine's uploads need no `PAXEL_STORE`.
- **No:** create nothing.

What the command printed decides the `Store:` line of the final message:

| It printed | Then |
|---|---|
| `Created private store: <link>` or `Store already exists: <link>` | `Store: <link> (private)` |
| a line that starts with `REFUSED:` (the repo is not private, or holds files Paxel did not write) | End with Blocked (REFUSED, step 10). Do not change the repo or its visibility. |
| any other line, and a non-zero exit | Go on to step 5. `Store: https://<host>/<login>/paxel-transcripts (not created: <that line>; the first box's setup tries again)` |
| none of these, and exit 0 | The download failed: go on as in the row above, with the line curl printed. |
| nothing: the user said No | `Store: https://<host>/<login>/paxel-transcripts (not created yet: the first box's setup creates it)` |

Boxes with no `gh` or `glab` login (step 5) cannot create the store: for them, end each `not created` value with `your boxes cannot create it: run <the step 4 command> here, and their next push after an agent turn finds it` instead of the part about the first box's setup.

When the user named no other store and step 4 created none (No, a failure, or no login here), read this machine's `~/.paxel/config`. When its `store_host`, `store_owner` and `store_name` lines name a store other than `<host>/<login>/paxel-transcripts`, the upload here reads that saved store, not the one the boxes would use. Use it: put it as `PAXEL_STORE` on the provisioning line (step 5), and end with `Store: https://<host>/<owner>/<name> (saved on this machine)`.

## 5. Show the change and get approval

Start from the line at the top of this file and apply each row that fits the entry point:

| Case | Change |
|---|---|
| **Runs as root**: cloud-init `runcmd`, GCP startup scripts, `/etc/workstation-startup.d`, `~/.customize_environment`, image entrypoints, root systemd units, a privileged Vagrant provisioner, a dev container whose user is root | Add `--user <account>`, the account the agents run as (Ubuntu images: often `ubuntu`; Cloud Workstations: `user`). Ask the user if the file does not show it. When the agents also run as root (Modal, Cloudflare, Fly.io Machines, Blaxel, Northflank, most Kubernetes images), use `--user root`. Under `sudo`, setup finds the invoking user itself. |
| **Git credential** | The box needs `gh` or `glab` logged in on disk, `GH_TOKEN` in the environment the agents run with, not only in the setup command's (pushes start from the agents' hooks), or a git login of its own with `PAXEL_STORE` (next row). SDK sandboxes: put `GH_TOKEN` in the create-level environment (`env`, `envs`, `envVars`, `env_vars` or an attached secret), not in one command's. Daytona, exe.dev and Sprites have no git login by default: a user secret `GH_TOKEN`, or `gh auth login` once where the home persists. Put the line after any step that logs in `gh` or `glab` or installs the SSH key. A box with no login yet still gets the hooks: after a later login, push looks for the store again within the hour. |
| **A git login but no `gh` or `glab`**: Coder, Ona (Gitpod), DevPod, or this remote box when `gh api user` and `glab api user` find no login | Setup then uses the box's own git login (a credential helper, Coder's `GIT_ASKPASS` and `coder gitssh`, an SSH agent or key), only for a store the line names, and cannot create the store. Add `PAXEL_STORE=<host>/<owner>/<name>` on the `bash` side. On the main machine, use the store step 4 printed, which then exists before the boxes start; when it printed none, the store the user named there or the saved store step 4 found, else `<host>/<login>/paxel-transcripts` with the host and login from step 4. On a remote box, ask the user for the store as `<host>/<owner>/<name>` (usually `github.com/<login>/paxel-transcripts`); a box with no git login of its own needs `gh auth login` here instead (`glab auth login` for a GitLab store). A user secret `GH_TOKEN` also works, as above. DevPod's login reaches the box only while it is connected (the IDE or `devpod ssh`). |
| **GitHub Codespaces** | The codespace's own token reaches only its repo, so it cannot see or push the store. Create the store from the main machine first (step 4; from a codespace, ask the user to run the step 4 `--create-store` command on the main machine), and have the user add a Codespaces user secret named `GH_TOKEN`: a fine-grained token with Contents read and write on `<login>/paxel-transcripts`, available to the repos their codespaces start from. |
| **Egress allowlist** (E2B, Modal, Vercel `networkPolicy`, Freestyle, Namespace, Docker Sandboxes, Kubernetes egress rules, a firewall script such as `init-firewall.sh`) | Allow the host of https://paxel.ycombinator.com, `github.com` and `api.github.com` (for GitLab, its host). When the image has no jq 1.6 or later, setup downloads jq from a GitHub release: also allow `github.com` and `release-assets.githubusercontent.com` (for a GitLab store too), or ship jq 1.6 or later in the image. |
| **Shared with the main machine**: dotfiles, Conductor or T3 setup scripts, anything that also runs there | Wrap the line in a host guard that is true on boxes and false on the main machine (guards below). |
| **`postCreateCommand`** | A string gets ` && <line>` appended. In an object, append ` && <line>` to the entry that logs in `gh` or `glab` or installs the SSH key: object entries run in parallel, so a separate `"paxel"` entry could run before that login. When no entry does that, stop and ask. An array (one command, no shell) cannot take a pipe: stop and ask. |
| **cloud-init** | Add the line as the last `runcmd` item. |
| **A store other than `<login>/paxel-transcripts`**, only when the user asks for one | Set `PAXEL_STORE` on the `bash` side of the pipe (below). For an organization store, tell the user that the organization's admins can read every transcript in it. |

End the line with `|| true` in a shell script with `set -e` or `pipefail`, in a Kubernetes `postStart` (a failing one kills the container), in a Nix activation, and anywhere a failing command stops the box from starting. Setup exits 0, but a failed download would otherwise stop the script.

Do not add a jq install before the line: on a box with no jq or one older than 1.6, setup downloads a pinned, checksummed jq into `~/.paxel/bin`. Only a box behind an egress allowlist needs more (the Egress allowlist row).

Host guards. Use the platform's variable; otherwise ask the user for a hostname pattern, or for a variable their box tooling sets (they can add one, such as `PAXEL_BOX=1`). Check `uname -s` only when the boxes and the main machine run different systems (for example Linux boxes and a Mac): when the main machine also runs Linux, that check is true there too.

| Platform | Guard |
|---|---|
| GitHub Codespaces | `[ "${CODESPACES:-}" = true ]` |
| Coder | `[ "${CODER:-}" = true ]` |
| Ona | `[ -n "${GITPOD_ENVIRONMENT_ID:-}" ]` |
| DevPod | `[ "${DEVPOD:-}" = true ]` |
| Google Cloud Shell | `[ "${CLOUD_SHELL:-}" = true ]` |
| E2B | `[ "${E2B_SANDBOX:-}" = true ]` |
| Modal | `[ -n "${MODAL_SANDBOX_ID:-}" ]` |
| Fly.io Machines | `[ -n "${FLY_MACHINE_ID:-}" ]` |
| Conductor cloud workspaces | `[ "${CONDUCTOR_IS_LOCAL:-1}" = 0 ]` |
| Kubernetes | `[ -n "${KUBERNETES_SERVICE_HOST:-}" ]` |

```sh
# Paxel transcript capture: remote boxes only
if [ "${CODESPACES:-}" = true ]; then curl -fsSL https://paxel.ycombinator.com/paxel.sh | bash -s -- setup || true; fi
```

```sh
# Paxel transcript capture: remote boxes only
case "$(uname -n)" in
  <box hostname pattern>) curl -fsSL https://paxel.ycombinator.com/paxel.sh | bash -s -- setup ;;
esac
```

```sh
curl -fsSL https://paxel.ycombinator.com/paxel.sh | bash -s -- setup --user ubuntu
```

```sh
curl -fsSL https://paxel.ycombinator.com/paxel.sh | PAXEL_STORE=github.com/acme/paxel-transcripts bash -s -- setup
```

**Short-lived boxes.** Ask the user once: "Are these boxes deleted within a few minutes after the agent's last turn (sandboxes, CI jobs, pods)?" When yes, also add this line where the box is torn down, run as the agents' account (from root: `sudo -u <account> -H ~<account>/.paxel/bin/paxel push --now || true`):

```sh
~/.paxel/bin/paxel push --now || true
```

| Platform | Teardown point |
|---|---|
| docker compose | `pre_stop` |
| Kubernetes | `lifecycle.preStop`, with a longer `terminationGracePeriodSeconds` (for example 120) |
| SDK sandboxes | in the app code, before `sandbox.stop()`, `kill()`, `terminate()` or `delete()`. That code runs outside the sandbox: run the line above in it with the same call as in step 3 |
| Coder | a `coder_script` with `run_on_stop = true` |
| Docker Sandboxes | `lifecycle.preRemove`, which runs on the host: `sbx exec "$SBX_SANDBOX_NAME" sh -c '<the line above>'` |
| CI | a last step with `if: always()` |

Then show the user, in one message:

1. the file path and the exact lines you will add, with the lines around them;
2. on a remote box: that you will then run setup on this box with the `--since` flag from step 2, check it, and run the first push (not for "nothing old");
3. that setup creates the private repo if it does not exist yet (a box with no `gh` or `glab` login cannot: the main machine creates it), and that the first push copies agent history, tool output included, with known credential formats removed (a credential in another format is copied and stays in the repo history) and the data of images pasted into a prompt, returned by a tool or generated by the agent replaced with `[image removed]` (an image inside other text, such as command output, is copied), plus git history: on this box, what the user chose in step 2; on each new box, its full history;
4. on a remote box: that capture starts within about a minute of setup. The hooks fire at the end of each agent turn, this one included, and the push starts about a minute later;
5. for short-lived boxes: the teardown line, and why: the push starts about a minute after the last agent turn, so a box deleted sooner loses its last sessions;
6. what the box still needs, from the rows above: a credential, a `GH_TOKEN` secret, the store created from the main machine, an egress rule.

Ask: "Apply this change?" Continue only on an explicit yes. If the user asks for a change, show the new version and ask again.

## 6. Edit the provisioning file

Make exactly the approved change and nothing else. Do not commit or push unless the user asks. If the file lives in a repo, tell the user that new boxes get the line only after it is pushed.

## 7. Run setup on this box (remote box only)

First check `id -u`, since it decides the flags:

- **Not 0:** drop any `--user`. Setup installs for the account you run as.
- **0 (you run as root):** setup installs nothing without `--user`. Keep the `--user` from the approved line, or add `--user <account>`: the account the agents on this box run as. When they run as root, as in many dev containers and cloud sandboxes, use `--user root`. Ask the user when you cannot tell.

Then run the approved line with those flags, adding `--yes` (you already asked about the store, so setup must not ask again) and the `--since` flag from step 2. Keep any `PAXEL_STORE`.

```sh
curl -fsSL https://paxel.ycombinator.com/paxel.sh | bash -s -- setup --yes --since 7d
```

Setup prints one line per item (created, updated or unchanged), the store, what the first push copies, and next steps. Read them. Capture is on from here: the hooks fire when this turn ends, and the push starts about a minute later. Codex sessions that were already running join after a restart; setup says so when that applies.

## 8. Check it (remote box only)

Run status as the account setup installed for. When that is you, or you ran `--user root` as root:

```sh
~/.paxel/bin/paxel status --json
```

When you run as root and passed `--user <account>` for another account, run it as that account (without `sudo`, use `su - <account> -c '~/.paxel/bin/paxel status --json'`):

```sh
sudo -u <account> -H ~<account>/.paxel/bin/paxel status --json
```

The command exits 0 when nothing needs action. Read the JSON: the store must be readable and writable (the write probe passed), private, and marked as a Paxel store; hooks must be registered for Claude Code and Codex; capture must not be off; `history.since` must be a time for "recent sessions only" or "nothing old", and null for "all history". On a box with no `gh` or `glab` login, status cannot check that the store is private (`private` is null) and push still stops on a public store: accept that, and in the final message write `private not checked from this box` in place of `private`.

When something needs action, use the next steps in the status output:

| Status shows | Then |
|---|---|
| `.paxel/bin/paxel` does not exist | Check that you ran it as the account setup installed for. If you ran setup as root without `--user`, it installed nothing: rerun step 7 with `--user <account>`, then run status as that account. |
| No readable store, on a box with no `gh` or `glab` login whose line names the store with `PAXEL_STORE` | Needs you, with the ending for a box with no `gh` or `glab` login (step 10): the user creates the store from the main machine, and this box's next push after an agent turn finds it. |
| No store yet: no `gh` or `glab` was logged in when setup ran, and the line names no `PAXEL_STORE` | Needs you: `gh auth login` (or `glab auth login`) as the agents' account. No setup rerun is needed: push looks for the store again within the hour. To check right away, rerun step 7 after the login. |
| The store is not readable or the write probe failed | Needs you, with the login or key command from the next steps (on Codespaces, the `GH_TOKEN` secret from step 5). After the user says it is done, rerun step 7. |
| Codex hook waiting for trust: only when setup could not chain the user's own `notify` (for example, `~/.codex/config.toml` is a symlink), so it used a `~/.codex/hooks.json` Stop hook | Needs you, on each new box: the user opens Codex on that box, runs `/hooks` and trusts the Paxel entry. Codex keeps that trust per box. A `notify` program the user already set needs no trust: setup chains it, so after each turn Codex runs Paxel's, which then runs theirs with the same input. |
| A settings file is a symlink or is not valid | Needs you: setup printed a snippet instead of editing it. The user adds that snippet to the file where it really lives (often a dotfiles repo or a Nix module). |
| Setup's jq item says `not installed`: the box has no jq 1.6 or later and setup could not download one (the download was blocked, or the platform has no jq build) | Needs you: install jq 1.6 or later (for example `sudo apt-get install -y jq`), or allow the download (egress allowlist, step 5). Then rerun step 7. |
| The store is public or internal | Blocked (not private). Pushes stay stopped until the repo is private. Do not change its visibility. |

You may rerun setup at most two more times, and only after something changed (a flag, or a step the user finished). Then end with Needs you or Blocked.

## 9. Run the first push (remote box only)

Skip this step when the user chose "Nothing old". Otherwise run it as the account setup installed for, as in step 8. When that is you, or you ran `--user root` as root:

```sh
~/.paxel/bin/paxel push --now
```

When you run as root and passed `--user <account>` for another account, run it as that account (without `sudo`, use `su - <account> -c '~/.paxel/bin/paxel push --now'`):

```sh
sudo -u <account> -H ~<account>/.paxel/bin/paxel push --now
```

It starts the push, or waits for one a hook already started, and prints what it wrote. Give it a time limit of 10 minutes, or your longest if that is shorter: all history can take longer (275 sessions took about 12 minutes on one box). If your command time limit stops it first, nothing is lost: the push resumes after this turn ends, and the step 8 command without `--json` shows its progress. Say so in the final message.

From its output, report:

- the sessions written: "Pushed <n> sessions to <store>.", or "Nothing new to push";
- what remains, when it prints any: files left out for their size, sessions whose credential scrub failed (each with its reason in brackets; push tries them again later), sessions the store host rejected, and the older sessions that stay on this box because of `--since` (it prints how many, and the command that adds them).

A result with sessions left over is not a failure. Report it, and do not rerun setup for it.

## 10. Final message

End with exactly one of these messages. Fill in the angle brackets and add nothing after it. Verified and Needs you end with the Upload lines. Blocked has none: nothing reaches the store until the block is cleared.

### Upload lines

`<where>` is `on your main machine` in Verified, `after that, on your main machine` in a remote box's Needs you, and `then, on this machine` in the main machine's Needs you.

```
Next steps: <where>, run your usual Paxel upload (the command on your Paxel dashboard, or this one). It pulls the store through the gh or glab login there:
  curl -fsSL https://paxel.ycombinator.com/upload.sh | bash
From inside a repo, the upload takes that repo's store sessions only. To take every repo's:
  curl -fsSL https://paxel.ycombinator.com/upload.sh | bash -s -- --all
When: box sessions reach the store about a minute after each agent turn and show up in your next upload from the main machine. Nothing uploads on its own.
```

For a store other than `<login>/paxel-transcripts` (`PAXEL_STORE`), the upload finds it once `--create-store` with that `PAXEL_STORE` has run on the main machine, which saves it there. When step 4 ran it on this machine and it printed the store, add nothing. Otherwise (a remote box, or a store created elsewhere), put this line before `Next steps:`, except in the ending for a box with no `gh` or `glab` login, whose Run line is that command:

```
Save the store on your main machine once, unless --create-store already ran there for it, so the usual upload finds it:
  curl -fsSL https://paxel.ycombinator.com/paxel.sh | PAXEL_STORE=<host>/<owner>/<name> bash -s -- --create-store --yes
```

On a main machine with no `gh` or `glab` login (step 4), put this line before `Next steps:`:

```
Before you upload: log in on this machine with gh auth login (or glab auth login), as the account your boxes use. Without a login, the upload does not look for the store.
```

On the main machine, run this check before you write the ending (a remote box needs no check):

```sh
curl -sS -o /dev/null -w '%{http_code}\n' https://paxel.ycombinator.com/geo_availability
```

When it prints `451`, put this line before `Next steps:` too. Any other answer (`204`, `000`, an error) adds nothing. The check never stops the setup: creating the store, the provisioning edit and the boxes' pushes do not need Paxel to be available on this network, only the upload does.

```
Region: the Paxel upload isn't available from this machine's network (HTTP 451, country or region), so it stops at sign-in here. Your boxes still push to the store; your report needs an upload from a network where Paxel is available.
```

### Verified

On a remote box:

```
Verified: Paxel capture is on for this box.
Store: https://<host>/<owner>/<name> (private)
Provisioning: <file> runs setup on new boxes.
Hooks: registered for Claude Code and Codex
First push: <what step 9 reported: sessions written and what remains | not run, as you chose: only sessions active from now on are copied>
Capture: on. New sessions reach the store about a minute after each agent turn ends. Progress: <the step 8 command without --json>
<the Upload lines>
```

### Needs you

On a remote box:

```
Needs you: <what is missing, in one line>
Run: <one exact command> (on this box)
Changed: <files changed, or nothing>
Store: <https://<host>/<owner>/<name> (private), as setup printed it | not created yet>
<the Upload lines>
```

On a remote box with no `gh` or `glab` login, when the store is not readable (step 8):

```
Needs you: create the store from your main machine; this box has no gh or glab login, so it cannot create it
Run: curl -fsSL https://paxel.ycombinator.com/paxel.sh | PAXEL_STORE=<host>/<owner>/<name> bash -s -- --create-store --yes (on your main machine)
Then: nothing on this box. Its next push after an agent turn finds the store, with no setup rerun; to push at once, run <the step 9 command>. If that push still cannot read the store, this box's git login cannot reach it: run gh auth login here (glab auth login for a GitLab store), then <the step 7 command>.
Changed: <files changed, or nothing>
Store: https://<host>/<owner>/<name> (not found from this box)
<the Upload lines>
```

On the main machine, after the edit, this is the ending:

```
Needs you: no remote box runs setup yet
Run: <file> again on each remote box, or start a new box from the updated script if your boxes are temporary
Changed: <file>
Store: <the Store value from step 4 | not created yet: the first box's setup creates paxel-transcripts under the gh or glab login that box uses>
<the Upload lines>
```

The second Store value is for a main machine with no `gh` or `glab` login.

### Blocked

```
Blocked: <what stopped the setup, in one line>
Stopped at: step <n> of the checklist
Changed: <files changed, or nothing>
```

| Cause | Blocked line | Also |
|---|---|---|
| A `REFUSED:` line (step 4) | `Blocked: <the REFUSED line, as printed>` | `Store: https://<host>/<owner>/<name>` after it |
| A store that is not private (step 8) | `Blocked: <host>/<owner>/<name> is not private, so pushes stay stopped until it is` | `Store: https://<host>/<owner>/<name>` after it |
| A platform under "Not supported today" (step 3) | `Blocked: <platform> is not supported today: <the reason from step 3>` | |

## Guardrails

- Never print, paste or log a credential: no `gh auth token`, no credential or `hosts.yml` files, no remote URLs that carry a token, no environment dumps. If a command prints one, do not repeat it.
- Never hand-edit agent settings files (`~/.claude/settings.json`, `~/.codex/config.toml`, `~/.codex/hooks.json`). Setup owns the Paxel entries in them.
- Never change a repository's visibility. Create the store only through `--create-store` (main machine, step 4) or setup (remote box), never with `gh` or `glab` directly: both create it private and check it.
- Never run `setup` on the main machine.
- No edits before the user approves, and only the approved change.
- At most two fix attempts after the first setup run.
- Ask the first-push question once, and never run setup without the `--since` it maps to.

## Turning it off

- One box: `~/.paxel/bin/paxel setup --off` removes the hooks, puts back the Codex `notify` line setup chained, and stops pushes. Running setup again turns capture back on.
- Everywhere: remove the line from provisioning, turn capture off on live boxes, then delete the repo. Credentials the scrub missed stay in the repo's history until the repo is deleted or its history is rewritten.
