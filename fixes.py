#!/usr/bin/env python3
"""Apply fixes.json to SKILL.md frontmatter. Usage: fixes.py DIR...  (each DIR holds skill folders)."""
import json
import re
import sys
from pathlib import Path

FIXES = Path(__file__).resolve().parent / "fixes.json"


def load():
    return json.loads(FIXES.read_text()) if FIXES.exists() else {}


def fix_text(name: str, text: str, fixes: dict) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end < 0:
        return text
    head, rest = text[:end], text[end:]
    for old, new in fixes.get("rename_keys", {}).items():
        head = re.sub(rf"(?m)^{re.escape(old)}(\s*:)", rf"{new}\1", head)
    for key, val in fixes.get("set", {}).get(name, {}).items():
        line = f"{key}: {val}"
        if re.search(rf"(?m)^{re.escape(key)}\s*:", head):
            head = re.sub(rf"(?m)^{re.escape(key)}\s*:.*$", line, head)
        else:
            head += "\n" + line
    return head + rest


def fix_file(md: Path, fixes: dict) -> bool:
    text = md.read_text(errors="replace")
    new = fix_text(md.parent.name, text, fixes)
    if new != text:
        md.write_text(new)
        return True
    return False


def main(dirs):
    fixes, changed = load(), []
    for d in map(Path, dirs):
        for md in sorted(d.glob("*/SKILL.md")):
            if fix_file(md, fixes):
                changed.append(str(md))
    for c in changed:
        print("fixed:", c)


if __name__ == "__main__":
    main(sys.argv[1:])
