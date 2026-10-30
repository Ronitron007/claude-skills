---
name: diagnose
description: Use when user wants investigation, diagnosis, root-cause analysis, or a plan WITHOUT any implementation. Triggered by /diagnose slash command or phrases like "just diagnose", "don't fix yet", "analyze only", "investigate first".
---

# Diagnose

## Overview

**Investigation-only mode. No code changes. No fixes. No implementation.**

Output a diagnosis, analysis, or plan — then stop. The user will decide whether and how to proceed.

## The Iron Rule

```
NO WRITES. NO EDITS. NO FIXES. PLAN ONLY.
```

While in this mode:
- ✅ Read files, run read-only commands (`git status`, `git log`, `git diff`, `ls`, `cat`, tests in dry-run/read mode, `tsc --noEmit`, `grep`, `rg`)
- ✅ Use Read, Glob, Grep, Bash (read-only), Agent (for investigation), WebFetch, WebSearch
- ❌ NO Edit, Write, NotebookEdit
- ❌ NO Bash commands that mutate state (no `git commit`, `git push`, `git checkout -b`, `npm install`, `rm`, `mv`, migrations, deploys, PR creation, sending messages)
- ❌ NO "while I'm here, let me fix this quickly"
- ❌ NO partial implementations "to illustrate the approach"

If unsure whether an action is read-only, don't run it. Ask.

## What to Produce

End every diagnose session with a structured report:

1. **What I found** — observed facts, file:line references, command output excerpts
2. **Root cause / hypothesis** — the explanation, with confidence level
3. **Options** — 2–3 possible approaches with tradeoffs (not just one)
4. **Recommended plan** — concrete steps, which files/lines, what tests to add
5. **Unresolved questions** — concise list, sacrifice grammar for concision
6. **What I did NOT do** — explicit line: "No files were modified."

Reference file paths as `path/to/file.ts:123` so they're clickable.

## Red Flags — STOP if you catch yourself thinking:

| Thought | Reality |
|---------|---------|
| "Let me just fix this one line" | No. Add it to the plan. |
| "I'll write the patch to show what I mean" | A described diff is enough. Don't write it. |
| "This is trivial, faster to fix than explain" | User explicitly asked for diagnosis only. Respect that. |
| "I'll create a scratch file to test my theory" | Scratch files are writes. Use read-only verification. |
| "Let me run the fix and see if tests pass" | That's implementation. Stop. |
| "I'll just refactor while I'm reading this" | No. |

All of these mean: **stop, finish the diagnosis, hand back to user.**

## Exit Criteria

You are done when:
- Root cause identified (or hypotheses ranked if uncertain)
- Plan is concrete enough that a future session can execute it without re-investigating
- Unresolved questions listed
- Explicit "no files modified" confirmation

Then stop and wait. Do not ask "want me to implement this?" as a leading question — just present the diagnosis and let the user drive.

## When NOT to Use

- User says "fix it" or "implement X" — that's implementation mode, not diagnose.
- User asks a factual question with an obvious answer — just answer.
- Mid-implementation, user asks a clarifying question — answer it, don't switch modes.
