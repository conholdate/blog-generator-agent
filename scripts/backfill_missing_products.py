#!/usr/bin/env python3
"""
One-time (re-runnable) backfill for products agent_engine/content_indexer_agent
never indexed AT ALL - confirmed by diffing its outputs/ directories against
every brand's real product list (blog-dashboard/lib/config.ts): entire
product folders are simply absent from its output, not a classification gap
like build_dashboard_topic_index.py's title-detection fixes (those handle
content that WAS indexed but mis-bucketed). A user hit this directly:
"Convert OneNote to PDF with Image Hyperlinks" (Aspose.Note, aspose.com) -
content_indexer_agent never processed Aspose.Note for aspose.com at all.

Scope (verified via `ls outputs/<brand>/` vs each brand's real product
list, 2026-10-01):
  aspose.cloud:    barcode, diagram, imaging, tasks        (4/14 missing)
  aspose.com:      3d, cad, font, llm, medical, note, ocr,
                    page, pub, svg, total, zip              (12/28 missing)
  groupdocs.cloud: metadata, rewriter, translation, viewer (4/14 missing)

Unlike build_dashboard_topic_index.py (reads content_indexer_agent's
already-indexed JSONL), this reads the REAL blog content directly - shallow
`git clone` of each affected brand's publish repo (once per brand, not once
per product - cheaper and simpler than cloning per-product), then walks
just the specific missing product folders and parses real front matter.
Reuses build_dashboard_topic_index's platform-detection logic
(_resolve_platform et al.) rather than duplicating it - there's no raw
`platform` field here at all (this is real front matter, not
content_indexer_agent's derived JSONL), so every post resolves via title
detection or falls through to the per-product "general" expansion, exactly
like that script's own fallback path.

Usage: python scripts/backfill_missing_products.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple

import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dashboard_topic_index as bi  # noqa: E402  (reuse _resolve_platform, not duplicate it)

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "content" / "dashboard_topic_index.json"

MISSING_PRODUCTS: Dict[str, dict] = {
    "aspose.cloud": {
        "repo": "aspose-cloud/aspose-cloud-blog",
        "branch": "master",
        "content_root": "content/Aspose.Cloud",
        "products": {
            "barcode": "Aspose.BarCode",
            "diagram": "Aspose.Diagram",
            "imaging": "Aspose.Imaging",
            "tasks": "Aspose.Tasks",
        },
    },
    "aspose.com": {
        "repo": "Aspose/aspose-blog",
        "branch": "master",
        "content_root": "content/Aspose.Blog",
        "products": {
            "3d": "Aspose.3D",
            "cad": "Aspose.CAD",
            "font": "Aspose.Font",
            "llm": "Aspose.LLM",
            "medical": "Aspose.Medical",
            "note": "Aspose.Note",
            "ocr": "Aspose.OCR",
            "page": "Aspose.Page",
            "pub": "Aspose.PUB",
            "svg": "Aspose.SVG",
            "total": "Aspose.Total",
            "zip": "Aspose.ZIP",
        },
    },
    "groupdocs.cloud": {
        "repo": "groupdocs-cloud/groupdocs-cloud-blog",
        "branch": "master",
        "content_root": "content/GroupDocs.Cloud",
        "products": {
            "metadata": "GroupDocs.Metadata",
            "rewriter": "GroupDocs.Rewriter",
            "translation": "GroupDocs.Translation",
            "viewer": "GroupDocs.Viewer",
        },
    },
}


def clone(repo: str, branch: str, dest: Path) -> None:
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, f"https://github.com/{repo}.git", str(dest)],
        check=True,
        capture_output=True,
        text=True,
    )


def load_product_posts(product_dir: Path) -> List[Tuple[dict, str]]:
    """Returns (entry, title) pairs for every index.md under a product
    folder. Front matter is parsed directly - no dependency on
    content_indexer_agent's derived fields."""
    out: List[Tuple[dict, str]] = []
    for post_file in sorted(product_dir.rglob("index.md")):
        try:
            post = frontmatter.loads(post_file.read_text(encoding="utf-8", errors="ignore"))
        except Exception as exc:
            print(f"  ⚠️ Could not parse {post_file}: {exc}", flush=True)
            continue
        title = str(post.get("title") or "").strip()
        if not title:
            continue
        out.append((post.metadata, title))
    return out


def main() -> None:
    index: Dict[str, List[dict]] = json.loads(INDEX_PATH.read_text(encoding="utf-8")) if INDEX_PATH.exists() else {}
    total_added = 0
    total_posts = 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for brand, cfg in MISSING_PRODUCTS.items():
            dest = tmp_path / brand.replace(".", "_")
            print(f"Cloning {cfg['repo']} ({cfg['branch']}) for {brand}...", flush=True)
            clone(cfg["repo"], cfg["branch"], dest)
            content_root = dest / cfg["content_root"]

            for slug, product_name in cfg["products"].items():
                product_dir = content_root / slug
                if not product_dir.exists():
                    print(f"  ⚠️ {slug} not found at {product_dir}, skipping", flush=True)
                    continue

                posts = load_product_posts(product_dir)
                total_posts += len(posts)

                # Same two-pass approach as build_dashboard_topic_index.py:
                # resolve each post's platform via title first, THEN expand
                # any still-unresolved ("general") post into whichever
                # platforms were genuinely resolved for this product.
                resolved: List[Tuple[dict, str | None]] = []
                for meta, title in posts:
                    url = str(meta.get("url") or "")
                    date = str(meta.get("date") or "")
                    entry = {"title": title, "url": f"https://blog.{brand}{url}" if url else "", "date": date}
                    platform = bi._resolve_platform({"platform": None}, title)
                    resolved.append((entry, platform))

                platforms_in_group = sorted({p for _, p in resolved if p})
                seen_per_bucket: Dict[str, Set[str]] = {}
                added_for_product = 0
                for entry, final_platform in resolved:
                    dedupe_key = entry["url"] or entry["title"]
                    platforms = [final_platform] if final_platform else bi.platforms_for_unresolved(platforms_in_group)
                    for platform in platforms:
                        key = f"{brand}|{product_name}|{platform}"
                        bucket_seen = seen_per_bucket.setdefault(key, set())
                        if dedupe_key in bucket_seen:
                            continue
                        bucket_seen.add(dedupe_key)
                        index.setdefault(key, []).append(entry)
                        total_added += 1
                        added_for_product += 1

                print(f"  {slug} ({product_name}): {len(posts)} posts -> {added_for_product} (bucket,post) pairs", flush=True)

    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"\nDone. {total_posts} posts read, {total_added} (bucket,post) pairs added. Total buckets now: {len(index)}.")


if __name__ == "__main__":
    main()
