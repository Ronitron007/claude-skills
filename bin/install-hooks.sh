#!/usr/bin/env bash
# Wire bin/skill-sync-hook.sh into Claude Code (SessionEnd) and Cursor (stop, sessionEnd).
# Idempotent; re-run any time. Remove: bin/install-hooks.sh --uninstall
set -euo pipefail
command -v jq >/dev/null || { echo "install-hooks: jq not found; nothing changed" >&2; exit 1; }
HOOK="$(cd "$(dirname "$0")" && pwd)/skill-sync-hook.sh"
CS=~/.claude/settings.json; CH=~/.cursor/hooks.json
tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT
# edit FILE FILTER: write jq's result back only if jq succeeds (a bad or odd file is left as it was)
edit() {
  jq --arg h "$HOOK" "$2" "$1" > "$tmp" || { echo "install-hooks: could not update $1; it is unchanged" >&2; exit 1; }
  cat "$tmp" > "$1"
}
if [ "${1:-}" = --uninstall ]; then
  [ -f "$CS" ] && edit "$CS" 'if (.hooks.SessionEnd | type) == "array"
    then .hooks.SessionEnd |= map(select(all(.hooks[]?; .command != $h))) else . end'
  [ -f "$CH" ] && edit "$CH" 'reduce ("stop", "sessionEnd") as $k (.;
    if (.hooks[$k] | type) == "array" then .hooks[$k] |= map(select(.command != $h)) else . end)'
  echo "removed skill-sync hooks"; exit 0
fi
mkdir -p ~/.claude ~/.cursor; [ -f "$CS" ] || echo '{}' > "$CS"; [ -f "$CH" ] || echo '{"version":1,"hooks":{}}' > "$CH"
edit "$CS" 'if any(.hooks.SessionEnd[]?.hooks[]?; .command == $h) then . else
  .hooks.SessionEnd = ((.hooks.SessionEnd // []) + [{"hooks": [{"type": "command", "command": $h, "timeout": 5}]}]) end'
edit "$CH" '.version = (.version // 1)
  | reduce ("stop", "sessionEnd") as $k (.;
      .hooks[$k] = ((.hooks[$k] // []) | if any(.[]; .command == $h) then . else . + [{"command": $h, "timeout": 5}] end))'
echo "skill-sync hooks installed: $CS (SessionEnd), $CH (stop, sessionEnd)"
