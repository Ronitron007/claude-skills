#!/bin/bash
# Claude Code hook: append "ISO-timestamp<TAB>agent<TAB>skill-slug" to /home/box/shared-skills/.usage.log
# Wired as PreToolUse (matcher "Skill") and UserPromptExpansion (direct /skill typing) in ~/.claude/settings.json.
# Never blocks: always exits 0 with no stdout.
LOG=/home/box/shared-skills/.usage.log
in=$(cat 2>/dev/null)
ev=$(jq -r '.hook_event_name // empty' <<<"$in" 2>/dev/null)
if [ "$ev" = "UserPromptExpansion" ]; then
  slug=$(jq -r '.command_name // empty' <<<"$in" 2>/dev/null)
else
  slug=$(jq -r '.tool_input.skill // .tool_input.command // .tool_input.name // empty' <<<"$in" 2>/dev/null)
fi
[ -z "$slug" ] && exit 0
slug=${slug#/}; slug=${slug%% *}
agent="claude-code"
at=$(jq -r '.agent_type // empty' <<<"$in" 2>/dev/null); [ -n "$at" ] && agent="claude-code:$at"
printf '%s\t%s\t%s\n' "$(date -Iseconds)" "$agent" "$slug" >> "$LOG" 2>/dev/null
exit 0
