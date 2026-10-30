---
name: ste-writing
description: Rewrite prose (docs, READMEs, PR descriptions, error messages, release notes, comments — never code) into ASD-STE100 Simplified Technical English to remove "AI slop". Use when asked to make writing not sound like AI, make docs clear or plain, enforce a controlled writing style, or write technical documentation that reads human. Two modes — strict (procedures/safety) and STE-flavored (general prose).
---

# ste-writing

Write prose in ASD-STE100 Simplified Technical English. This applies to documentation, READMEs, pull-request text, error messages, release notes, and comments. It does not apply to code, identifiers, or command syntax. It is not for marketing copy, essays, or anything that needs a voice — STE strips voice on purpose.

## Rules

WORDS
- Use one name for one thing. Do not call the same item by two different names.
- Use the short common word: start (not begin/commence/initiate), use (not utilize/leverage), help (not facilitate), make sure (not ensure), before (not prior to), after (not subsequent to), about (not regarding/concerning), get (not obtain/acquire), show (not demonstrate), also (not additionally/furthermore/moreover).
- Give each word one meaning. "fall" means to move down, not to decrease.
- No marketing adjectives: seamless, robust, powerful, cutting-edge, effortless, world-class, next-generation, revolutionary.
- American spelling.

VERBS
- Active voice. "the parser reads the file", not "the file is read by the parser".
- Use a verb for an action. "analyze the log", not "perform an analysis of the log".
- No stacked auxiliaries. Not "it is important to note that this may help to improve". Write "this improves X".
- No "-ing" main verb where a simple tense works.

SENTENCES
- One instruction per sentence. Max 20 words (instruction), max 25 (descriptive).
- No contractions. Use articles: a, an, the, this, these.

PUNCTUATION
- No semicolons. Write two sentences. (Note: the em dash is not banned by STE, only the semicolon is — add "no em dash" yourself if you want it gone.)

STRUCTURE
- One topic per paragraph, max six sentences. For steps, use a numbered vertical list, one action per item, imperative form. Put a condition before its command.

Write only the requested text. No preamble, no summary, no closing remarks.

## Modes

- **strict** — procedures, runbooks, safety text, error messages: apply every rule and both length caps.
- **STE-flavored** — general prose (READMEs, PR descriptions, docs): apply the sentence, paragraph, active-voice, and no-phrasal-verb discipline; relax the ~900-word dictionary lockdown so the text keeps enough range to read naturally.

## Self-lint (run before returning text)

1. Any sentence over 20 words? Split it.
2. Any semicolon? Replace with a period.
3. Any contraction? Expand it.
4. Any passive voice with a known actor? Make it active.
5. Any "-ing" main verb, nominalization ("perform an analysis"), or phrasal verb ("spin up")? Replace with a plain verb.
6. Same thing named two ways? Pick one name.

The mechanical rules above are lintable and are what removes slop. Full STE also needs human judgment (the right technical noun, whether a sentence "makes good sense") — a checker cannot certify that, and slop is not about that. This skill fixes the FORM of slop. It cannot make a hollow paragraph true.

## Machine check (bundled linter)

For long or important text, run the deterministic linter in this skill's directory:

```
python3 ~/.claude/skills/ste-writing/ste-lint.py draft.md    # or pipe text on stdin
```

The score is violations per 100 words. Lower is cleaner. Lint the draft, apply the rules, lint again. The delta between the two scores is the signal. It checks the mechanical subset only, not full STE compliance.

### Do not guess which rule fired

The default output prints only a total. Guessing at the cause wastes rounds. Ask it directly:

```bash
python3 -c "
import importlib.util, json
s = importlib.util.spec_from_file_location('l', '$HOME/.claude/skills/ste-writing/ste-lint.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
r = m.lint(open('draft.md').read())
print(json.dumps({k: v for k, v in r['violations'].items() if v}, indent=1))
print('longest sentence words:', r['longest_sentence_words'])
"
```

### Gotcha: a list with no blank lines is ONE paragraph

The linter splits paragraphs on blank lines (`re.split(r"\n\s*\n", raw)`). A numbered or bulleted list written with items on consecutive lines therefore counts as a single paragraph, and a list of four items with two sentences each trips `long_paragraph(>6s)`. Put a blank line between list items. This does not change how the list renders.

## References

- `before-after-samples.md` (this directory) — real baseline-vs-STE model outputs with scores. Read it to calibrate the target register.
- Full standard: `~/.claude/references/ASD-STE100-ISSUE-9.pdf` (Issue 9, 2025-01-15). Official source: https://asd-ste100.org (do not paste the standard in full; it is copyrighted).
- Source of this skill: https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop — includes first-party cross-model tests (slop −74% on Claude sonnet, −50% on gpt-5.5 vs baseline).
