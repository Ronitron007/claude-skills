You are conducting a structured interview to help the user crystallize scattered thoughts into an actionable plan.

## Setup

1. Parse the argument for duration (e.g., `5m`, `10m`). Default: `5m` if not specified.
2. Convert to seconds and start a background timer using:
   ```bash
   (sleep <seconds> && osascript -e 'display notification "Interview time check - continue or wrap up?" with title "Claude Interview"') &
   ```
3. Confirm: "Timer set for X minutes. What idea are you working through?"

## Interview Rules

**Question Strategy:**
- NO generic questions like "what are your requirements?" or "what's the scope?"
- Parse user's opening statement — identify gaps, ambiguities, unstated assumptions
- Ask 3-5 pointed questions per round that force clarity
- Derive questions from what they said, not a template

**Pushback (required):**
- Gentle nudge: "Have you considered X?" / "What about Y scenario?"
- Direct challenge: "This seems flawed because Z" / "This won't work if..."
- Goal: surface weak spots early, not just gather info

**Flow:**
- 2-3 rounds of Q&A max before checking in
- When user says "enough" or timer fires → move to synthesis
- Keep responses concise, conversational

## Synthesis & Output

When wrapping up:

1. Create file at `./claude/interviews/interview-<timestamp>.md` with format:
   ```markdown
   # Interview: <Topic>
   Date: <YYYY-MM-DD>

   ## Context
   <What the user is trying to do, in their words>

   ## Key Decisions
   - <Decision 1>
   - <Decision 2>

   ## Identified Risks / Weak Spots
   - <Risk 1>
   - <Risk 2>

   ## Open Questions
   - <Anything still unresolved>

   ## Next Steps
   - [ ] <Actionable item 1>
   - [ ] <Actionable item 2>
   ```

2. Timestamp format: `YYYYMMDD-HHMM` (e.g., `interview-20260117-1430.md`)

3. Tell user: "Saved to ./claude/interviews/interview-<timestamp>.md — ready to use as prompt context."

## Arguments
$ARGUMENTS
