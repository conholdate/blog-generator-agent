#!/bin/bash
# sync-to-gitlab.sh — syncs ALL new commits to GitLab with original authorship
# Excludes this script itself and handles logs.txt drift automatically.
# Run daily after pushing to GitHub.

set -e

GITHUB_REPO=/Users/mustafa/Desktop/conholdate-blog
GITLAB_REPO=/Users/mustafa/Desktop/gitlab/blog-post-generator   # confirm this path is correct

cd "$GITHUB_REPO" || exit 1
mkdir -p /tmp/lab-patches && rm -f /tmp/lab-patches/*.patch

# Generate patches for everything since last sync, EXCLUDING this script file,
# the logs file (handled separately below, not via patch), and audit reports
# (generated output that diverges between independently-run clones and isn't
# meant to be synced at all).
git format-patch lab-sync..main -o /tmp/lab-patches --quiet \
  -- . ':!sync-to-gitlab.sh' ':!content/logs/logs.txt' ':!outputs/audit/*'

if [ -z "$(ls -A /tmp/lab-patches 2>/dev/null)" ]; then
  echo "Nothing new to sync"
  # still refresh logs.txt in case it's the only thing that changed
else
  COUNT=$(ls /tmp/lab-patches/*.patch | wc -l | tr -d ' ')
fi

cd "$GITLAB_REPO" || exit 1

if [ -n "$(ls -A /tmp/lab-patches 2>/dev/null)" ]; then
  git am /tmp/lab-patches/*.patch || {
    echo "⚠️  Patch conflict — resolve the file, then: git am --continue && git push"
    echo "    (or abort with: git am --abort)"
    exit 1
  }
fi

# Always bring logs.txt to the current GitHub state directly (no patching).
# This avoids repeated conflicts since the GitHub Action appends to it constantly.
if ! cmp -s "$GITHUB_REPO/content/logs/logs.txt" "content/logs/logs.txt" 2>/dev/null; then
  cp "$GITHUB_REPO/content/logs/logs.txt" content/logs/logs.txt
  git add content/logs/logs.txt
  git commit -m "Sync logs.txt with source repo" --quiet
  echo "📝 logs.txt updated"
fi

git push

cd "$GITHUB_REPO"
git tag -f lab-sync main
rm -rf /tmp/lab-patches

if [ -n "$COUNT" ]; then
  echo "✅ Synced $COUNT commits to GitLab"
else
  echo "✅ Sync complete (logs only, or nothing new)"
fi