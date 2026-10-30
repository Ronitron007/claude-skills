# Sourced by sync.sh on the Grok Bot box (select with SKILLS_HOST=box or a .host file containing "box").
# Claude Code on the box must go through the usage-limit wrapper.
export PATH=/home/box/claude-limits/bin:$PATH
# `claude plugin ...` (restore.sh, host_post) is not a model turn: skip the wrapper's usage probe
# for that subcommand only. The wrapper's hourly limit check still applies; other calls are untouched.
claude() { if [ "${1:-}" = plugin ]; then CLAUDE_LIMITS_PROBE=1 command claude "$@"; else command claude "$@"; fi; }
export -f claude

host_post() {
  # pstack's Claude port drops disable-model-invocation on 57 of 58 skills, so they would auto-load.
  # It is enabled on the Mac; keep it off here. Undo: claude plugin enable pstack@pstack-claude
  if jq -e '.enabledPlugins["pstack@pstack-claude"] == true' ~/.claude/settings.json >/dev/null 2>&1; then
    claude plugin disable 'pstack@pstack-claude' >/dev/null && echo "sync: disabled pstack@pstack-claude (box policy)"
  fi
  # /home/box/shared-skills is read by mr, REGISTRY.md links and the skill-use hook: keep the path.
  local old=${SHARED_SKILLS_DIR:-/home/box/shared-skills}
  if [ -d "$old" ] && [ ! -L "$old" ] && find ~/.claude/skills ~/.cursor/skills -maxdepth 1 -lname "$old/*" 2>/dev/null | grep -q .; then
    echo "sync: not moving $old yet: links still point into it"
  elif [ -d "$old" ] && [ ! -L "$old" ]; then
    [ -f "$old/.usage.log" ] && cat "$old/.usage.log" >> "$REPO/registry/.usage.log"
    local keep="/workspace/backups/shared-skills-old-$(date +%Y%m%d-%H%M)"
    mkdir -p /workspace/backups && mv "$old" "$keep" && echo "sync: moved old $old to $keep"
  fi
  # link only when nothing is there: `ln -s` onto a real folder would create a link inside it
  if [ ! -e "$old" ] && [ ! -L "$old" ]; then ln -s "$REPO/view" "$old"; fi
  return 0
}
