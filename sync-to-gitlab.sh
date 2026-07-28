#!/bin/bash
# sync-to-gitlab.sh — syncs ALL new commits to GitLab with original authorship
# Run daily after pushing to GitHub

GITHUB_REPO=/Users/mustafa/Desktop/conholdate-blog
GITLAB_REPO=/Users/mustafa/Desktop/gitlab/blog-post-generator   # ← FIX THIS PATH

cd "$GITHUB_REPO" || exit 1
mkdir -p /tmp/lab-patches && rm -f /tmp/lab-patches/*.patch

git format-patch lab-sync..main -o /tmp/lab-patches --quiet

if [ -z "$(ls -A /tmp/lab-patches 2>/dev/null)" ]; then
  echo "Nothing new to sync"
  exit 0
fi

COUNT=$(ls /tmp/lab-patches/*.patch | wc -l | tr -d ' ')

cd "$GITLAB_REPO" || exit 1
git am /tmp/lab-patches/*.patch || {
  echo "⚠️  Patch conflict — resolve the file, then: git am --continue && git push"
  echo "    (or abort with: git am --abort)"
  exit 1
}
git push

cd "$GITHUB_REPO"
git tag -f lab-sync main
rm -rf /tmp/lab-patches
echo "✅ Synced $COUNT commits to GitLab"