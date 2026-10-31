#!/usr/bin/env python3
"""Write rules/agents.md into each agent's global instruction file, between markers.

Only agents whose config folder exists get the block. A re-run replaces the block, so a
change to rules/agents.md reaches every agent. Text outside the markers is never touched.
--uninstall removes the block. --dry-run prints what would change.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()
SOURCE = REPO / "rules/agents.md"
BEGIN = "<!-- claude-skills:begin (written by rules.py from the claude-skills repo; edit rules/agents.md there) -->"
END = "<!-- claude-skills:end -->"
BLOCK_RE = re.compile(r"\n*<!-- claude-skills:begin[^\n]*-->.*?<!-- claude-skills:end -->\n?", re.S)

# (agent config folder, global instruction file read by that agent)
TARGETS = [
    (HOME / ".claude", HOME / ".claude/CLAUDE.md"),
    (HOME / ".codex", HOME / ".codex/AGENTS.md"),
    (HOME / ".gemini", HOME / ".gemini/GEMINI.md"),
    (HOME / ".config/opencode", HOME / ".config/opencode/AGENTS.md"),
    (HOME / ".factory", HOME / ".factory/AGENTS.md"),
    (HOME / ".pi/agent", HOME / ".pi/agent/AGENTS.md"),
]


def render() -> str:
    return f"{BEGIN}\n{SOURCE.read_text().strip().replace('{{REPO}}', str(REPO))}\n{END}\n"


def apply(text: str, block: str) -> str:
    rest = BLOCK_RE.sub("\n", text).rstrip("\n")
    if not block:
        return rest + "\n" if rest else ""
    return f"{rest}\n\n{block}" if rest else block


def main(argv):
    uninstall, dry = "--uninstall" in argv, "--dry-run" in argv
    block = "" if uninstall else render()
    for folder, f in TARGETS:
        if not folder.is_dir():
            continue
        old = f.read_text() if f.exists() else ""
        new = apply(old, block)
        if new == old:
            continue
        if dry:
            print(f"rules: would update {f}")
            continue
        f.unlink() if not new else f.write_text(new)
        print(f"rules: {'removed block from' if uninstall else 'updated'} {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
