from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional

from ..io import IndexRecord, read_jsonl
from ..logging_utils import get_logger
from ..normalize import normalize_text
from ..similarity import lexical_fast_match
from .base import CoverageResult, CoverageRow
from .blogs_to_blogs import infer_platforms

logger = get_logger("cg-cover.coverage.docs_to_blogs")


# Common platform tokens that may appear in "Title | Platform" style doc headers.
# normalize_text(".NET") typically becomes "net", so we include both forms here.
_PLATFORM_TOKENS: set[str] = {
    "net",
    ".net",
    "dotnet",
    "java",
    "python",
    "cpp",
    "c++",
    "cplusplus",
    "c#",
    "csharp",
    "node",
    "nodejs",
    "node.js",
    "javascript",
    "js",
    "android",
    "ios",
}


def _strip_platform_suffix(text: str, baseline_platform_n: str) -> str:
    """
    Strip a trailing ' | <platform>' suffix from titles/topics, e.g.

      'Developer Guide | .NET' -> 'Developer Guide'

    Only strips if the right-hand side looks like a platform token OR matches the
    provided baseline platform. This prevents accidental stripping for legitimate
    titles that contain pipes for other reasons.
    """
    s = (text or "").strip()
    if " | " not in s:
        return s

    left, right = s.rsplit(" | ", 1)
    rhs_n = normalize_text(right)

    # rhs_n could be "", so guard it.
    if rhs_n and (rhs_n == baseline_platform_n or rhs_n in _PLATFORM_TOKENS):
        return left.strip()

    return s


def _dedupe_baseline_docs(records: List[IndexRecord], baseline_platform_n: str) -> List[IndexRecord]:
    """
    De-dupe baseline docs by a stable topic key.
    Preference order:
      1) normalized (stripped) topic/title
      2) normalized id
    Keeps the first occurrence.
    """
    out: Dict[str, IndexRecord] = {}
    for r in records:
        raw_topic = (r.topic or r.title or "").strip()
        topic_text = _strip_platform_suffix(raw_topic, baseline_platform_n)
        topic_key = normalize_text(topic_text) or normalize_text(r.id) or ""
        if not topic_key:
            continue
        out.setdefault(topic_key, r)
    return list(out.values())


def compute_docs_to_blogs(
    *,
    brand_key: str,
    product_key: str,
    outputs_product_root: Path,
    baseline_platform: Optional[str],
    platforms_limit: Optional[List[str]] = None,
) -> CoverageResult:
    """
    docs_to_blogs (Step 1 lexical):
      - Load docs/{baseline_platform}.jsonl as baseline (required)
      - Load blog/all.jsonl as candidates grouped by inferred blog platforms
      - For each baseline docs topic, match into each blog platform subset using lexical_fast_match

    IMPORTANT:
      Some docs titles are shaped like 'Topic | .NET'. That pipe breaks Markdown tables.
      This function strips a trailing ' | <platform>' suffix (when it looks like a platform)
      before dedupe/matching/reporting.
    """
    t0 = perf_counter()

    baseline_platform_n = normalize_text(baseline_platform or "")
    if not baseline_platform_n:
        raise ValueError("docs_to_blogs requires baseline_platform (e.g. net, java).")

    indexes_root = outputs_product_root / "indexes"
    docs_path = indexes_root / "docs" / f"{baseline_platform_n}.jsonl"
    blogs_path = indexes_root / "blog" / "all.jsonl"

    logger.info(
        "compute_docs_to_blogs started: brand=%s product=%s baseline_platform=%s platforms_limit=%s docs_path=%s blogs_path=%s",
        brand_key,
        product_key,
        baseline_platform_n,
        ",".join(platforms_limit) if platforms_limit else "None",
        docs_path,
        blogs_path,
    )

    # -----------------------------
    # Load docs baseline
    # -----------------------------
    t_load_docs = perf_counter()
    docs_records = list(read_jsonl(docs_path))
    logger.info(
        "Loaded docs baseline records: %d (%.2f ms)",
        len(docs_records),
        (perf_counter() - t_load_docs) * 1000.0,
    )

    # Optional safety filter (in case platform file contains mixed platforms due to bug)
    baseline_docs: List[IndexRecord] = []
    for r in docs_records:
        rp = normalize_text(r.platform or "")
        if not rp or rp == baseline_platform_n:
            baseline_docs.append(r)

    baseline_items = _dedupe_baseline_docs(baseline_docs, baseline_platform_n)
    logger.info(
        "Baseline docs selected: baseline_platform=%s records=%d unique_topics=%d",
        baseline_platform_n,
        len(baseline_docs),
        len(baseline_items),
    )

    # -----------------------------
    # Load blog candidates
    # -----------------------------
    t_load_blogs = perf_counter()
    blog_records = list(read_jsonl(blogs_path))
    logger.info(
        "Loaded blog index records: %d (%.2f ms)",
        len(blog_records),
        (perf_counter() - t_load_blogs) * 1000.0,
    )

    # -----------------------------
    # Build blog platform -> records mapping
    # -----------------------------
    t_map = perf_counter()
    platform_to_blog_records: Dict[str, List[IndexRecord]] = defaultdict(list)
    all_platforms_set: set[str] = set()
    no_platform_records = 0

    for r in blog_records:
        plats = infer_platforms(r)
        if not plats:
            no_platform_records += 1
            plats = ["general"]

        for p in plats:
            p2 = normalize_text(p) or "general"
            platform_to_blog_records[p2].append(r)
            all_platforms_set.add(p2)

    platforms = sorted(all_platforms_set)

    if platforms_limit:
        limit_set = {normalize_text(x) for x in platforms_limit if normalize_text(x)}
        platforms = [p for p in platforms if p in limit_set]

    logger.info(
        "Blog platform mapping built (%.2f ms): unique_platforms=%d no_platform_records=%d",
        (perf_counter() - t_map) * 1000.0,
        len(platforms),
        no_platform_records,
    )

    # -----------------------------
    # Lexical match baseline docs topics to blog topics per platform
    # -----------------------------
    t_match = perf_counter()
    rows: List[CoverageRow] = []

    total_topics = len(baseline_items)
    total_cells = total_topics * max(len(platforms), 1)
    matched_cells = 0
    progress_every = 200 if total_topics > 2000 else 100

    logger.info(
        "Starting lexical matching: baseline_topics=%d blog_platforms=%d total_cells=%d",
        total_topics,
        len(platforms),
        total_cells,
    )

    for i, d in enumerate(baseline_items, start=1):
        raw_topic = (d.topic or d.title or "").strip()
        topic_text = _strip_platform_suffix(raw_topic, baseline_platform_n)
        topic_key = normalize_text(topic_text) or normalize_text(d.id) or ""

        cat = str(d.category or "General")
        sub = str(d.sub_category or "General")

        row_cov: Dict[str, Dict[str, object]] = {}

        # Use stripped baseline text for matching
        base_text = topic_text

        for p in platforms:
            best: Dict[str, object] = {
                "matched": False,
                "score": 0.0,
                "record_id": None,
                "title": None,
                "topic": None,
                "url": None,
            }

            candidates = platform_to_blog_records.get(p, [])
            if not candidates:
                row_cov[p] = best
                continue

            for c in candidates:
                cand_text = (c.topic or c.title or "").strip()
                m = lexical_fast_match(base_text, cand_text)
                if m.matched and m.score >= float(best["score"]):
                    best = {
                        "matched": True,
                        "score": float(m.score),
                        "record_id": c.id,
                        "title": c.title,
                        "topic": c.topic,
                        "url": c.url,
                    }

            if bool(best["matched"]):
                matched_cells += 1

            row_cov[p] = best

        rows.append(
            CoverageRow(
                category=cat,
                sub_category=sub,
                topic=topic_text,  # IMPORTANT: no pipe → markdown-safe topic cell
                topic_key=topic_key,
                baseline_record_id=d.id,
                coverage=row_cov,
            )
        )

        if i == 1 or i % progress_every == 0 or i == total_topics:
            elapsed_ms = (perf_counter() - t_match) * 1000.0
            logger.info("Matching progress: %d/%d topics processed (%.2f ms elapsed)", i, total_topics, elapsed_ms)

    match_ms = (perf_counter() - t_match) * 1000.0
    logger.info(
        "Lexical matching complete: topics=%d total_cells=%d matched_cells=%d match_rate=%.2f%% (%.2f ms)",
        total_topics,
        total_cells,
        matched_cells,
        (matched_cells / total_cells * 100.0) if total_cells else 0.0,
        match_ms,
    )

    total_ms = (perf_counter() - t0) * 1000.0
    logger.info(
        "compute_docs_to_blogs finished: rows=%d blog_platforms=%d total_time=%.2f ms",
        len(rows),
        len(platforms),
        total_ms,
    )

    return CoverageResult(
        case="docs_to_blogs",
        brand_key=brand_key,
        product_key=product_key,
        baseline_platform=baseline_platform_n,
        platforms=list(platforms),
        rows=rows,
    )
