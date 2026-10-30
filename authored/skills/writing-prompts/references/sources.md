# Extraction: OpenAI "Improving instruction hierarchy in frontier LLMs" + IH-Challenge paper (blog + full 25-page paper read)

1. Trust tiers: system ≻ developer ≻ user ≻ tool — put non-negotiable rules in the highest-privilege slot, never only the user turn.
2. State the compatibility rule: lower-priority instructions obeyed only where compatible with higher tiers; conflicts ignored, feasible-set intersection.
3. Retrieved/tool text is DATA, never commands — instructions inside sources have zero authority; present/quote, don't execute.
4. Authority comes from the CHANNEL, not from text claiming it — "SYSTEM INSTRUCTION (PRIORITY: 1000)" inside content is an impersonation attack; say so in the prompt.
5. Tie-break rule for same-tier conflicts stated explicitly (later supersedes earlier) — the model never improvises resolution. (Extraction analog: sources conflict → record both, never pick.)
6. Write the policy spec INTO the system prompt — a written spec converts to behavior via hierarchy training; single global spec ≈ category-specific.
7. Make every hard constraint MACHINE-CHECKABLE — LLM judges reward-hack; phrase constraints so a script can verify (exact enums, exact formats, explicit boundary of what counts).
8. Keep each instruction simple so failures are ATTRIBUTABLE — one constraint per rule; else comprehension failures masquerade as priority failures ("IF-simple").
9. Pair every prohibition with its benign complement — bare "never X" breeds blanket-refusal shortcuts; state the positive action ("copy verbatim, or emit not_reported") and test the benign case.
10. Sandwich defense (restate the critical rule AFTER long untrusted content) helps weaker models, can COST on robust ones — A/B per model.
11. Defense-in-depth: independent post-hoc output check (script for checkable rules, monitor for nuanced) — never let the generation prompt be the only enforcement point.
LOAD-BEARING: every instruction needs an assigned trust tier + a stated conflict rule; lower-tier text (incl. source content) is honored only where compatible, never because it claims authority.
# Extraction: arXiv 2503.04818 — "Prompt Engineering is Complicated and Contingent" (Meincke, Mollick, Mollick, Shapiro — full paper read)

1. No universal prompting tricks — politeness/commanding: no reliable aggregate effect; add wording only if it wins an A/B on your own task. "Prompting 'tricks' like politeness are not universal."
2. Explicit output-format constraints raised reliability — removing them degraded both models (RD 0.086-0.121 at 100%-consistency, p<0.001); format instruction is a CONSISTENCY device. "Removing explicit formatting constraints consistently led to performance degradation."
3. Formatting effects are contingent — validate per model/setting; prior work found the opposite in other settings.
4. Choose the passing standard BEFORE measuring — 100%/90%/51% thresholds flip conclusions; map threshold to error tolerance.
5. Single-run evals overestimate reliability — sample repeatedly (n=100/question); majority ≫ 100%-consistent (RD −0.177).
6. Tiny wording changes swing individual items ±0.6 in BOTH directions while aggregate stays flat — check per-item regressions, not averages.
7. Persona system-prompt line carried no measurable aggregate weight — boilerplate must earn its tokens.
8. Model characteristics dwarf prompt micro-optimization — spend effort on model choice, eval infrastructure, format scaffolding before wording polish.
9. Temperature 0 is NOT determinism — same question, different answers across 100 temp-0 runs; use majority/verification for must-not-vary fields.
Scope: GPQA Diamond, two OpenAI non-reasoning models; transferable part is the METHODOLOGY not the effect sizes.
LOAD-BEARING: the durable skill is measurement discipline — standard first, format constraints kept, repeated sampling over the full item set.
# Extraction: "Effective context engineering for AI agents" (Anthropic Engineering, Sep 2025, full text read)

1. Context > prompt — curation happens EVERY turn; prompt is one component of the window.
2. Attention budget / context rot — recall precision degrades as tokens grow (n² attention, short-skewed training); a gradient, not a cliff.
3. Guiding principle: the SMALLEST set of HIGH-SIGNAL tokens that maximizes desired-outcome likelihood; per block: does removing it lower the odds? If no, delete.
4. THE RIGHT ALTITUDE — two failure extremes: brittle hardcoded if-else scripts vs vague guidance falsely assuming shared context. Optimum = strong heuristics ("quote verbatim; range→record range; conflict→record both"), never bare "be accurate".
5. MINIMAL ≠ SHORT — minimal set that FULLY outlines expected behavior; completeness is the floor, tokens minimized above it; cut redundancy never coverage. [KEY reconciliation with our definitions-win data]
6. Start minimal, add ONLY against observed failures — patch real failure modes with one targeted instruction/example each; no imagined-failure defenses.
7. Section with explicit delimiters (XML/Markdown headers), one content piece in exactly one section; organization is the durable part.
8. Canonical EXAMPLES beat edge-case rule lists — "examples are the 'pictures' worth a thousand words"; rule #14 for a rare case → replace pile with one worked example.
9. Tools: unambiguous, minimally overlapping, token-efficient; human test — one obvious tool per situation.
10. Just-in-time context via lightweight references (paths/queries/links) + retrieval; upfront only the stable core.
11. Calibrate prescriptiveness to model capability; do the simplest thing that works; re-check inherited scaffolding on model upgrades.
12. Long-horizon: compaction (recall-first, clear old tool results), structured notes, sub-agents returning 1-2k-token distillations; specify what must SURVIVE a summary (decisions, unresolved issues, exact values with sources).
LOAD-BEARING: attention is a finite budget — the job is the smallest high-signal token set, complete but never padded, at heuristic altitude.
# Extraction: Claude Prompting Best Practices (platform.claude.com, full page read)

1. Colleague test — explicit beats inferred; "If you want 'above and beyond' behavior, explicitly request it."
2. Explain the WHY behind each rule — "Claude is smart enough to generalize from the explanation" (TTS/ellipses example).
3. 3–5 relevant, DIVERSE examples in <example> tags — the most reliable format/consistency lever; narrow sets teach unintended patterns.
4. XML tags separate content types (instructions/context/input/examples) — prevents data being read as instructions; consistent names, nesting.
5. One-sentence role in system prompt measurably shifts behavior.
6. Long context: documents at TOP, query/instructions at BOTTOM — up to 30% quality gain on 20k+ inputs.
7. Quote-first grounding for long docs: extract verbatim quotes into <quotes> BEFORE the task — focuses attention (maps to our extraction-honesty domain).
8. Say what TO do, not what to avoid; the prompt's own style bleeds into output.
9. Strict schemas: Structured Outputs or direct instruction + retries; prefills dead on 4.6+.
10. Reasoning: general "think thoroughly" beats prescriptive step lists; shape via <thinking> examples if needed.
11. Self-check close: "Before you finish, verify your answer against [criteria]" — reliable error catcher (strip on Opus 5: over-verifies).
12. Action verbs for actions — "can you suggest" yields suggestions; imperative yields edits.
13. Calibrated intensity — CAPS/MUST anti-laziness pressure now OVER-triggers; write plain conditionals unless truly absolute.
14. Research prompts: success criteria + cross-source verification + competing hypotheses with tracked confidence.
15. Forbid speculation about unopened sources — grounding as hard precondition ("Never speculate about code you have not opened").
LOAD-BEARING: state exactly what you want — behavior, format, action, and the REASON behind each rule; failures are prompts that left intent to inference or over-pressured a literal instruction-follower.
# RED baseline — two fresh agents, no skill, same scenario (quality-risk research prompt for ashwagandha)

## Baseline B (full prompt banked in task output a6b487e4a80bb628b)
Surprisingly strong: purpose block, definitions, per-list entry anatomy, ordered source hierarchy, different-ingredient shape example with <angle-bracket> placeholders, "never fill a gap with an estimate".
RESIDUAL FAILURES (the skill must close these):
1. resolution_hint instructs the researcher to PICK THE WINNER ("which statement the better evidence supports, and why") — violates record-never-resolve; the exact domain-honesty failure our envelopes guard against.
2. No data-not-commands line: nothing says instructions inside fetched sources carry zero authority (OpenAI IH takeaway 3/4 missing).
3. Schema-strictness mismatch: "Leave it empty when versioning does not apply" vs a required-nullable field — 'empty' is not 'null'; prompt language must match the schema's actual states.
4. Minor: some bare prohibitions without stated benign complement.
TEST HONESTY NOTE: the scenario brief itself contained scaffolding ("wrong or invented facts are costly", full field lists) and the agent runs a frontier model — a leaner scenario or smaller model would fail harder. The skill's value: reproduce this quality without a lucky scaffold, and close the residual failures above.

## Baseline A (task acadbb14fb55ed269) — also strong, same residual failures
F1 CONFIRMED 2/2: resolution_hint = "which side looks stronger and why (newer, more authoritative, larger sample...)" — winner-picking, again.
F2 CONFIRMED 2/2 (worse in A): invented vocabularies contradicting the schema's closed enums — kind: 'regulation','pharmacopoeia','market_survey'... (schema: trial/meta-analysis/systematic-review/review/guideline/registry/regulator/other); version_status: adds 'withdrawn','unclear' (schema: current/superseded/unknown). A strict schema REJECTS these; the prose sets the researcher up to fail validation.
F3 CONFIRMED 2/2: no line anywhere that instructions inside fetched sources carry zero authority.
Strong behaviors to CODIFY (appeared unprompted, must survive without a lucky scaffold): purpose block with stakes, definitions with the N-facts rule, per-field anatomy, different-ingredient worked example with <placeholders>, "never invent a URL; empty list is a valid answer", India-first source ordering, newest-version rule, alias search terms.
