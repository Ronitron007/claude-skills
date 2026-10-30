#!/usr/bin/env bash
# Skill sync hook: on session end (Claude Code SessionEnd, Cursor stop/sessionEnd) or an mr run,
# check cheaply whether skills changed here; if so, start a detached `sync.sh --record`, which
# commits to the sync branch and opens/updates a PR. Never touches main, never calls a model.
# Contract: no stdout, always exit 0, ~20 ms when nothing changed. Safe to fire twice.
set -u
cat >/dev/null 2>&1 || true                       # drain hook JSON; we do not need it
[ "${SKILL_SYNC_DISABLE:-0}" = 1 ] && exit 0
REPO="${SKILLS_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/skill-sync"
mkdir -p "$STATE" 2>/dev/null || exit 0
# Inside an mr child (runners.child_env points push URLs at file:///nonexistent) a push would
# fail: only mark pending; mr's parent process calls this hook again after the run.
case "${GIT_CONFIG_KEY_0:-}" in *pushInsteadOf*) touch "$STATE/pending"; exit 0;; esac

# dirty check: real folders/files dropped into ~/.claude (new skill, npx install), edits in the
# clone, or an earlier record that did not finish
dirty=
[ -f "$STATE/pending" ] && dirty=1
[ -z "$dirty" ] && [ -n "$(find ~/.claude/skills -mindepth 1 -maxdepth 1 -type d ! -name '.*' 2>/dev/null | head -1)" ] && dirty=1
[ -z "$dirty" ] && [ -n "$(find ~/.claude/commands -mindepth 1 -maxdepth 1 -type f -name '*.md' 2>/dev/null | head -1)" ] && dirty=1
[ -z "$dirty" ] && [ -n "$(git -C "$REPO" status --porcelain 2>/dev/null | head -1)" ] && dirty=1
[ -z "$dirty" ] && exit 0
touch "$STATE/pending"

# detach: `claude -p` kills hook children (even async ones) at exit, so leave its session
setsid nohup bash -c '
  sleep "${SKILL_SYNC_DEBOUNCE:-15}"                       # let a burst of session ends settle
  echo "== $(date -Iseconds) record" >>"$1/sync.log"
  timeout 300 "$2/sync.sh" --record >>"$1/sync.log" 2>&1 && rm -f "$1/pending"
' _ "$STATE" "$REPO" </dev/null >/dev/null 2>&1 &
exit 0
