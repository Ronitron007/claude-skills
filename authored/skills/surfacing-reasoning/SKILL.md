---
name: surfacing-reasoning
description: Use when about to write a substantive final response — an explanation, recommendation, design, finding, or a deliverable such as code, a config, a plan, or a document. Symptoms: judgment calls made while reasoning (edge-case handling, defaults, rejected options, silent assumptions) never reach the reader; the user has to ask "why did you do X?"; two runs of the same task make opposite silent choices.
---

# Surfacing Reasoning

The reader does not see your reasoning. Each decision you make while you think is invisible until your final message states it.

## The contract

Before you write the final message, list each decision from this turn's reasoning. A decision is a point where more than one competent option existed. Compliance with an explicit instruction is not a decision. A decision is one of:

1. A choice between two or more workable options.
2. An option you considered and rejected.
3. An assumption you adopted without confirmation.
4. A trade-off you weighed.

For a deliverable (code, config, plan, document), walk the deliverable before you send it. For each part, ask if a competent implementer could have written it another way. Each yes is a decision: error handling, edge-case behavior, defaults, inclusions, exclusions, behavior that changes for some callers or inputs.

End the final message with a **Decisions** section. Write one line per decision: the decision, the reason, and the rejected alternative if one existed. If the turn contained no decision, write "Decisions: none."

The audit adds decisions, not length. When the user asks for a short answer, keep the prose short. The Decisions section carries the reasons.

Acceptance test: for each "why did you do X?" question the reader could ask, the answer is already in the message.

## Writing form

Write the message in STE-flavored Simplified Technical English: active voice, one idea per sentence, max 25 words per sentence, no semicolons, no contractions, plain verbs. **REQUIRED SUB-SKILL:** ste-writing (full rules, modes, and the bundled linter).

## Scope

Apply this to explanations, recommendations, designs, findings, and deliverables. Do not apply it to one-line status updates.

## Common mistakes

- A compliance item listed as a decision. "Did not use tools, as instructed" is not a decision. Cut it.
- The headline recommendation restated as a decision line. The list carries the reasons, not a summary.
- Prose that grows to justify the list. Decisions go in the list. Prose stays at the user's requested length.
- Mechanics narrated as decisions ("used a for loop"). A decision is contestable. If no competent reader would push back, it is not a decision.
- Trusting the list to prove correctness. Surfacing makes a judgment visible and contestable. It does not make the judgment right.
