from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional

from ..io import IndexRecord, read_jsonl
from ..logging_utils import get_logger
from ..normalize import normalize_text
from ..similarity import lexical_fast_match
from .base import CoverageResult, CoverageRow

logger = get_logger("cg-cover.agent")


def _dedupe_baseline_docs(records: List[IndexRecord]) -> List[IndexRecord]:
    """
    De-dupe baseline docs by a stable topic key.
    Preference order:
      1) normalized topic/title
      2) normalized id
    Keeps the first occurrence.
    """
    out: Dict[str, IndexRecord] = {}
    for r in records:
        topic_text = (r.topic or r.title or "").strip()
        topic_key = normalize_text(topic_text) or normalize_text(r.id) or ""
        if not topic_key:
            continue
        out.setdefault(topic_key, r)
    return list(out.values())


def compute_docs_to_tutorials(
    *,
    brand_key: str,
    product_key: str,
    outputs_product_root: Path,
    baseline_platform: Optional[str],
) -> CoverageResult:
    """
    docs_to_tutorials (Step 1 lexical):

      - Baseline: docs/{baseline_platform}.jsonl
      - Candidates: tutorials/{baseline_platform}.jsonl
      - For each baseline docs topic, find best tutorial match (lexical_fast_match)
      - Output matrix has a single column: "tutorials"
    """
    t0 = perf_counter()

    baseline_platform_n = normalize_text(baseline_platform or "")
    if not baseline_platform_n:
        raise ValueError("docs_to_tutorials requires baseline_platform (e.g., net, java).")

    indexes_root = outputs_product_root / "indexes"
    docs_path = indexes_root / "docs" / f"{baseline_platform_n}.jsonl"
    tuts_path = indexes_root / "tutorials" / f"{baseline_platform_n}.jsonl"

    logger.info(
        "compute_docs_to_tutorials started: brand=%s product=%s baseline_platform=%s docs_path=%s tutorials_path=%s",
        brand_key,
        product_key,
        baseline_platform_n,
        docs_path,
        tuts_path,
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

    # Safety filter: keep only platform-matching records (in case of indexing issues)
    baseline_docs: List[IndexRecord] = []
    for r in docs_records:
        rp = normalize_text(r.platform or "")
        if not rp or rp == baseline_platform_n:
            baseline_docs.append(r)

    baseline_items = _dedupe_baseline_docs(baseline_docs)
    logger.info(
        "Baseline docs selected: baseline_platform=%s records=%d unique_topics=%d",
        baseline_platform_n,
        len(baseline_docs),
        len(baseline_items),
    )

    # -----------------------------
    # Load tutorials candidates
    # -----------------------------
    t_load_tuts = perf_counter()
    tutorial_records = list(read_jsonl(tuts_path))
    logger.info(
        "Loaded tutorial index records: %d (%.2f ms)",
        len(tutorial_records),
        (perf_counter() - t_load_tuts) * 1000.0,
    )

    # -----------------------------
    # Match docs topics -> tutorials topics
    # -----------------------------
    t_match = perf_counter()
    rows: List[CoverageRow] = []

    platforms_out = ["tutorials"]  # single target column for this case
    total_topics = len(baseline_items)
    matched_cells = 0
    progress_every = 200 if total_topics > 2000 else 100

    logger.info(
        "Starting lexical matching: baseline_topics=%d candidates=%d",
        total_topics,
        len(tutorial_records),
    )

    for i, d in enumerate(baseline_items, start=1):
        topic_text = (d.topic or d.title or "").strip()
        topic_key = normalize_text(topic_text) or normalize_text(d.id) or ""

        cat = str(d.category or "General")
        sub = str(d.sub_category or "General")

        best: Dict[str, object] = {
            "matched": False,
            "score": 0.0,
            "record_id": None,
            "title": None,
            "topic": None,
            "url": None,
        }

        base_text = (d.topic or d.title or "").strip()

        # Find best tutorial match for this docs topic
        for t in tutorial_records:
            cand_text = (t.topic or t.title or "").strip()
            m = lexical_fast_match(base_text, cand_text)
            if m.matched and m.score >= float(best["score"]):
                best = {
                    "matched": True,
                    "score": float(m.score),
                    "record_id": t.id,
                    "title": t.title,
                    "topic": t.topic,
                    "url": t.url,
                }

        if bool(best["matched"]):
            matched_cells += 1

        row_cov = {"tutorials": best}

        rows.append(
            CoverageRow(
                category=cat,
                sub_category=sub,
                topic=topic_text,
                topic_key=topic_key,
                baseline_record_id=d.id,
                coverage=row_cov,
            )
        )

        if i == 1 or i % progress_every == 0 or i == total_topics:
            elapsed_ms = (perf_counter() - t_match) * 1000.0
            logger.info(
                "Matching progress: %d/%d topics processed (%.2f ms elapsed)",
                i,
                total_topics,
                elapsed_ms,
            )

    match_ms = (perf_counter() - t_match) * 1000.0
    match_rate = (matched_cells / total_topics * 100.0) if total_topics else 0.0
    logger.info(
        "Lexical matching complete: topics=%d matched=%d match_rate=%.2f%% (%.2f ms)",
        total_topics,
        matched_cells,
        match_rate,
        match_ms,
    )

    total_ms = (perf_counter() - t0) * 1000.0
    logger.info(
        "compute_docs_to_tutorials finished: rows=%d total_time=%.2f ms",
        len(rows),
        total_ms,
    )

    return CoverageResult(
        case="docs_to_tutorials",
        brand_key=brand_key,
        product_key=product_key,
        baseline_platform=baseline_platform_n,
        platforms=platforms_out,
        rows=rows,
    )
