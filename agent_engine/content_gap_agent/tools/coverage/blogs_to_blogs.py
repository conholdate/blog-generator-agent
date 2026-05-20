from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional, Tuple, Set

from ..io import IndexRecord, read_jsonl
from ..logging_utils import get_logger
from ..normalization import (
    FORMAT_TOKEN_SET,
    canonical_file_format,
    canonical_topic_key,
    nor_platform_key,
    normalize_sentence_text,
    normalize_text,
)
from .base import CoverageResult, CoverageRow
from .filters import is_release_update_record

logger = get_logger("cg-cover.agent")

GENERAL_PLATFORM_KEY = "general"
MIN_BLOG_DATE = date(2020, 1, 1)
_BLOG_DATE_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$")

# -----------------------------
# KEY-BASED GROUPING + MATCHING
# -----------------------------

_KEY_SPLIT_RE = re.compile(r"[^a-z0-9]+", re.I)
_CONVERSION_PAIR_RE = re.compile(r"\b([a-z0-9]{1,20})\s*(?:to|into|in2|->|→)\s*([a-z0-9]{1,20})\b", re.IGNORECASE)


def normalize_gap_key(k: str) -> str:
    """
    Normalize indexer key for stable grouping/matching.
    Example: "OBJ-to-STL" -> "obj-to-stl"
    """
    k = (k or "").strip()
    if not k:
        return ""
    canonical = canonical_topic_key(k)
    if canonical:
        k = canonical
    parts = [p.lower() for p in _KEY_SPLIT_RE.split(k) if p]
    return "-".join(parts)


def record_gap_key(r: IndexRecord) -> str:
    """
    Prefer indexer-provided key; fallback to canonical topic key if missing.
    Indexing is now responsible for topic normalization quality.
    """
    if getattr(r, "key", None):
        return normalize_gap_key(str(r.key))
    return normalize_gap_key(r.topic or r.title)


def _conversion_gap_keys(text: str) -> List[str]:
    keys: List[str] = []
    normalized = re.sub(r"[-_/]+", " ", str(text or ""))
    for match in _CONVERSION_PAIR_RE.finditer(normalized):
        src = canonical_file_format(match.group(1))
        dst = canonical_file_format(match.group(2))
        if src in FORMAT_TOKEN_SET and dst in FORMAT_TOKEN_SET:
            key = normalize_gap_key(f"{src} to {dst}")
            if key and key not in keys:
                keys.append(key)
    return keys


def record_gap_keys(r: IndexRecord) -> List[str]:
    """
    Return every conversion key a record can satisfy.

    Baseline grouping still uses record_gap_key() so bidirectional articles do
    not create extra reverse-direction rows. Matching uses this list so a title
    like "KML to GPX and GPX to KML" can satisfy both existing rows.
    """
    keys: List[str] = []
    primary = record_gap_key(r)
    if primary:
        keys.append(primary)

    searchable_parts = [
        str(getattr(r, "key", "") or ""),
        str(getattr(r, "topic", "") or ""),
        str(getattr(r, "title", "") or ""),
    ]
    for part in searchable_parts:
        for key in _conversion_gap_keys(part):
            if key and key not in keys:
                keys.append(key)

    return keys


def _normalize_platform_key(s: Optional[str]) -> str:
    raw = (s or "").strip().lower()
    if raw == GENERAL_PLATFORM_KEY:
        return GENERAL_PLATFORM_KEY
    return nor_platform_key(s) if s else ""


def _record_blog_date(record: IndexRecord) -> Optional[date]:
    raw = str(getattr(record, "published_date", "") or "").strip()
    match = _BLOG_DATE_RE.match(raw)
    if not match:
        return None
    try:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError:
        return None


def _is_recent_blog_record(record: IndexRecord) -> bool:
    blog_date = _record_blog_date(record)
    return bool(blog_date and blog_date >= MIN_BLOG_DATE)


def infer_platforms(
    record: IndexRecord,
    *,
    allowed_platform_keys: Optional[Set[str]] = None,
) -> List[str]:
    """
    Determine platform keys for a record.
    Policy: platform comes ONLY from record.platform.
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
    allowed_platforms: Optional[List[str]] = None,
    include_general: bool = True,
) -> CoverageResult:
    """
    blogs_to_blogs (KEY-based):
      - Load blogs/all.jsonl
      - Group baseline topics by IndexRecord.key (normalized)
      - Match presence across platforms by KEY equality
      - Output CoverageRow.key and CoverageRow.topic = key
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
    total_records = len(records)
    records = [r for r in records if not is_release_update_record(r)]
    excluded_release = total_records - len(records)
    pre_date_filter_count = len(records)
    records = [r for r in records if _is_recent_blog_record(r)]
    excluded_old_or_undated = pre_date_filter_count - len(records)
    logger.info("Loaded blog index records: %d (%.2f ms)", len(records), (perf_counter() - t_load) * 1000.0)
    if excluded_release:
        logger.info("Excluded release/update records from coverage map: %d", excluded_release)
    if excluded_old_or_undated:
        logger.info(
            "Excluded blog records dated before %s or without parseable date: %d",
            MIN_BLOG_DATE.isoformat(),
            excluded_old_or_undated,
        )

    # Allowed platform set (normalized)
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

    # Normalize baseline platform
    baseline_platform_n = _normalize_platform_key(baseline_platform) if baseline_platform else ""
    baseline_label = baseline_platform_n or "all"

    # Determine platform universe
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

    # Apply platforms_limit
    if platforms_limit:
        limit_norm = [_normalize_platform_key(p) for p in platforms_limit if p and _normalize_platform_key(p)]
        limit_set = set(limit_norm)
        all_platforms = [p for p in all_platforms if p in limit_set]
        if baseline_platform_n and baseline_platform_n not in all_platforms:
            all_platforms = [baseline_platform_n] + all_platforms

    # Choose baseline records
    baseline_records = platform_to_records.get(baseline_platform_n, []) if baseline_platform_n else records

    # Group baseline by KEY only (one row per key)
    t_group = perf_counter()
    grouped: Dict[str, IndexRecord] = {}
    skipped_empty_keys = 0

    for r in baseline_records:
        k = record_gap_key(r)
        if not k:
            skipped_empty_keys += 1
            continue
        if k not in grouped:
            grouped[k] = r  # representative record for this key

    logger.info(
        "Baseline grouping complete (%.2f ms): baseline_records=%d grouped_keys=%d skipped_empty_keys=%d",
        (perf_counter() - t_group) * 1000.0,
        len(baseline_records),
        len(grouped),
        skipped_empty_keys,
    )

    # Build rows
    rows: List[CoverageRow] = []
    t_match = perf_counter()
    total_topics = len(grouped)

    matched_cells = 0
    total_cells = 0

    for key_norm, b in sorted(grouped.items(), key=lambda x: x[0]):
        cat = b.category or ""
        sub = b.sub_category or ""
        display_topic = normalize_sentence_text(canonical_topic_key(b.topic or b.title or key_norm) or key_norm.replace("-", " "))
        row_cov: Dict[str, Dict[str, object]] = {}

        # If baseline platform explicitly provided, mark it as covered by definition.
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
                if key_norm in record_gap_keys(c):
                    best = {
                        "matched": True,
                        "score": 1.0,
                        "record_id": c.id,
                        "title": c.title,
                        "topic": c.topic,
                        "url": c.url,
                    }
                    break

            row_cov[p] = best
            if best["matched"]:
                matched_cells += 1

        # Topic column = key
        rows.append(
            CoverageRow(
                category=cat,
                sub_category=sub,
                topic=display_topic,
                key=key_norm,
                baseline_record_id=b.id,
                coverage=row_cov,
            )
        )

    logger.info(
        "KEY matching complete: topics=%d total_cells=%d matched_cells=%d match_rate=%.2f%% (%.2f ms)",
        total_topics,
        total_cells,
        matched_cells,
        (matched_cells / total_cells * 100.0) if total_cells else 0.0,
        (perf_counter() - t_match) * 1000.0,
    )

    # Output platform order
    if baseline_platform_n:
        platforms_out = [baseline_platform_n] + [p for p in all_platforms if p != baseline_platform_n]
    else:
        platforms_out = list(all_platforms)

    logger.info(
        "compute_blogs_to_blogs finished: rows=%d total_time=%.2f ms",
        len(rows),
        (perf_counter() - t0) * 1000.0,
    )

    return CoverageResult(
        case="blogs_to_blogs",
        brand_key=brand_key,
        product_key=product_key,
        baseline_platform=baseline_label,
        platforms=platforms_out,
        rows=rows,
        meta={
            "matching_mode": "key_exact",
            "total_input_records": total_records,
            "records_after_filters": len(records),
            "excluded_release_update_records": excluded_release,
            "excluded_old_or_undated_records": excluded_old_or_undated,
            "baseline_records": len(baseline_records),
            "total_cells": total_cells,
            "matched_cells": matched_cells,
            "missing_cells": max(0, total_cells - matched_cells),
            "match_rate": (matched_cells / total_cells) if total_cells else 0.0,
            "skipped_empty_keys": skipped_empty_keys,
        },
    )
