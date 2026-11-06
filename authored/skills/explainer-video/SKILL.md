---
name: explainer-video
description: Make a narrated, 3Blue1Brown-style explainer video of a code system, design or spec — Manim animation, narration in Simplified Technical English, an independent fact-check before any recording, and the voice recorded through the voiceover skill. Use this whenever the user asks for an explainer video, a walkthrough video, a "3b1b style" video, a narrated animation of how something works, or a video version of a doc, even if they only say "make a video about X" or "explain X in a video".
---

# Explainer video

An explainer video costs effort twice. A recording goes out to an outside voice agent in the user's name, and a wrong sentence teaches the viewer something false. So the order of work matters more than any single step. Truth first, then recording, then pixels.

```
viewer model + term questions + prior-art fan-out ──► "teach / assume" yes
   │
   ▼
script ──► independent fact-check ──► corrections ──► re-check ──► voiceover skill ──► takes
 (deep, STE, lint 0.00)  (fresh agent, runs code)          (fresh agent)   (its approval rule)
                                                                                     │
                     deliver ◄── mux + concat ◄── animate to real audio lengths ◄────┘
           (full file + phone copy)                (Manim, durations.json)
```

## Rules that hold for every video, and why

1. **Depth of understanding is the point, not depth of detail.** The viewer wants a mental model, top down. A video that uses words the viewer does not know is dense, however true it is: on 2026-11-04 Rohan stopped a 95-scene script for that reason. Teach each new concept before use, and move detail the model does not need to the cut list. `stage.viewer` and `stage.script` set the bar.
2. **Nothing is recorded before the fact-check passes.** On an earlier video, a "fix" made from one file, without reading the other, turned a true sentence false after it was already recorded. The later fact-check found 2 wrong and 12 partly wrong claims out of 386. Checking text is cheap; re-recording is not.
3. **Record the voice with the `voiceover` skill.** Load it and follow its steps, including its approval rule.
4. **Store every output durably from the first minute.** The session scratchpad is wiped across days and even on a session restart. Keep recordings, ledgers and reports under `~/kyaloon-media/<slug>/`, and commit code to the branch after each working part.
5. **Patch mistakes; do not re-record whole scenes.** When a fact changes after recording, re-record only the changed sentences and splice them in (`stage.patch`).
6. **Names, not numbers, in the narration.** Say "get category context", not "step one". The user's naming rule applies to spoken text too, and a recording cannot be edited.
7. **Re-check live state just before recording the late scenes.** Rulings, switches and open PRs change while the video is in progress. A limits scene written in the morning can be stale by the afternoon.

## Where things live

- **Script and Manim code:** `docs/superpowers/explainers/YYYY-MM-DD-<slug>/` in a worktree that the session is isolated in. A hook blocks writes outside it; if needed, move the worktree under `.claude/worktrees/` and enter it. Commit there. A docs-only PR merges straight away with `[skip ci]`.
- **Media** (recordings, final audio, renders, final MP4, ledgers, notes, reports): `~/kyaloon-media/<slug>/`. The voiceover skill saves raw recordings to `~/Voiceovers/`; copy them into the media folder at once. Media never goes into git.
- **Manim:** Manim Community in `~/.venvs/kyaloon-manim` (Python 3.13; 3.14 lacks wheels). If it is missing: `uv venv --python /opt/homebrew/bin/python3.13 ~/.venvs/kyaloon-manim && uv pip install --python ~/.venvs/kyaloon-manim/bin/python manim`. Cairo and Pango come from Homebrew. No LaTeX: use `Text`, `MarkupText` and `Code`, never `MathTex`.

## `stage.viewer` (before the script)

The viewer model is `viewer-rohan.md` (next to this file). It lists what Rohan knows, what is new to him, and his word choices, each with evidence.

1. List every concept the video needs, from the outline down to its foundations.
2. Mark each one `known` or `teach` from the viewer model. When there is even a little doubt, ask Rohan ("do you know X, or should we walk it?"). He wants to be asked. Use `AskUserQuestion` with multi-select, four terms per question. Never guess a term into `known`.
3. Fan out research agents, one per concept cluster, to find existing explainers of the `teach` concepts: how they teach each one (analogy, picture, tiny example, order of ideas) and what they assume. Each agent writes a teaching ladder for this viewer. Record them in the media folder.
4. Show Rohan one screen, "terms I will teach" and "terms I will assume", and get his yes. Then write the script.
5. After the video, and after each Q&A chat, move what he learned to `known` in the viewer model.

## `stage.script`

Read the code at the commit that actually runs, for example the deployed staging SHA, not a branch in progress.

**Creation rules.** The script passes only when each of these holds:

- `rules.term_gate`: `terms.md` lists every technical term that the voice says, as `known` or `teach` with the scene that teaches it. `scripts/term_gate.py <narration.md> <terms.md>` exits 0: each new term is taught before its first use, and is used again after it is taught (a term used only once is cut, not taught).
- `rules.term_budget`: a scene teaches at most two new terms (the gate checks it).
- `rules.floor_first`: the video starts at the viewer's floor. Each `teach` concept gets a plain analogy and a tiny example, from the research ladders, before the video builds on it.
- `rules.general_then_ours`: explain a concept in general first, then "in this codebase".
- `rules.keep_test`: a fact goes into the voice only if the next idea needs it, it answers a question the viewer asked, it changes a decision the viewer must make, or it fixes a likely wrong belief. Implementation detail (file:line, file descriptor numbers, build variants), edge cases that do not change the mental model, exact numbers that are not the point, and second examples go to `cuts.md`, grouped by scene. Rohan skims `cuts.md` before any recording.
- `rules.scene_shape`: one question, one answer, one example, one takeaway.

**The depth bar.** The script passes only when each of these holds:

- **Top down.** One outline diagram of the whole path comes first. The video then walks it box by box and returns to it between parts.
- **Every box, at the depth of the mental model.** For each box: what it does, what it reads and writes, and each rule with its reason, in the words the viewer has. Failure paths and limits go in when they pass `rules.keep_test`. The rest goes to `cuts.md`.
- **Every term, defined.** A term that a newcomer to this codebase would not know is defined at first use, and again in `glossary.md`. Project words, table names, tool names and abbreviations all count.
- **Every concept the user named, in depth.** When the user names a confusing idea (for example "constraint versus condition"), it gets its own scenes: what each is, who writes it, what data it is checked against, which code checks it, what results it can give, how options change it, and a side-by-side table.
- **One worked example with real data, through every box.** Run the real code on a fixture or a read-only export, and show its real inputs and outputs. Label anything a model would produce (plans, verdicts) as illustrative.
- **The limits, stated plainly**, with numbers.
- **One idea per scene.** Length follows content, not a target. The find_products video needed 51 scenes and about 40 minutes.

Files: `script.md` (each scene: snake_case name, target length, narration, visuals), `narration.md` (only what the voice reads, one `## <scene_name>` block per scene, a blank line between blocks), `glossary.md`, and `sources.md` (each claim with its file:line, labeled verified or inferred).

Write the narration in ASD-STE100: load the `ste-writing` skill and lint `narration.md` with `python3 ~/.claude/skills/ste-writing/ste-lint.py` until it scores 0.00. Spell numbers for the voice ("one thousand four hundred thirty-one"), and speak code names as words ("find products"). Put the written forms in the visuals.

## `stage.factcheck`

Brief a **fresh** Opus agent that did not write the script. It checks **every** narration sentence, not a sample:

- It splits the narration into atomic claims and gives each a verdict (verified, wrong, partly wrong, unverifiable) with evidence: a file:line quote, or a command it ran and that command's output.
- It runs code where it can. A throwaway local database loaded with the test fixture beats reading.
- It also checks the numbers, code names and table cells that the visuals show.
- It marks every scene whose audio already exists.

Then apply the corrections, and confirm each one against the cited code before it goes in. Next, have a **second fresh agent** re-check only the changed sentences. Repeat until no claim is wrong. Keep `factcheck.md` and the re-check in the media folder, not the scratchpad.

## `stage.voice`

1. Load the `voiceover` skill and run its `check`.
2. Plan the sends with the user once:
   - **One send per scene:** clean timing for each scene, but many sends.
   - **One send per part:** few yeses, but each part is then split into scenes at the pauses (`ffmpeg -af silencedetect`). Check each scene's length against its share of the words.
3. Before each send, snapshot the exact text of each scene into `blocks/NN_<scene>.txt`. The patch step needs to know what was recorded.
4. For each send, follow the voiceover skill: write the script verbatim, run `compose`, apply its approval rule, then `send`. Use the full premise for the first send and `--short` for follow-ups.
5. After each send, copy the saved `.ogg` file(s) into `~/kyaloon-media/<slug>/takes/`, and add a row to `ledger.tsv` (scene or part, file, time sent).
6. Convert each take for the edit: `ffmpeg -i take.ogg -ar 48000 -ac 2 take.wav`. Read each length with ffprobe.

You cannot hear audio. Say so, and send the user one take early to judge the voice.

## `stage.patch` (only when text changes after recording)

1. Run `scripts/patch_runs.py <narration.md> <blocks-dir>`. It lists, per recorded scene, the runs of sentences that are new against the recorded text. Sentences that only moved are reused from the old audio, not re-recorded.
2. Record each run through the voiceover skill, as a `--short` follow-up.
3. Splice (an agent can do this):
   - Find the sentence and paragraph boundaries in the old take with `ffmpeg -af silencedetect` (about -35 dB, 0.25 s).
   - Cut at the middle of a silence. Keep natural pauses: about 0.35 s between sentences and 0.7 s between paragraphs.
   - Gain-match each patch to its take.
   - Write to `audio-final/`, never over an original.
   - Verify that every cut and every join sits inside a silence.
4. Send the trickiest patched take to the user to judge. A new send can sound different from the old one.

## `stage.animate`

Brief an Opus agent with `script.md`, the final audio folder, and these parts:

- `style.py`: a dark background, one fixed color per concept, and an `OutlineDiagram` anchor that can highlight a box and zoom into it.
- `timing.py`: reads `durations.json`. Each scene scales its beats so that its length matches its audio within 0.1 s.
- One module per part, with one `Scene` per script scene.
- `render_all.py` and `mux_all.py`.

Render at `-qm` (720p, 30 fps) into `~/kyaloon-media/<slug>/render/`. Take `durations.json` from ffprobe of the final takes. Keep text at least about 20 px tall at 720p, and reveal long tables and JSON row by row. The agent extracts mid-scene frames and looks at them (overlaps, text off screen) for a good share of the scenes. Then it muxes each scene with its take and joins the scenes in order.

## `stage.deliver`

- Write the final file to `~/kyaloon-media/<slug>/<slug>-v1.mp4`. Never overwrite; add a suffix. Check it with ffprobe: its duration matches the audio, and it has one video stream and one audio stream.
- `SendUserFile` reaches the phone only under 30 MiB. Also make a phone copy with `scripts/phone_copy.sh <input> <output>` (480p, 15 fps, two-pass, about 62 kbps video and 32 kbps mono audio). Look at one frame to confirm the text is still readable. Send the phone copy, and say where the full file is.
- Commit the script files and the Manim code. Open the docs PR and merge it.

## Briefing agents

Every agent brief carries:

- the worktree as the Bash working directory, and `git -C <path>` for any other repo;
- plain commands with literal paths (the guard refuses shell variables in option positions, loops and complex compound commands, so write a small Python script instead);
- durable output paths;
- "do not start background sub-agents";
- "send nothing to the voice agent" (recording stays with you, through the voiceover skill);
- a word cap for the report.

If an agent dies on a network error, check its files and resume it with `SendMessage` instead of starting over.

## Reference: the find_products video (2026-10-22)

51 scenes, 6,501 words, about 40 minutes. The fact-check checked 386 claims and ran 116 of the checks as code. Source: `docs/superpowers/explainers/2026-10-22-find-products-video/` in RealDose. Media: `~/kyaloon-media/explainer-find-products-2026-10-22/`. That video used ElevenLabs before the voiceover skill existed.
