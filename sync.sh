#!/usr/bin/env bash
# Sync this machine with GitHub: take main, restore, link, and send local changes as a PR.
# For machines that use the repo as their skills folder (see README "How this works").
# Never pushes to main and never force-pushes. Not for the main machine (it runs export.py).
#   ./sync.sh           full sync (by hand)
#   ./sync.sh --record  light: link + commit + push/PR only, no pull/restore (used by bin/skill-sync-hook.sh)
set -uo pipefail
cd "$(dirname "$0")"; REPO=$PWD
RECORD=; [ "${1:-}" = --record ] && RECORD=1
HOST=${SKILLS_HOST:-$(cat .host 2>/dev/null || hostname -s)}
say() { echo "sync: $*"; }
# .sync-branch (untracked) pins the branch, e.g. an open PR's branch; dropped once that PR is closed
if [ -z "${SYNC_BRANCH:-}" ] && [ -f .sync-branch ] && [ -z "$RECORD" ] && command -v gh >/dev/null; then
  st=$(gh pr view "$(cat .sync-branch)" --json state -q .state 2>/dev/null)
  case "$st" in MERGED|CLOSED) say "PR for $(cat .sync-branch) is $st; back to sync/$HOST"; rm -f .sync-branch;; esac
fi
BRANCH=${SYNC_BRANCH:-$(cat .sync-branch 2>/dev/null || echo "sync/$HOST")}
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/skill-sync"; mkdir -p "$STATE"
exec 9>"$STATE/lock"
if [ -n "$RECORD" ]; then flock -n 9 || { say "another sync is running"; exit 1; }
else flock -w 900 9 || { say "another sync is still running"; exit 1; }; fi
case "$BRANCH" in main|master) say "refusing to use $BRANCH"; exit 1;; esac
[ -f "hosts/$HOST.sh" ] && . "hosts/$HOST.sh"
commit() { git add -A && { git diff --cached --quiet || git commit -q -m "sync($HOST): $1"; }; }

# 1. local edits first, on the sync branch, so nothing is lost. Switching never moves an existing
# sync branch backwards: -B only when the branch is new or HEAD already contains it.
if [ "$(git branch --show-current)" != "$BRANCH" ]; then
  if git show-ref -q --verify "refs/heads/$BRANCH" && ! git merge-base --is-ancestor "$BRANCH" HEAD; then
    git checkout -q "$BRANCH" || { say "cannot switch to $BRANCH (local changes conflict); commit or stash them, then re-run"; exit 1; }
  else
    git checkout -q -B "$BRANCH" || exit 1
  fi
fi
commit "local edits" || exit 1

# 2. take main (merge, not rebase: the branch may be pushed already, and we never force-push)
if [ -n "$RECORD" ]; then
  :  # record: no network pull, no restore
elif git fetch -q origin main; then
  git merge -q --no-edit origin/main || { git merge --abort; say "conflict with origin/main; fix by hand, then re-run"; exit 1; }
else
  say "fetch failed; continuing with the local copy"
fi

# 3. restore + link + host policy
[ -n "$RECORD" ] || ./restore.sh || say "restore.sh had failed steps (see warnings above)"
python3 link.py || exit 1
if [ -z "$RECORD" ] && declare -F host_post >/dev/null; then host_post; fi
commit "adopt and fix skills" || exit 1

# 4. nothing to send?
if git diff --quiet origin/main HEAD --; then
  [ -n "$RECORD" ] || git checkout -q -B "$BRANCH" origin/main
  say "in sync with main; nothing to push"; exit 0
fi

# 5. secret check, then push the branch and open or update its PR
[ "${SYNC_NO_PUSH:-0}" = 1 ] && { say "SYNC_NO_PUSH=1: committed, not pushing"; exit 0; }
command -v gitleaks >/dev/null || { say "gitleaks not found; not pushing"; exit 1; }
scan() {
  gitleaks git --log-opts="origin/main..HEAD" --redact --no-banner -c .gitleaks.toml . >/dev/null 2>&1 \
    || { say "gitleaks found a possible secret; not pushing. Run: gitleaks git --log-opts=origin/main..HEAD -v -c .gitleaks.toml ."; exit 1; }
}
scan
# push: fast-forward only. If the remote branch moved on (a commit added on GitHub, another
# machine), merge it and push again. Only if that merge conflicts, use one dated fallback branch
# and pin it in .sync-branch, so later runs reuse it and its PR instead of opening new ones.
push() { git push --porcelain origin "HEAD:refs/heads/$1" 2>/dev/null; }
REMOTE=$BRANCH
if ! out=$(push "$REMOTE"); then
  if ! git fetch -q origin "refs/heads/$REMOTE:refs/remotes/origin/$REMOTE" 2>/dev/null; then
    say "push failed (offline, no access, or the branch is protected); the next run retries"; exit 1
  fi
  if git merge -q --no-edit "origin/$REMOTE" && scan && out=$(push "$REMOTE"); then
    say "merged origin/$REMOTE (it had moved on)"
  else
    git merge --abort 2>/dev/null
    REMOTE="$BRANCH-$(date +%Y%m%d-%H%M)"   # never force: a new branch, remembered below
    out=$(push "$REMOTE") || { say "push failed"; exit 1; }
    git branch -q -f "$REMOTE" HEAD && git checkout -q "$REMOTE" && echo "$REMOTE" > .sync-branch
    say "origin/$BRANCH conflicts with this branch; using $REMOTE from now on (.sync-branch)"
  fi
fi
if grep -q '^=' <<<"$out"; then             # porcelain "=": the remote already had this commit
  say "$REMOTE is up to date; nothing new to push"; exit 0
fi
if command -v gh >/dev/null; then
  url=$(gh pr list --head "$REMOTE" --state open --json url -q '.[0].url' 2>/dev/null)
  [ -n "$url" ] || url=$(gh pr create --base main --head "$REMOTE" --title "sync: skills from $HOST" \
    --body "Local skill changes from \`$HOST\`, made by sync.sh. Review, then merge; the main machine's export picks them up." 2>&1 | tail -1)
  say "pushed $REMOTE: $url"
else
  say "pushed $REMOTE; open a PR against main"
fi
