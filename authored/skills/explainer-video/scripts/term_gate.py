#!/usr/bin/env python3
"""Check that the narration teaches each new term before it uses it.

Usage: term_gate.py <narration.md> <terms.md> [--budget 2]

terms.md is a markdown table written by the script agent, one row per technical term
that the voice says:

    | Term | Status | Taught in | Spoken forms |
    |---|---|---|---|
    | call stack | teach | stack_intro | call stack |
    | promise | known | | promise, promises |

Status is `known` (in the viewer model's knows column) or `teach`.
Spoken forms: the words the voice uses for the term, comma-separated, matched as whole
words, case-insensitive.

Checks:
  - each spoken form of a `teach` term first occurs in its `Taught in` scene or later
  - a `teach` term is used in at least one scene after the scene that teaches it
    (a term used once is not worth teaching: cut it)
  - no scene teaches more than --budget new terms
Exit code: 0 pass; 1 a check failed; 2 bad input.
"""
from __future__ import annotations

import re
import sys
from collections import Counter


def scenes(path: str) -> list[tuple[str, str]]:
    text = open(path).read()
    return [(n, b.lower()) for n, b in re.findall(r"^## (\w+)\n(.*?)(?=^## |\Z)", text, re.S | re.M)]


def terms(path: str) -> list[dict]:
    rows = []
    for line in open(path):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].lower() == "term" or set(cells[0]) <= set("-: "):
            continue
        forms = [f.strip().lower() for f in cells[3].split(",") if f.strip()] or [cells[0].lower()]
        rows.append({"term": cells[0], "status": cells[1].lower(), "taught": cells[2], "forms": forms})
    return rows


def main() -> int:
    args = sys.argv[1:]
    budget = 2
    if "--budget" in args:
        i = args.index("--budget")
        budget = int(args[i + 1])
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        return 2
    sc = scenes(args[0])
    order = {n: i for i, (n, _) in enumerate(sc)}
    rows = terms(args[1])
    fails = []
    taught = Counter()
    for r in rows:
        if r["status"] not in ("known", "teach"):
            fails.append(f"{r['term']}: status must be known or teach")
            continue
        uses = [i for i, (_, body) in enumerate(sc)
                if any(re.search(rf"\b{re.escape(f)}\b", body) for f in r["forms"])]
        if not uses:
            fails.append(f"{r['term']}: listed but never spoken")
            continue
        if r["status"] == "known":
            continue
        if r["taught"] not in order:
            fails.append(f"{r['term']}: taught-in scene {r['taught']!r} does not exist")
            continue
        t = order[r["taught"]]
        taught[r["taught"]] += 1
        if uses[0] < t:
            fails.append(f"{r['term']}: used in {sc[uses[0]][0]} before it is taught in {r['taught']}")
        if not any(u > t for u in uses):
            fails.append(f"{r['term']}: never used after {r['taught']}; cut it instead of teaching it")
    for scene, n in taught.items():
        if n > budget:
            fails.append(f"{scene}: teaches {n} new terms (budget {budget})")
    for f in fails:
        print("FAIL", f)
    print(f"{len(rows)} terms, {sum(taught.values())} taught, {len(fails)} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
