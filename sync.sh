#!/usr/bin/env bash
# Sync this machine with GitHub: take main, restore, link, and send local changes as a PR.
# For machines that use the repo as their skills folder (see README "How this works").
# Never pushes to main and never force-pushes. Not for the main machine (it runs export.py).
set -uo pipefail
cd "$(dirname "$0")"; REPO=$PWD
HOST=${SKILLS_HOST:-$(cat .host 2>/dev/null || hostname -s)}
BRANCH=${SYNC_BRANCH:-sync/$HOST}
say() { echo "sync: $*"; }
case "$BRANCH" in main|master) say "refusing to use $BRANCH"; exit 1;; esac
[ -f "hosts/$HOST.sh" ] && . "hosts/$HOST.sh"
commit() { git add -A && { git diff --cached --quiet || git commit -q -m "sync($HOST): $1"; }; }

# 1. local edits first, on the sync branch, so nothing is lost
[ "$(git branch --show-current)" = "$BRANCH" ] || git checkout -q -B "$BRANCH" || exit 1
commit "local edits" || exit 1

# 2. take main (merge, not rebase: the branch may be pushed already, and we never force-push)
if git fetch -q origin main; then
  git merge -q --no-edit origin/main || { git merge --abort; say "conflict with origin/main; fix by hand, then re-run"; exit 1; }
else
  say "fetch failed; continuing with the local copy"
fi

# 3. restore + link + host policy
./restore.sh || say "restore.sh had failed steps (see warnings above)"
python3 link.py || exit 1
if declare -F host_post >/dev/null; then host_post; fi
commit "adopt and fix skills" || exit 1

# 4. nothing to send?
if git diff --quiet origin/main HEAD --; then
  git checkout -q -B "$BRANCH" origin/main
  say "in sync with main; nothing to push"; exit 0
fi

# 5. secret check, then push the branch and open or update its PR
command -v gitleaks >/dev/null || { say "gitleaks not found; not pushing"; exit 1; }
gitleaks git --log-opts="origin/main..HEAD" --redact --no-banner -c .gitleaks.toml . >/dev/null 2>&1 \
  || { say "gitleaks found a possible secret; not pushing. Run: gitleaks git --log-opts=origin/main..HEAD -v -c .gitleaks.toml ."; exit 1; }
REMOTE=$BRANCH
if ! git push -q origin "HEAD:refs/heads/$REMOTE" 2>/dev/null; then
  REMOTE="$BRANCH-$(date +%Y%m%d-%H%M)"   # remote branch moved on: use a new one, never force
  git push -q origin "HEAD:refs/heads/$REMOTE" || { say "push failed"; exit 1; }
fi
if command -v gh >/dev/null; then
  url=$(gh pr list --head "$REMOTE" --state open --json url -q '.[0].url' 2>/dev/null)
  [ -n "$url" ] || url=$(gh pr create --base main --head "$REMOTE" --title "sync: skills from $HOST" \
    --body "Local skill changes from \`$HOST\`, made by sync.sh. Review, then merge; the main machine's export picks them up." 2>&1 | tail -1)
  say "pushed $REMOTE: $url"
else
  say "pushed $REMOTE; open a PR against main"
fi
