#!/usr/bin/env bash
# Skill sync hook: on session end (Claude Code SessionEnd, Cursor stop/sessionEnd) or an mr run,
# check cheaply whether skills changed here; if so, start a detached `sync.sh --record`, which
# commits to the sync branch and opens/updates a PR. Never touches main, never calls a model.
# Contract: no output, always exit 0, ~20 ms when nothing changed. Safe to fire twice.
# Off: SKILL_SYNC_DISABLE=1 (also SKILLSYNC_DISABLE=1), and in claude-limits probe sessions.
trap 'exit 0' EXIT                                     # whatever happens below, exit 0
exec 2>/dev/null
if [ ! -t 0 ]; then                                    # drain hook JSON (we do not need it), bounded
  if command -v timeout >/dev/null; then timeout 2 cat >/dev/null; else while IFS= read -r -t 2 _; do :; done; fi
fi
exec </dev/null >/dev/null
[ "${SKILL_SYNC_DISABLE:-0}" = 1 ] || [ "${SKILLSYNC_DISABLE:-0}" = 1 ] && exit 0
[ "${CLAUDE_LIMITS_PROBE:-0}" = 1 ] && exit 0          # usage probe: a one-word turn, no skill edits
HOME=${HOME:-$(getent passwd "$(id -u)" 2>/dev/null | cut -d: -f6)}
[ -n "$HOME" ] && [ -d "$HOME" ] || exit 0
REPO="${SKILLS_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/skill-sync"
mkdir -p "$STATE" || exit 0

# dirty check: real folders/files dropped into ~/.claude (new skill, npx install) or edits in the clone
changed() {
  [ -n "$(find "$HOME/.claude/skills" -mindepth 1 -maxdepth 1 -type d ! -name '.*' | head -1)" ] && return 0
  [ -n "$(find "$HOME/.claude/commands" -mindepth 1 -maxdepth 1 -type f -name '*.md' | head -1)" ] && return 0
  [ -n "$(git -C "$REPO" status --porcelain | head -1)" ]
}

# Inside an mr child (runners.child_env points push URLs at file:///nonexistent) a push would
# fail: mark pending only if something changed; mr's parent process calls this hook after the run.
case "${GIT_CONFIG_KEY_0:-}" in *pushInsteadOf*) changed && touch "$STATE/pending"; exit 0;; esac

[ -f "$STATE/pending" ] || changed || exit 0           # pending: an earlier record did not finish
touch "$STATE/pending"

# detach: `claude -p` kills hook children (even async ones) at exit, so leave its session
setsid nohup bash -c '
  sleep "${SKILL_SYNC_DEBOUNCE:-15}"                       # let a burst of session ends settle
  echo "== $(date -Iseconds) record" >>"$1/sync.log"
  t=; command -v timeout >/dev/null && t="timeout 300"
  $t "$2/sync.sh" --record >>"$1/sync.log" 2>&1 && rm -f "$1/pending"
' _ "$STATE" "$REPO" </dev/null >/dev/null 2>&1 &
exit 0
