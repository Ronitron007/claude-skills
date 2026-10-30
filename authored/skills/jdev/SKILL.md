---
name: jdev
description: Use when explaining code, a system, an error, a design, or a rule to a junior developer, or when the user wants an explanation that a developer new to the codebase can follow with no follow-up question. Symptoms: an undefined term, a rule with no reason, a mechanism with no worked example, a step skipped as "obvious", prose that needs the code open beside it.
---

# jdev — explain for a junior developer

## Overview

The reader is a developer who joined yesterday. They know the language and git. They do not know this codebase, its vocabulary, its rules, or the reasons behind the rules. Write so that the reader needs no follow-up question.

Acceptance test: for each "what is X?", "why?", "what does it look like?", "what must I not do?", and "how do I see it?" the reader could ask, the answer is already in the message.

This skill stacks three layers. Layers 1 and 2 are existing skills. Layer 3 is new.

## Layer 1 — register: Simplified Technical English

**REQUIRED SUB-SKILL:** ste-writing, STE-flavored mode. The rules that matter most here:

- Active voice. One idea per sentence. Max 20 words per instruction sentence, 25 per descriptive sentence.
- One name for one thing. The short common word: use, start, help, before, after, about.
- No semicolons, no contractions, no marketing adjectives, no "-ing" main verb where a simple tense works.
- One topic per paragraph, max six sentences. Steps go in a numbered list, one action per item.
- Lint long text: `python3 ~/.claude/skills/ste-writing/ste-lint.py draft.md`

## Layer 2 — reasoning: the Decisions section

**REQUIRED SUB-SKILL:** surfacing-reasoning. The reader does not see your reasoning. Before you send, list each decision from this turn. A decision is a choice between workable options, an option you rejected, an assumption you adopted, or a trade-off you weighed. Compliance with an instruction is not a decision. Test: if the line could start with "as instructed" or "as the skill says", it is compliance. Cut it. End the message with a **Decisions** section. Write one line per decision: the decision, the reason, the rejected alternative. If there was none, write "Decisions: none."

When you write the explanation to a file for the junior developer, the Decisions section goes in the chat message, not in the file. The file is for the junior developer. The Decisions section is for the person who reviews your work.

A word cap on the explanation does not include the Decisions section.

## Layer 3 — the junior-developer recipe

The explanation has these parts, in this order.

1. **The problem.** One short paragraph. What goes wrong without this thing. The reader sees the problem before the mechanism.

2. **The terms.** Define each term the reader does not know, at first use. A term counts as known only if a developer with no context on this codebase or this domain knows it. Treat as unknown: project vocabulary, domain words, internal tool and script names, flags, acronyms, and role words such as "operator". Also define every term the request itself names as unknown.

3. **The mechanism.** What it does, in the order it runs. Name the file and the function for each part.

4. **One worked example.** Walk one concrete case from start to end, with real names. Show the real input, the real output it produces, and the real command a person runs next. One complete example beats three sketches. A list of what a function does is mechanism, not an example.

5. **The reason behind each rule.** Every "must", "never", or "always" in the subject gets its reason and the failure it prevents. One or two sentences each. Rules live in the code, in its comments, and in its strings. Search all three. The reason behind a rule is not advanced content. A rule without its reason teaches obedience. A rule with its reason teaches judgment.

6. **The traps.** Two to four things a new developer would plausibly do here that are wrong. Give each one the correct action instead.

7. **See it yourself.** One command to run, file to open, or test to read, so the reader can observe the behavior.

Parts 2, 4, 5, and 6 are the junior layer. They are what an explanation for a peer leaves out.

### Under a word cap

Fit the parts by cutting in this order: mechanism detail first, then trap count, then example length. Do not cut the terms, the example, or the reasons behind rules. The reader can read the code for the mechanism. They cannot read the code for a reason.

## Common mistakes

- The reason behind a rule cut as "architecture-level nuance beyond a first-day orientation". It is the highest-value line for a junior. Keep it.
- A term the request itself named as unknown, left undefined.
- A numbered list of what the function does, offered as the example. An example has a concrete input and a concrete output.
- Three thin examples where one complete example fits.
- A compliance item listed as a decision ("defined the term, as the brief asked"). Cut it.
- The Decisions section dropped because the request said "return only the explanation". The section stays. It goes in the chat message.

## When not to use

One-line status updates, commit messages, code, or identifiers. For those, the global concision rule applies.
