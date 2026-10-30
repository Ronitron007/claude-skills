#!/usr/bin/env bash
# Install a launchd agent that runs export.py when skills change, and hourly as a fallback.
# Re-run to update. Uninstall: ./install.sh --uninstall
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
LABEL=com.rohan.claude-skills-export
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--uninstall" ]; then rm -f "$PLIST"; echo "removed $LABEL"; exit 0; fi

mkdir -p "$REPO/.logs"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/python3</string><string>$REPO/export.py</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
  <key>WatchPaths</key>
  <array>
    <string>$HOME/.claude/skills</string>
    <string>$HOME/.claude/commands</string>
    <string>$HOME/.agents/skills</string>
    <string>$HOME/.agents/.skill-lock.json</string>
    <string>$HOME/.claude/plugins/installed_plugins.json</string>
    <string>$HOME/.claude/plugins/known_marketplaces.json</string>
  </array>
  <key>StartInterval</key><integer>3600</integer>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$REPO/.logs/export.log</string>
  <key>StandardErrorPath</key><string>$REPO/.logs/export.log</string>
</dict>
</plist>
EOF
launchctl bootstrap "gui/$UID" "$PLIST"
echo "loaded $LABEL; log: $REPO/.logs/export.log"
