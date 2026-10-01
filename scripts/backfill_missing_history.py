#!/usr/bin/env python3
"""
One-time (re-runnable) backfill for posts that WERE actually generated and
merged to their live publish repo, but are missing from
content/dashboard_topic_index.json because content_indexer_agent's
snapshot never had them - confirmed via a real user report: a post
published 2026-09-30 (merged PR #78 in aspose-cloud-blog, 13:30 UTC,
~27 minutes before orchestrator.py's append_new_post() hook went live)
was missing, and checking further found the gap goes back to March 2026 -
not just that narrow window, a real partial hole in the snapshot itself.

Source: content/blogPosts/<brand_dir>/<post-folder>/index.md - this same
repo's own mirror of every post the generator has ever produced,
independent of content_indexer_agent entirely. Idempotent: only posts
not already present (matched by title) are added, safe to re-run.

Usage: python scripts/backfill_missing_history.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Set

import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dashboard_topic_index as bi  # noqa: E402  (reuse _resolve_platform / platforms_for_unresolved)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent_engine" / "blog_generator"))
from utils.topic_index import product_family_from_category  # noqa: E402  (reuse, don't redefine a third time)

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "content" / "dashboard_topic_index.json"
BLOG_POSTS_DIR = REPO_ROOT / "content" / "blogPosts"

# groupdocs_com intentionally excluded - out of dashboard scope, same as
# every other script in this pipeline.
BRAND_DIR_MAP = {
    "aspose_cloud": "aspose.cloud",
    "aspose_com": "aspose.com",
    "conholdate_cloud": "conholdate.cloud",
    "conholdate_com": "conholdate.com",
    "groupdocs_cloud": "groupdocs.cloud",
}

FIXED_PRODUCT_BRANDS = {"conholdate.com": "Conholdate.Total", "conholdate.cloud": "Conholdate.Total"}


def main() -> None:
    index: Dict[str, List[dict]] = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    indexed_titles: Set[str] = {
        e["title"].strip().lower() for entries in index.values() for e in entries if e.get("title")
    }

    added = 0
    skipped_no_title = 0
    for brand_dir, brand in BRAND_DIR_MAP.items():
        root = BLOG_POSTS_DIR / brand_dir
        if not root.exists():
            continue
        for post_dir in sorted(root.glob("*/")):
            index_md = post_dir / "index.md"
            if not index_md.exists():
                continue
            try:
                post = frontmatter.loads(index_md.read_text(encoding="utf-8", errors="ignore"))
            except Exception as exc:
                print(f"⚠️ Could not parse {index_md}: {exc}", flush=True)
                continue

            title = str(post.get("title") or "").strip()
            if not title:
                skipped_no_title += 1
                continue
            if title.lower() in indexed_titles:
                continue  # already covered - either in the original snapshot or a prior backfill

            if brand in FIXED_PRODUCT_BRANDS:
                product = FIXED_PRODUCT_BRANDS[brand]
            else:
                categories = post.get("categories") or []
                if isinstance(categories, str):
                    categories = [categories]
                category = categories[0] if categories else ""
                product = product_family_from_category(category) or "Unknown"

            url_path = str(post.get("url") or "")
            date = str(post.get("date") or "")
            entry = {"title": title, "url": f"https://blog.{brand}{url_path}" if url_path else "", "date": date}

            resolved = bi._resolve_platform({"platform": None}, title)
            if resolved:
                platforms = [resolved]
            else:
                # Fall back to whichever platforms are ALREADY established
                # for this product in the current, real index - not just
                # this batch - same capped-expansion rule as every other
                # script in this pipeline.
                existing_platforms = sorted(
                    {
                        k.split("|")[-1]
                        for k in index
                        if k.startswith(f"{brand}|{product}|") and k.split("|")[-1] != "general"
                    }
                )
                platforms = bi.platforms_for_unresolved(existing_platforms)

            dedupe_key = entry["url"] or entry["title"]
            new_for_this_post = False
            for p in platforms:
                key = f"{brand}|{product}|{p}"
                bucket = index.setdefault(key, [])
                if any((e.get("url") or e.get("title")) == dedupe_key for e in bucket):
                    continue
                bucket.append(entry)
                added += 1
                new_for_this_post = True
            if new_for_this_post:
                indexed_titles.add(title.lower())
                print(f"  + {brand}|{product}|{'+'.join(platforms)}: {title!r}", flush=True)

    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(
        f"\nDone. {added} (bucket,post) pairs added ({skipped_no_title} local posts skipped - no title in front matter). "
        f"Total buckets now: {len(index)}."
    )


if __name__ == "__main__":
    main()
