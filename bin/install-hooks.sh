#!/usr/bin/env bash
# Wire bin/skill-sync-hook.sh into Claude Code (SessionEnd) and Cursor (stop, sessionEnd).
# Idempotent; re-run any time. Remove: bin/install-hooks.sh --uninstall
set -euo pipefail
HOOK="$(cd "$(dirname "$0")" && pwd)/skill-sync-hook.sh"
CS=~/.claude/settings.json; CH=~/.cursor/hooks.json
mkdir -p ~/.claude ~/.cursor; [ -f "$CS" ] || echo '{}' > "$CS"; [ -f "$CH" ] || echo '{"version":1,"hooks":{}}' > "$CH"
tmp=$(mktemp)
if [ "${1:-}" = --uninstall ]; then
  jq --arg h "$HOOK" '(.hooks.SessionEnd // []) |= map(select(all(.hooks[]?; .command != $h)))' "$CS" > "$tmp" && cat "$tmp" > "$CS"
  jq --arg h "$HOOK" '.hooks.stop |= map(select(.command != $h)) | .hooks.sessionEnd |= map(select(.command != $h))' "$CH" > "$tmp" && cat "$tmp" > "$CH"
  rm -f "$tmp"; echo "removed skill-sync hooks"; exit 0
fi
jq --arg h "$HOOK" 'if any(.hooks.SessionEnd[]?.hooks[]?; .command == $h) then . else
  .hooks.SessionEnd = ((.hooks.SessionEnd // []) + [{"hooks": [{"type": "command", "command": $h, "timeout": 5}]}]) end' "$CS" > "$tmp" && cat "$tmp" > "$CS"
jq --arg h "$HOOK" '.version = (.version // 1)
  | .hooks.stop = ((.hooks.stop // []) | if any(.[]; .command == $h) then . else . + [{"command": $h, "timeout": 5}] end)
  | .hooks.sessionEnd = ((.hooks.sessionEnd // []) | if any(.[]; .command == $h) then . else . + [{"command": $h, "timeout": 5}] end)' "$CH" > "$tmp" && cat "$tmp" > "$CH"
rm -f "$tmp"; echo "skill-sync hooks installed: $CS (SessionEnd), $CH (stop, sessionEnd)"
