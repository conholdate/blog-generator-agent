from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional, Tuple, Set

from ..io import IndexRecord, read_jsonl
from ..logging_utils import get_logger
from ..normalize import canonical_topic_key, nor_platform_key
from ..similarity import lexical_fast_match
from .base import CoverageResult, CoverageRow

logger = get_logger("cg-cover.agent")

GENERAL_PLATFORM_KEY = "general"


def _normalize_platform_key(s: Optional[str]) -> str:
    """Normalize a platform key consistently; empty -> ''."""
    return nor_platform_key(s) if s else ""


def infer_platforms(
    record: IndexRecord,
    *,
    allowed_platform_keys: Optional[Set[str]] = None,
) -> List[str]:
    """
    Determine platform keys for a blog record.

    POLICY:
    - Exactly one platform per article in indexing.
    - Coverage must treat record.platform as the ONLY source of truth.
    - Keywords must never be treated as platform keys.

    If allowed_platform_keys is provided, output is validated against it.
    """
    p0 = _normalize_platform_key(record.platform)
    if not p0:
        return []

    if allowed_platform_keys is not None and p0 not in allowed_platform_keys:
        return []

    return [p0]


def compute_blogs_to_blogs(
    *,
    brand_key: str,
    product_key: str,
    outputs_product_root: Path,
    baseline_platform: Optional[str] = None,
    platforms_limit: Optional[List[str]] = None,
    # preferred source-of-truth platform universe (from product YAML)
    allowed_platforms: Optional[List[str]] = None,
    include_general: bool = True,
) -> CoverageResult:
    """
    blogs_to_blogs:
      - Load blogs/all.jsonl
      - Map records to platforms (record.platform only)
      - Choose baseline topics:
          * if baseline_platform provided: baseline topics from that platform
          * else: baseline topics from all blogs (canonical topic universe)
      - For each baseline topic, check matches in each platform subset (lexical match on canonical topic keys)
    """
    t0 = perf_counter()
    logger.info(
        "compute_blogs_to_blogs started: brand=%s product=%s baseline_platform=%s platforms_limit=%s allowed_platforms=%s outputs_product_root=%s",
        brand_key,
        product_key,
        baseline_platform or "all",
        ",".join(platforms_limit) if platforms_limit else "None",
        ",".join(allowed_platforms) if allowed_platforms else "None",
        outputs_product_root,
    )

    blogs_path = outputs_product_root / "indexes" / "blog" / "all.jsonl"
    logger.info("Loading blog index: %s", blogs_path)

    t_load = perf_counter()
    records = list(read_jsonl(blogs_path))
    logger.info("Loaded blog index records: %d (%.2f ms)", len(records), (perf_counter() - t_load) * 1000.0)

    # Allowed platform set (normalized + python collapsing)
    allowed_set: Optional[Set[str]] = None
    if allowed_platforms:
        allowed_set = {p for p in (_normalize_platform_key(x) for x in allowed_platforms) if p}
        if include_general:
            allowed_set.add(GENERAL_PLATFORM_KEY)

    # Build platform -> records mapping
    platform_to_records: Dict[str, List[IndexRecord]] = defaultdict(list)
    no_platform_records = 0
    general_fallback_assignments = 0

    t_map = perf_counter()
    for r in records:
        plats = infer_platforms(r, allowed_platform_keys=allowed_set)
        if not plats:
            no_platform_records += 1
            plats = [GENERAL_PLATFORM_KEY] if include_general else []

        for p in plats:
            p2 = _normalize_platform_key(p) or (GENERAL_PLATFORM_KEY if include_general else "")
            if not p2:
                continue
            if p2 == GENERAL_PLATFORM_KEY:
                general_fallback_assignments += 1
            platform_to_records[p2].append(r)

    inferred_platforms = sorted(platform_to_records.keys())

    logger.info(
        "Platform mapping built (%.2f ms): inferred_platforms=%d records_with_no_platform=%d general_assignments=%d",
        (perf_counter() - t_map) * 1000.0,
        len(inferred_platforms),
        no_platform_records,
        general_fallback_assignments,
    )

    # Normalize baseline
    baseline_platform_n = _normalize_platform_key(baseline_platform) if baseline_platform else ""
    baseline_label = baseline_platform_n or "all"
    logger.info(
        "Baseline resolved: input=%s normalized=%s label=%s",
        baseline_platform or "None",
        baseline_platform_n or "None",
        baseline_label,
    )

    # Determine platform universe:
    # - If allowed_platforms provided => use it as the source of truth (even if some have 0 records)
    # - Else fall back to inferred platforms (legacy behavior)
    if allowed_set is not None:
        ordered_allowed = [_normalize_platform_key(p) for p in (allowed_platforms or [])]
        ordered_allowed = [p for p in ordered_allowed if p]
        if include_general and GENERAL_PLATFORM_KEY not in ordered_allowed:
            ordered_allowed.append(GENERAL_PLATFORM_KEY)
        all_platforms = ordered_allowed
    else:
        all_platforms = inferred_platforms
        if include_general and GENERAL_PLATFORM_KEY not in all_platforms:
            all_platforms.append(GENERAL_PLATFORM_KEY)

    logger.info("Initial platform universe size: %d", len(all_platforms))

    # Apply platforms_limit (validated against universe)
    if platforms_limit:
        t_limit = perf_counter()
        limit_norm = [_normalize_platform_key(p) for p in platforms_limit if p and _normalize_platform_key(p)]
        limit_set = set(limit_norm)
        before = len(all_platforms)
        all_platforms = [p for p in all_platforms if p in limit_set]
        after = len(all_platforms)

        # If baseline is explicit and was not included in limit, keep it for matrix integrity.
        baseline_added = False
        if baseline_platform_n and baseline_platform_n not in all_platforms:
            all_platforms = [baseline_platform_n] + all_platforms
            baseline_added = True

        logger.info(
            "Applied platforms_limit (%.2f ms): before=%d after=%d baseline_added=%s limit_norm=%s",
            (perf_counter() - t_limit) * 1000.0,
            before,
            after,
            str(baseline_added),
            ",".join(limit_norm) if limit_norm else "None",
        )

    # Choose baseline records
    if baseline_platform_n:
        baseline_records = platform_to_records.get(baseline_platform_n, [])
        logger.info("Baseline records selected from platform=%s: %d records", baseline_platform_n, len(baseline_records))
        if not baseline_records:
            logger.info(
                "Baseline platform has zero records: platform=%s. Coverage will still run but matrix will be sparse.",
                baseline_platform_n,
            )
    else:
        baseline_records = records
        logger.info("Baseline records selected from full corpus: %d records", len(baseline_records))

    # Group baseline by (category, sub_category, canonical_topic_key) to reduce duplicates
    t_group = perf_counter()
    grouped: Dict[Tuple[str, str, str], IndexRecord] = {}
    skipped_empty_topics = 0

    for r in baseline_records:
        # Canonical key: removes "using C# / in Java / for .NET" etc.
        topic_key = canonical_topic_key(r.topic or r.title)
        if not topic_key:
            skipped_empty_topics += 1
            continue
        key = (r.category or "", r.sub_category or "", topic_key)
        if key not in grouped:
            grouped[key] = r

    logger.info(
        "Baseline grouping complete (%.2f ms): baseline_records=%d grouped_topics=%d skipped_empty_topics=%d",
        (perf_counter() - t_group) * 1000.0,
        len(baseline_records),
        len(grouped),
        skipped_empty_topics,
    )

    # High-level platform candidate stats (useful for debugging skew)
    logger.info("Candidate pool sizes per platform (top 10 by size):")
    plat_sizes = sorted(((p, len(rs)) for p, rs in platform_to_records.items()), key=lambda x: x[1], reverse=True)
    for p, n in plat_sizes[:10]:
        logger.info("  platform=%s candidates=%d", p, n)

    rows: List[CoverageRow] = []

    # Progress + matching stats
    t_match = perf_counter()
    total_topics = len(grouped)
    progress_every = 20
    matched_cells = 0
    total_cells = 0

    logger.info(
        "Starting lexical matching: topics=%d platforms_to_evaluate=%d baseline_platform_explicit=%s",
        total_topics,
        len(all_platforms),
        str(bool(baseline_platform_n)),
    )

    for i, ((cat, sub, topic_key), b) in enumerate(
        sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])),
        start=1,
    ):
        row_cov: Dict[str, Dict[str, object]] = {}

        # Canonical baseline text for comparisons
        base_text = canonical_topic_key(b.topic or b.title)

        # If baseline platform was explicitly provided, mark that platform as covered by definition.
        if baseline_platform_n:
            row_cov[baseline_platform_n] = {
                "matched": True,
                "score": 1.0,
                "record_id": b.id,
                "title": b.title,
                "topic": b.topic,
                "url": b.url,
            }
            matched_cells += 1
            total_cells += 1

        # For each platform, find best match
        for p in all_platforms:
            if baseline_platform_n and p == baseline_platform_n:
                continue

            total_cells += 1
            best = {"matched": False, "score": 0.0, "record_id": None, "title": None, "topic": None, "url": None}

            candidates = platform_to_records.get(p, [])
            if not candidates:
                row_cov[p] = best
                continue

            for c in candidates:
                cand_text = canonical_topic_key(c.topic or c.title)

                # Lexical match is now applied to canonicalized text
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
                # Display the original title (less confusing than LLM topic alone)
                topic=b.title or b.topic,
                topic_key=topic_key,
                baseline_record_id=b.id,
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

    # Output platforms ordering:
    if baseline_platform_n:
        platforms_out = [baseline_platform_n] + [p for p in all_platforms if p != baseline_platform_n]
    else:
        platforms_out = list(all_platforms)

    logger.info(
        "Platforms output ordering: %d platforms (baseline_first=%s)",
        len(platforms_out),
        str(bool(baseline_platform_n)),
    )
    logger.info("compute_blogs_to_blogs finished: rows=%d total_time=%.2f ms", len(rows), (perf_counter() - t0) * 1000.0)

    return CoverageResult(
        case="blogs_to_blogs",
        brand_key=brand_key,
        product_key=product_key,
        baseline_platform=baseline_label,
        platforms=platforms_out,
        rows=rows,
    )
