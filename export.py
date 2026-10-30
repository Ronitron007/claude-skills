#!/usr/bin/env python3
"""Export global Claude skills into this repo, split by provenance.

authored  -> full copy (you wrote it)
vendored  -> full copy + provenance (third-party, no reinstall source, or locally modified)
cli       -> manifest + `npx skills add` restore line (~/.agents/.skill-lock.json)
plugin    -> manifest + `claude plugin install` restore line
account   -> manifest only (claude.ai skills re-sync on sign-in)
junk      -> listed, not exported

Every run rebuilds the generated files from scratch, so output is deterministic and
a run with no skill changes produces no commit.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME = Path.home()
CLAUDE = HOME / ".claude"
AGENTS = HOME / ".agents"
REPO = Path(__file__).resolve().parent
OVERRIDES = REPO / "overrides.json"
UPSTREAM_CACHE = REPO / ".cache/upstream.json"
ANTHROPIC_SKILLS = "anthropics/skills"
GENERATED = ["authored", "vendored", "manifest.json", "INDEX.md", "restore.sh"]
SKIP_NAMES = {"__pycache__", ".DS_Store", "node_modules", ".git"}
SECRET_RE = re.compile(
    r"(sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}"
    r"|AKIA[0-9A-Z]{16}|xox[abp]-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
BATCH_MIN = 3  # skills sharing one SKILL.md mtime second = one installer run
MODIFIED_SLACK_S = 120  # file newer than lock updatedAt by more than this = local edit


def frontmatter(md: Path) -> dict:
    text = md.read_text(errors="replace")
    out = {}
    if not text.startswith("---"):
        return out
    for line in text.split("\n---", 1)[0].splitlines()[1:]:
        m = re.match(r"\s*(name|description|author|license|source)\s*:\s*(.*)", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip().strip("\"'")
    return out


def files_of(path: Path):
    if path.is_file():
        yield path
        return
    for root, dirs, files in os.walk(path, followlinks=True):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_NAMES)
        for f in sorted(files):
            if f not in SKIP_NAMES and not f.endswith(".pyc"):
                yield Path(root) / f


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plugin_skill_index() -> dict:
    """SKILL.md sha -> plugin id, and dir name -> plugin id, from the plugin cache."""
    by_hash, by_name = {}, {}
    installed = json.loads((CLAUDE / "plugins/installed_plugins.json").read_text())["plugins"]
    for pid, installs in installed.items():
        for inst in installs:
            for md in Path(inst["installPath"]).glob("**/skills/*/SKILL.md"):
                by_hash[sha(md)] = pid
                by_name.setdefault(md.parent.name, pid)
    return by_hash, by_name


def collect():
    lock = {}
    lock_file = AGENTS / ".skill-lock.json"
    if lock_file.exists():
        lock = json.loads(lock_file.read_text())["skills"]
    overrides = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}
    by_hash, by_name = plugin_skill_index()
    upstream = upstream_check(lock)

    # gather candidate skill paths: ~/.claude/skills first, then ~/.agents/skills not linked into it
    # (a same-name copy in ~/.agents/skills is the same skill installed for other agents)
    cands, seen = [], set()
    for root in (CLAUDE / "skills", AGENTS / "skills"):
        if not root.exists():
            continue
        for p in sorted(root.iterdir()):
            if p.name == "synced" or p.name.startswith(".") or p.name in seen:
                continue
            seen.add(p.name)
            cands.append({"name": p.name, "path": p, "real": p.resolve(), "linked": root == CLAUDE / "skills"})

    # one installer run writes many skills within a second or two; a human does not
    mtimes = {c["name"]: int((c["real"] / "SKILL.md").stat().st_mtime)
              for c in cands if (c["real"] / "SKILL.md").exists()}

    def batch(t):
        names = sorted(n for n, m in mtimes.items() if abs(m - t) <= 2)
        if len(names) < BATCH_MIN:
            return ""
        srcs = sorted({lock[n]["source"] for n in names if n in lock})
        return f"batch install of {len(names)} skills" + (f" incl. skills from {', '.join(srcs)}" if srcs else "")

    entries, pending = [], []
    for c in cands:
        name, real = c["name"], c["real"]
        md = real / "SKILL.md"
        e = {"name": name, "kind": "skill", "path": tilde(c["path"]), "linked_to_claude": c["linked"]}
        if not md.exists():
            e |= cls("junk", f"no SKILL.md ({'file' if real.is_file() else 'dir'})")
        elif name in overrides:
            e |= cls(overrides[name], "override in overrides.json")
        elif name in lock:
            lk = lock[name]
            e |= cls("cli", f"in ~/.agents/.skill-lock.json from {lk['source']}")
            e["source"] = lk.get("sourceUrl") or lk["source"]
            e["skill_path"] = lk.get("skillPath")
            newest = newest_mtime(real)
            if upstream.get(upstream_url(e["source"], e["skill_path"])) is False:
                e |= cls("vendored", e["evidence"] + f"; upstream no longer has {e['skill_path']}")
            elif newest > iso_ts(lk["updatedAt"]) + MODIFIED_SLACK_S:
                by = batch(int(newest))
                if by:
                    e["evidence"] += f"; rewritten later by {by} (inferred)"
                else:
                    e |= cls("vendored", e["evidence"] + "; files edited after install")
        elif sha(md) in by_hash:
            e |= cls("plugin", f"SKILL.md identical to plugin {by_hash[sha(md)]}")
            e["plugin"] = by_hash[sha(md)]
        elif name in by_name:
            e |= cls("vendored", f"same name as plugin {by_name[name]} skill, content differs")
        else:
            fm = frontmatter(md)
            if fm.get("author") or fm.get("license"):
                e |= cls("vendored", f"frontmatter author={fm.get('author')} license={fm.get('license')}")
            else:
                pending.append(e)
        e["description"] = frontmatter(md).get("description", "") if md.exists() else ""
        e["_real"] = real
        entries.append(e)

    for e in pending:
        by = batch(mtimes[e["name"]])
        if by:
            e |= cls("vendored", f"{by} (inferred)")
        else:
            e |= cls("authored", "no lock, plugin, or vendor metadata")

    for md in sorted((CLAUDE / "commands").glob("*.md")):
        name = md.stem
        e = {"name": name, "kind": "command", "path": tilde(md), "_real": md,
             "description": frontmatter(md).get("description", "")}
        e |= cls(overrides.get(name, "authored"), "override" if name in overrides else "~/.claude/commands")
        entries.append(e)

    # the synced folder name holds account ids, so keep it out of the export
    acct = []
    for mf in sorted((CLAUDE / "skills/synced").glob("*/manifest.json")):
        for s in json.loads(mf.read_text())["skills"]:
            acct.append({"name": s["name"], "kind": "skill", "path": "claude.ai",
                         "description": s.get("description", ""), "source": s.get("source")}
                        | cls("account", f"claude.ai synced ({s.get('source')})"))
    # claude.ai does not sync to a headless machine, but some of these are public in anthropics/skills
    pub = {a["name"]: {"source": ANTHROPIC_SKILLS, "skillPath": f"skills/{a['name']}/SKILL.md"}
           for a in acct if a["source"] in ("anthropic", "anthropic-example")}
    found = upstream_check(pub)
    for a in acct:
        if a["name"] in pub and found.get(upstream_url(ANTHROPIC_SKILLS, pub[a["name"]]["skillPath"])):
            a["public_in"] = ANTHROPIC_SKILLS
            a["evidence"] += f"; public in {ANTHROPIC_SKILLS}"
    return entries + acct


def cls(c, evidence):
    return {"class": c, "evidence": evidence}


def tilde(p) -> str:
    """Home-relative path: portable across machines, and no username in a public repo."""
    s = str(p)
    return "~" + s[len(str(HOME)):] if s.startswith(str(HOME)) else s


def upstream_url(source: str, skill_path: str):
    m = re.match(r"(?:https://github\.com/)?([\w.-]+/[\w.-]+?)(?:\.git)?/?$", source or "")
    return f"https://raw.githubusercontent.com/{m.group(1)}/HEAD/{skill_path}" if m and skill_path else None


def head(url):
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=8)
        return True
    except urllib.error.HTTPError as err:
        return False if err.code == 404 else None
    except OSError:
        return None


def upstream_check(lock: dict) -> dict:
    """url -> True/False if the GitHub repo still has the skill on its default branch.
    Unknown (offline) urls are absent. Cached for a day so the hourly run stays offline."""
    cache = json.loads(UPSTREAM_CACHE.read_text()) if UPSTREAM_CACHE.exists() else {}
    urls = {u for lk in lock.values() if (u := upstream_url(lk.get("sourceUrl") or lk["source"], lk.get("skillPath")))}
    stale = [u for u in urls if u not in cache or time.time() - cache[u][0] > 86400]
    with ThreadPoolExecutor(16) as pool:
        for u, found in zip(stale, pool.map(head, stale)):
            if found is not None:
                cache[u] = [time.time(), found]
    if stale:
        UPSTREAM_CACHE.parent.mkdir(exist_ok=True)
        UPSTREAM_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True))
    return {u: v[1] for u, v in cache.items()}


def newest_mtime(path: Path) -> float:
    return max((f.stat().st_mtime for f in files_of(path)), default=0)


def iso_ts(s: str) -> float:
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def plugins():
    installed = json.loads((CLAUDE / "plugins/installed_plugins.json").read_text())["plugins"]
    markets = json.loads((CLAUDE / "plugins/known_marketplaces.json").read_text())
    enabled = json.loads((CLAUDE / "settings.json").read_text()).get("enabledPlugins", {})
    plist = []
    for pid, installs in sorted(installed.items()):
        for inst in installs:
            if inst["scope"] != "user":
                continue
            plist.append({"id": pid, "version": inst.get("version"), "enabled": enabled.get(pid, False)})
    mlist = []
    for name, m in sorted(markets.items()):
        src = m["source"]
        ref = src.get("repo") or src.get("url") or src.get("path")
        mlist.append({"name": name, "type": src["source"], "ref": tilde(ref),
                      "missing": src["source"] == "directory" and not Path(ref).exists()})
    return plist, mlist


def export(entries, plist, mlist):
    for g in GENERATED:
        p = REPO / g
        shutil.rmtree(p) if p.is_dir() else p.unlink(missing_ok=True)

    secrets = []
    for e in entries:
        if e["class"] not in ("authored", "vendored"):
            continue
        sub = "commands" if e["kind"] == "command" else "skills"
        dest = REPO / e["class"] / sub / (e["name"] + (".md" if e["kind"] == "command" else ""))
        src = e["_real"]
        for f in files_of(src):
            rel = f.relative_to(src) if src.is_dir() else Path()
            out = dest / rel if src.is_dir() else dest
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
            try:
                if SECRET_RE.search(f.read_text()):
                    secrets.append(str(out.relative_to(REPO)))
            except UnicodeDecodeError:
                pass
        e["exported_to"] = str(dest.relative_to(REPO))
        if e["class"] == "vendored":
            (dest.parent / f"{e['name']}.provenance.json").write_text(
                json.dumps({k: e[k] for k in ("name", "path", "evidence")}, indent=2) + "\n")

    clean = [{k: v for k, v in e.items() if not k.startswith("_")} for e in entries]
    clean.sort(key=lambda e: (e["class"], e["kind"], e["name"]))
    (REPO / "manifest.json").write_text(
        json.dumps({"skills": clean, "plugins": plist, "marketplaces": mlist}, indent=2) + "\n")
    (REPO / "INDEX.md").write_text(index_md(clean, plist, mlist))
    rs = REPO / "restore.sh"
    rs.write_text(restore_sh(clean, plist, mlist))
    rs.chmod(0o755)
    return secrets


def index_md(entries, plist, mlist):
    counts = Counter(e["class"] for e in entries)
    lines = ["# Skill index", "", "Generated by `export.py`. Do not edit.", "",
             "| Class | Count | Handling |", "|---|---|---|"]
    handling = {"authored": "full copy in `authored/`", "vendored": "full copy in `vendored/`",
                "cli": "reinstall line in `restore.sh`", "plugin": "comes with its plugin",
                "account": "re-syncs from claude.ai", "junk": "not exported"}
    for c in handling:
        if counts[c]:
            lines.append(f"| {c} | {counts[c]} | {handling[c]} |")
    lines += ["", "| Name | Kind | Class | Evidence | Description |", "|---|---|---|---|---|"]
    for e in entries:
        d = e.get("description", "").replace("|", "/").replace("\n", " ")
        d = d[:110] + "..." if len(d) > 110 else d
        lines.append(f"| `{e['name']}` | {e['kind']} | {e['class']} | {e['evidence']} | {d} |")
    lines += ["", "## Plugins (user scope)", "", "| Plugin | Version | Enabled |", "|---|---|---|"]
    lines += [f"| `{p['id']}` | {p['version']} | {p['enabled']} |" for p in plist]
    lines += ["", "## Marketplaces", "", "| Name | Type | Ref | Note |", "|---|---|---|---|"]
    lines += [f"| `{m['name']}` | {m['type']} | {m['ref']} | {'source path missing' if m['missing'] else ''} |"
              for m in mlist]
    return "\n".join(lines) + "\n"


RESTORE_HEAD = r'''#!/usr/bin/env bash
# Generated by export.py. Restores skills on a new machine (macOS or Linux).
# Safe to re-run: copies never delete, and a failed install only prints a warning.
set -uo pipefail
cd "$(dirname "$0")"
FAILED=0
have() { command -v "$1" >/dev/null 2>&1 || { echo "skip: '$1' not found, $2 not restored" >&2; return 1; }; }
try() { "$@" || { echo "warn: failed: $*" >&2; FAILED=$((FAILED + 1)); }; }
mkdir -p ~/.claude/skills ~/.claude/commands

# authored + vendored: copy back
for c in authored vendored; do
  for d in "$c"/skills/*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d"); mkdir -p ~/.claude/skills/"$n" && cp -R "$d". ~/.claude/skills/"$n"/
  done
  for f in "$c"/commands/*.md; do [ -f "$f" ] && cp "$f" ~/.claude/commands/; done
done
echo "copied authored + vendored skills"
'''


def restore_sh(entries, plist, mlist):
    q = lambda s: "'" + s.replace("'", "'\\''") + "'"
    out = [RESTORE_HEAD, "if have claude 'plugins'; then"]
    missing = {m["name"] for m in mlist if m["missing"]}
    for m in mlist:
        line = f"  try claude plugin marketplace add {q(m['ref'])}"
        out.append(f"  # local source, not on this machine: {line.strip()}" if m["missing"] else line)
    for p in plist:
        if p["id"].split("@")[-1] in missing:
            out.append(f"  # marketplace source missing: try claude plugin install {q(p['id'])}")
            continue
        out.append(f"  try claude plugin install {q(p['id'])} --scope user")
        if not p["enabled"]:
            out.append(f"  try claude plugin disable {q(p['id'])}")
    out.append("fi")

    by_src = {}
    for e in entries:
        if e["class"] == "cli":
            by_src.setdefault((e["source"], e.get("linked_to_claude")), []).append(e["name"])
    out += ["", "if have npx 'skills CLI skills'; then"]
    for (src, linked), names in sorted(by_src.items()):
        line = f"try npx -y skills add {q(src)} -g -a claude-code -y -s {' '.join(q(n) for n in sorted(names))}"
        out.append(f"  {line}" if linked else f"  # installed for other agents only: {line}")
    pub = sorted(e["name"] for e in entries if e["class"] == "account" and e.get("public_in"))
    if pub:
        out += ["  # claude.ai skills: the desktop app syncs them, so install only where it does not",
                "  [ -d ~/.claude/skills/synced ] || try npx -y skills add "
                f"{q(ANTHROPIC_SKILLS)} -g -a claude-code -y -s {' '.join(q(n) for n in pub)}"]
    out.append("fi")

    acct = sorted(e["name"] for e in entries if e["class"] == "account" and not e.get("public_in"))
    if acct:
        out += ["", f"# claude.ai account skills, not restorable from here: {', '.join(acct)}"]
    out += ['', 'echo "restore done, $FAILED failed step(s)"', '[ "$FAILED" -eq 0 ]']
    return "\n".join(out) + "\n"


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)


def gitleaks_staged() -> str:
    """Findings text, or "" when clean. No gitleaks: SECRET_RE in export() is the only check."""
    exe = shutil.which("gitleaks")
    if not exe:
        print("warn: gitleaks not found, secret check is regex only", file=sys.stderr)
        return ""
    r = subprocess.run([exe, "git", "--pre-commit", "--staged", "--redact", "-v", "--no-banner",
                        "-c", str(REPO / ".gitleaks.toml"), str(REPO)], capture_output=True, text=True)
    return "" if r.returncode == 0 else (r.stdout + r.stderr).strip()


def commit(push: bool):
    if git("rev-parse", "--git-dir").returncode != 0:
        return "not a git repo, skipped commit"
    git("add", "-A")
    if git("diff", "--cached", "--quiet").returncode == 0:
        return "no changes"
    leak = gitleaks_staged()
    if leak:
        git("reset", "-q")
        if sys.platform == "darwin":  # launchd runs are silent otherwise
            subprocess.run(["osascript", "-e", 'display notification "possible secret, sync stopped. '
                            'See .logs/export.log" with title "claude-skills"'])
        raise SystemExit("gitleaks blocked the commit (repo is public):\n" + leak)
    stat = git("diff", "--cached", "--name-status", "--", "authored", "vendored").stdout
    names = lambda st: sorted({l.split("\t")[-1].split("/")[2].removesuffix(".md")
                               for l in stat.splitlines()
                               if l[0] in st and l.count("/") >= 2 and not l.endswith(".provenance.json")})
    added, removed, changed = names("A"), names("D"), names("M")
    parts = [f"{s}{','.join(n)}" for s, n in (("+", added), ("-", removed), ("~", changed)) if n]
    msg = "sync: " + (" ".join(parts) or "manifest update")
    r = git("commit", "-q", "-m", msg[:200])
    if r.returncode != 0:
        return "commit failed: " + r.stderr.strip()
    if push and git("remote").stdout.strip():
        p = git("push", "-q")
        return msg + ("" if p.returncode == 0 else " (push failed: " + p.stderr.strip() + ")")
    return msg


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    # launchd drops change events that land while a run is in progress, so re-run until stable
    for _ in range(3):
        before = watched_signature()
        entries = collect()
        plist, mlist = plugins()
        secrets = export(entries, plist, mlist)
        print(", ".join(f"{c}={n}" for c, n in sorted(Counter(e["class"] for e in entries).items())))
        if secrets:
            print("possible secrets, not committing:\n  " + "\n  ".join(secrets), file=sys.stderr)
            return 1
        if not a.no_commit:
            print(commit(push=not a.no_push))
        if watched_signature() == before:
            break
    return 0


def watched_signature():
    paths = [CLAUDE / "skills", CLAUDE / "commands", AGENTS / "skills", AGENTS / ".skill-lock.json",
             CLAUDE / "plugins/installed_plugins.json", CLAUDE / "plugins/known_marketplaces.json"]
    return [(str(p), p.stat().st_mtime_ns) for p in paths if p.exists()]


if __name__ == "__main__":
    sys.exit(main())
