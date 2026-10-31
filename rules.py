#!/usr/bin/env python3
"""Write rules/agents.md into each agent's global instruction file, between markers.

Only agents whose config folder exists get the block. A re-run replaces the block in place,
so a change to rules/agents.md reaches every agent. Text outside the markers is never
touched: install then uninstall gives back the original bytes (a missing final newline
comes back added). A file with odd markers or a dangling symlink is
skipped with a warning, never guessed at. --uninstall removes the block. --dry-run prints
what would change.
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()
SOURCE = REPO / "rules/agents.md"
BEGIN = "<!-- claude-skills:begin (written by rules.py from the claude-skills repo; edit rules/agents.md there) -->"
END = "<!-- claude-skills:end -->"
# full-line markers only, so a file that quotes a marker inline is not matched
BEGIN_RE = re.compile(r"^<!-- claude-skills:begin[^\n]*-->$", re.M)
END_RE = re.compile(r"^<!-- claude-skills:end -->$", re.M)
BLOCK_RE = re.compile(r"\n?^<!-- claude-skills:begin[^\n]*-->$.*?^<!-- claude-skills:end -->$\n?", re.M | re.S)

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
    """text and result use \\n. block "" removes the block. Raises ValueError on odd markers."""
    begins, ends = len(BEGIN_RE.findall(text)), len(END_RE.findall(text))
    if begins != ends or begins > 1:
        raise ValueError(f"{begins} begin and {ends} end markers; fix the file by hand")
    if begins:  # replace in place, keeping the newline before the block
        m = BLOCK_RE.search(text)
        if m is None:
            raise ValueError("end marker before begin marker; fix the file by hand")
        lead = "\n" if m.group(0).startswith("\n") else ""
        if not block and m.end() == len(text):
            lead = ""  # the block was appended (see below): removing it restores the original bytes
        return text[:m.start()] + lead + block + text[m.end():]
    if not block:
        return text
    if not text:
        return block
    return text + ("" if text.endswith("\n") else "\n") + "\n" + block


def write_atomic(f: Path, content: str):
    """Replace the real file in one step (through a symlink), so no reader sees it half written."""
    real = f.resolve()
    if f.is_symlink() and not real.exists():
        raise OSError(f"dangling symlink to {real}")
    mode = real.stat().st_mode & 0o777 if real.exists() else 0o644
    fd, tmp = tempfile.mkstemp(dir=real.parent, prefix=f".{real.name}.")
    try:
        with os.fdopen(fd, "w", newline="") as h:
            h.write(content)
        os.chmod(tmp, mode)
        os.replace(tmp, real)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def is_linked_worktree() -> bool:
    """A worktree or a second checkout would write its own, short-lived path into every agent file."""
    try:
        r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--git-dir", "--git-common-dir"],
                           capture_output=True, text=True)
    except FileNotFoundError:  # no git: cannot be a worktree we know of
        return False
    dirs = r.stdout.split()
    return r.returncode == 0 and len(dirs) == 2 and Path(REPO, dirs[0]).resolve() != Path(REPO, dirs[1]).resolve()


def update(f: Path, block: str, dry: bool, uninstall: bool):
    raw = ""
    if f.exists():
        with open(f, newline="") as h:
            raw = h.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    new = apply(raw.replace("\r\n", "\n"), block).replace("\n", nl)
    if new == raw:
        return
    if dry:
        return print(f"rules: would update {f}")
    if not new and uninstall:
        f.unlink()
    else:
        write_atomic(f, new)
    print(f"rules: {'removed block from' if uninstall else 'updated'} {f}")


def main(argv):
    uninstall, dry = "--uninstall" in argv, "--dry-run" in argv
    if is_linked_worktree() and "--force" not in argv:
        print(f"rules: {REPO} is a git worktree; run rules.py from the main clone (or pass --force)", file=sys.stderr)
        return 1
    block = "" if uninstall else render()
    failed = 0
    for folder, f in TARGETS:
        if not folder.is_dir():
            continue
        try:
            update(f, block, dry, uninstall)
        except (OSError, ValueError) as err:
            failed += 1
            print(f"rules: skipped {f}: {err}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
