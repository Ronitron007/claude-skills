#!/usr/bin/env python3
"""Make this clone the one place skills live on this machine.

1. Adopt real folders in ~/.claude/skills: a reinstall (npx skills) goes to installed/<name>,
   a changed copy of a repo skill goes back into the repo, an unknown skill goes to extra/skills
   and sources.json (class authored). Nothing is deleted that is not saved first.
2. Link ~/.claude/skills/<name> and ~/.claude/commands/<file> to the repo folders.
3. Remove our links from ~/.cursor/skills: Cursor also reads ~/.claude/skills, and it does
   not de-duplicate, so a second link would list the skill twice.
4. Build view/: one link per skill, plus the registry files (the old /home/box/shared-skills layout).
5. Apply fixes.json to every skill folder.
"""
import filecmp
import json
import os
import shutil
import socket
import sys
from datetime import date
from pathlib import Path

import fixes

REPO = Path(__file__).resolve().parent
HOME = Path.home()
CLAUDE_SKILLS, CLAUDE_CMDS = HOME / ".claude/skills", HOME / ".claude/commands"
CURSOR_SKILLS = HOME / ".cursor/skills"
LOCK = HOME / ".agents/.skill-lock.json"
INSTALLED, EXTRA, VIEW = REPO / "installed", REPO / "extra/skills", REPO / "view"
ORDER = [EXTRA, INSTALLED, REPO / "vendored/skills", REPO / "authored/skills"]  # first match wins
OURS = [str(REPO), "/home/box/shared-skills"]
dry = "--dry-run" in sys.argv


def say(*a):
    print("link:", *a)


def same_tree(a: Path, b: Path) -> bool:
    c = filecmp.dircmp(a, b, ignore=["__pycache__", ".DS_Store"])
    if c.left_only or c.right_only or c.diff_files or c.funny_files:
        return False
    return all(same_tree(a / d, b / d) for d in c.common_dirs)


def replace_dir(src: Path, dest: Path):
    """Move src to dest; dest's old content is replaced."""
    if dry:
        return say("would move", src, "->", dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))


def target(name: str):
    for root in ORDER:
        if (root / name / "SKILL.md").exists():
            return root / name
    return None


def adopt():
    lock = json.loads(LOCK.read_text())["skills"] if LOCK.exists() else {}
    for p in sorted(CLAUDE_SKILLS.iterdir()) if CLAUDE_SKILLS.exists() else []:
        if p.is_symlink() or not p.is_dir() or p.name.startswith(".") or p.name == "synced":
            continue
        if not (p / "SKILL.md").exists():
            say("skip (no SKILL.md):", p)
            continue
        name = p.name
        if not dry:
            fixes.fix_file(p / "SKILL.md", fixes.load())  # so a known fix does not count as a local edit
        if name in lock:  # reinstalled by npx skills: the fresh copy wins
            replace_dir(p, INSTALLED / name)
            say("adopted reinstall:", name, "-> installed/")
            if name not in known() and not dry:  # a new install: record its source so it reaches GitHub
                lk = lock[name]
                declare(name, {"source": lk.get("sourceUrl") or lk["source"], "skillPath": lk.get("skillPath"),
                               "description": description(INSTALLED / name),
                               "note": f"installed on {socket.gethostname()} {date.today()}"})
                say("recorded new install in sources.json:", name)
            continue
        t = target(name)
        if t is None:
            replace_dir(p, EXTRA / name)
            if not dry:
                declare(name, {"class": "authored", "description": description(EXTRA / name),
                               "note": f"adopted on {socket.gethostname()} {date.today()}"})
            say("adopted new skill:", name, "-> extra/skills + sources.json")
        elif same_tree(p, t):
            if not dry:
                shutil.rmtree(p)
        else:
            replace_dir(p, t)
            say("kept local edit:", name, "->", t.relative_to(REPO))


def known() -> set:
    """Skills the repo already knows: sources.json plus the main machine's manifest."""
    src, man = REPO / "sources.json", REPO / "manifest.json"
    names = set(json.loads(src.read_text())) if src.exists() else set()
    if man.exists():
        names |= {e["name"] for e in json.loads(man.read_text())["skills"]}
    return names


def declare(name: str, entry: dict):
    src = REPO / "sources.json"
    s = json.loads(src.read_text()) if src.exists() else {}
    s[name] = entry
    src.write_text(json.dumps(s, indent=2) + "\n")


def description(d: Path) -> str:
    import export
    return export.frontmatter(d / "SKILL.md").get("description", "")


def link(dest: Path, src: Path):
    if dest.is_symlink() and os.readlink(dest) == str(src):
        return
    if dry:
        return say("would link", dest, "->", src)
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.exists():
        raise SystemExit(f"link: refusing to replace real folder {dest}")
    dest.symlink_to(src)


def ours(p: Path) -> bool:
    return p.is_symlink() and any(os.readlink(p).startswith(o) for o in OURS)


def build_view(want: dict):
    """Update view/ in place, one atomic rename per entry, so a reader (mr, the registry hook) never
    sees it empty or half-built. Links that are already right are left alone."""
    if VIEW.is_symlink() or (VIEW.exists() and not VIEW.is_dir()):
        VIEW.unlink()
    VIEW.mkdir(exist_ok=True)
    for name, src in want.items():
        p = VIEW / name
        if p.is_symlink() and os.readlink(p) == str(src):
            continue
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)  # not ours: view/ holds only links
        tmp = VIEW / f".{name}.tmp-{os.getpid()}"
        tmp.unlink(missing_ok=True)
        tmp.symlink_to(src)
        os.replace(tmp, p)
    for p in list(VIEW.iterdir()):
        if p.name not in want:
            shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()


def main():
    CLAUDE_SKILLS.mkdir(parents=True, exist_ok=True)
    CLAUDE_CMDS.mkdir(parents=True, exist_ok=True)
    adopt()
    names = sorted({d.name for root in ORDER if root.exists() for d in root.iterdir()
                    if (d / "SKILL.md").exists()})
    if not dry:
        fixes.main([str(r) for r in ORDER if r.exists()])
    for n in names:
        link(CLAUDE_SKILLS / n, target(n))
    for f in sorted((REPO / "authored/commands").glob("*.md")):
        dest = CLAUDE_CMDS / f.name
        if dest.is_file() and not dest.is_symlink():
            if not filecmp.cmp(f, dest, shallow=False) and not dry:
                shutil.copy2(dest, f)
                say("kept local edit: command", f.name)
            if not dry:
                dest.unlink()
        link(dest, f)
    # drop dangling or stale links we made earlier
    for p in sorted(CLAUDE_SKILLS.iterdir()):
        if p.is_symlink() and os.readlink(p).startswith(str(REPO) + "/") and p.name not in names and not dry:
            p.unlink()
            say("removed stale link:", p)
    if CURSOR_SKILLS.exists():
        for p in sorted(CURSOR_SKILLS.iterdir()):
            if ours(p) and not dry:
                p.unlink()
                say("removed duplicate cursor link:", p.name)
    if not dry:
        (REPO / "registry" / ".usage.log").touch()  # gitignored; the Claude Code skill hook appends here
        want = {n: target(n) for n in names}
        for f in ["README.md", "REGISTRY.md", "registry.json", "SELECTION-METHOD.md", "bin", ".usage.log"]:
            if (REPO / "registry" / f).exists():
                want[f] = REPO / "registry" / f
        build_view(want)
    say(f"{len(names)} skills linked into {CLAUDE_SKILLS}")


if __name__ == "__main__":
    main()
