# Skill selection method (highest return per token)

How agents on this box decide whether a public skill is worth installing. Used to score
every entry in REGISTRY.md / registry.json. Written 2026-10-29 (IST).

## Short version (use this)

Score each candidate 0-5 on six axes, for the specific skills you would install (not the whole pack):

    Score = 3F + 3L + 2U + 1S - 2C - 3R        install on probation if Score >= 18

| Axis | Question | 5 means | 0 means |
| --- | --- | --- | --- |
| F fire rate | How often does its trigger hit Rohan's real work (kyaloon-app Expo/Supabase, mr CLI)? | most sessions | stack he doesn't use |
| L lift | Does it change outcomes vs. the base model's default? | enforces a step models skip (verify, spec handoff, version-specific facts) | restates good practice |
| U uniqueness | Non-overlap with installed skills and Grok Bot's built-ins | nothing else claims the trigger | duplicate |
| S staleness resistance | Survives upstream drift | process skill, active repo | pinned API facts, stale repo |
| C context cost | Always-loaded name+description tokens (+ body over ~500 lines) | big pack / verbose descriptions (>2.5k tok) | slash-only or one short description |
| R risk | Misfire / over-trigger / house-rule conflict | auto-push, auto-PR, Opus by default, autonomous runs | narrow trigger, no side effects |

C bands used here (measured from the cloned repos, chars/4): 0 = slash-only (disable-model-invocation),
1 = <300 tok, 2 = 300-1000, 3 = 1000-2500, 4 = 2500-5000, 5 = >5000.

**Hard gates (do not install, whatever the score):** pushes/opens PRs or writes to main without an explicit ask;
hard-codes or auto-escalates to Opus; needs a new runtime or API key for its happy path; vague
description ("use for coding"); unmaintained >6 months and version-pinned; trigger collides with an
installed skill and can't be fixed by editing one description; nobody can name a real task from last month it would have changed.

**Install individual skills, not packs.** Copy only the picked skill folders into /home/box/shared-skills/<slug>.

**Cheap evaluation (one skill per fortnight):**
1. Install one new skill at the start of a pruning fortnight (never two at once, or .usage.log can't attribute).
2. Pick 2-3 real recurring tasks (e.g. an mr spec -> cheap-model implement round; a kyaloon screen or Supabase migration).
3. A/B by absence: run with the skill, then move its folder out and rerun on a fresh branch; n=3 per arm is enough.
   Look for categorical differences (did it verify? did it write tests? did the spec hold?).
4. Log to a sidecar `/home/box/shared-skills/.eval.log` (leave .usage.log's 3-column format alone):
   `timestamp<TAB>slug<TAB>task-id<TAB>arm(on|off)<TAB>model<TAB>output-tokens<TAB>rework-edits<TAB>pass|fail`.
   rework-edits (lines fixed afterwards) is the best lift proxy.
5. Fortnight verdict: 0 uses -> pruned automatically; used but rework unchanged -> delete (ceremony);
   used with less rework -> keep, and tighten its description if it fired on the wrong tasks.

What I changed from Opus's answer (below): kept its formula and gates unchanged; added measured C bands so
C is not a guess; cut its 5-task A/B to 2-3 tasks; made "install individual skills" the default for every pack,
not just superpowers.

---

## Opus planning answer (verbatim)

Source: one call, `cursor-agent -p --model claude-opus-5-thinking-high`, 2026-10-29 ~23:45 IST
(the first attempt stopped at a workspace-trust prompt before reaching the model; it was rerun once with `--trust`).

Advising only — no tools run, no files touched, consistent with your standing rule that I diagnose and recommend rather than apply.

## (a) Scoring: 0–5 rubric, weighted

Rate each candidate skill 0–5 on six axes, then:

```
Score = 3F + 3L + 2U + 1S − 2C − 3R      (range −25…+45; install if ≥ 18)
```

| Axis | Meaning | 5 looks like | 0 looks like |
|---|---|---|---|
| **F** Fire rate | How often the trigger hits *Rohan's* work | fires in most Expo/Supabase or `mr` sessions | fires on stacks he doesn't use |
| **L** Lift | Change in outcome vs frontier default | enforces a workflow the model skips unprompted (TDD, verification gates, spec handoff) | restates good practice the base model already does |
| **U** Uniqueness | Non-overlap with installed set | no installed skill claims the trigger | duplicate trigger phrase with `expo-design-system` et al. |
| **S** Staleness resistance | Survives upstream drift | process/workflow, few version-pinned API facts | pinned SDK snippets that rot each release |
| **C** Context cost | Always-loaded frontmatter | one skill, ≤40-token description | pack of 15, verbose descriptions |
| **R** Risk | Misfire + house-rule conflict | narrow trigger, no side effects | auto-branches/pushes, auto-escalates to Opus |

Weighting rationale: **L and F dominate because the token cost is not the real cost.** A 40-token description × 20 skills ≈ 800 tokens/session — negligible against your budget. The expensive failure is a skill firing on the wrong task and dragging a cheap model through a ceremony it didn't need, so `R` carries the heaviest negative weight.

Body cost is deliberately *not* scored: it's paid only on trigger, so it's already priced in through F. But cap it — a SKILL.md body over ~500 lines, or one that eagerly pulls references, should lose a point on `C`.

## (b) Hard gates (auto-reject, no scoring)

1. Performs git writes to `main`, force-pushes, or opens PRs without an explicit ask.
2. Hard-codes an expensive model or auto-escalates to Opus.
3. Trigger phrase collides with an installed skill and the overlap isn't resolvable by editing one description.
4. Requires a new runtime dependency or credential for its happy path.
5. Frontmatter description is vague ("use for coding tasks") — guaranteed over-trigger.
6. Upstream unmaintained >6 months *and* contains version-pinned API detail.
7. You can't name the concrete task last month where it would have changed the result.

## (c) Cheap evaluation protocol

1. **Probation install**: one skill at a time, start of a pruning fortnight. Never evaluate two new skills in the same cycle — `.usage.log` can't attribute the difference.
2. **Pick 5 real recurring tasks**, not synthetic ones. For `mr`, that's spec-write → cheap-model-implement rounds; for the app, a screen build and a Supabase migration.
3. **A/B by absence**: run the task with the skill present, then move the directory out of `~/.claude/skills` and rerun on a fresh branch. n=3 per arm is enough — you're looking for categorical differences (did it write tests? did it verify before claiming done?), not p-values.
4. **Log to a sidecar** `.eval.log`, leaving `.usage.log`'s three-column format intact: `timestamp, slug, task-id, arm, model, output-tokens, rework-edits, pass/fail`. `rework-edits` (lines Rohan had to fix afterwards) is your single best lift proxy.
5. **Fortnight verdict**: 0 invocations → delete, as the routine already does. Invoked but `rework-edits` unchanged → delete, it's ceremony. Invoked with lower rework → keep, and tighten the description if it fired on anything unintended.

## (d) Individual skills, not packs

Install individually. Packs bundle a fixed frontmatter tax and, worse, a bundled trigger surface you didn't vet — superpowers' `using-superpowers` asserts precedence over your own judgement, which is exactly the over-trigger risk the rubric penalises.

From superpowers, cherry-pick four that score highest against the `mr` pipeline: **writing-plans** and **executing-plans** (they *are* your spec-first Opus-plans/cheap-implements split), **verification-before-completion** (highest lift per token on the box — cheap models reliably overclaim success), and **systematic-debugging**. Defer **TDD** until `mr` has a test harness, skip **using-git-worktrees** unless best-of-N runs become routine, and skip **brainstorming** — it adds a conversational round-trip that conflicts with keeping complexity low.
