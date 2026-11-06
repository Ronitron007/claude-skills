"""List the sentence runs to re-voice after the narration changed.

Usage: python3 -I patch_runs.py <narration.md> <blocks_dir>
<blocks_dir> holds NN_<scene>.txt: the exact text each existing take was generated from.
For each scene whose text changed, prints the runs of NEW sentences (sentences that appear nowhere in the
voiced text of that scene), their character count, and the total. Sentences that only moved are not listed:
reuse their old audio. Writes runs.json next to the blocks.
"""
import json
import os
import re
import sys

narration, blocks = sys.argv[1], sys.argv[2]
text = open(narration).read()
parts = re.split(r'^## (\S+)\s*$', text, flags=re.M)
current = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}
split = lambda t: [x for x in re.split(r'(?<=[.!?])\s+', t.strip()) if x]

runs, total = [], 0
for name in sorted(os.listdir(blocks)):
    if not name.endswith(".txt"):
        continue
    scene = name[3:-4]
    if scene not in current:
        print(f"!! {scene}: not in the narration any more")
        continue
    voiced = split(open(os.path.join(blocks, name)).read())
    new = split(current[scene])
    i = 0
    while i < len(new):
        if new[i] in voiced:
            i += 1
            continue
        j = i
        while j < len(new) and new[j] not in voiced:
            j += 1
        run = " ".join(new[i:j])
        runs.append({"scene": scene, "start_sentence": i, "end_sentence": j, "text": run, "chars": len(run)})
        total += len(run)
        i = j

json.dump(runs, open(os.path.join(blocks, "runs.json"), "w"), indent=1)
for r in runs:
    print(f"{r['scene']} s{r['start_sentence']}-{r['end_sentence']}: {r['chars']} chars")
print("runs", len(runs), "TOTAL chars (about the same in credits):", total)
