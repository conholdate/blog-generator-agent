from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Optional

from .settings import CoverageSettings
from .tools.logging_utils import get_logger
from .tools.normalization import (
    nor_platform_display_name,
    nor_website_section_from_case,
    normalize_product_display_name,
    normalize_sentence_text,
)
from .tools.prerequisites import ensure_prerequisites
from .tools.io import write_json, write_text
from .tools.sheets_export import (
    build_payload,
    is_successful_sheet_response,
    post_payload,
    resolve_sheet_config,
    should_post_payload,
    write_payload,
)
from .tools.render.md_render import render_md_matrix
from .tools.render.gap_render import render_gaps_md
from .tools.coverage.blogs_to_blogs import compute_blogs_to_blogs
from .tools.coverage.docs_to_blogs import compute_docs_to_blogs
from .tools.coverage.docs_to_tutorials import compute_docs_to_tutorials

from .tools.metrics import MetricsSender, MetricsRun, new_run_id

log = get_logger("cg-cover.agent")


@dataclass(frozen=True)
class CoverageRunRequest:
    brand_key: str
    brand_name: str
    brand_site: str
    product_key: str
    product_name: str
    case: str
    baseline_platform: Optional[str]
    threshold_strict: float
    threshold_loose: float
    top_k: int
    platforms: Optional[list[str]] = None
    no_embeddings: bool = False


def _product_root(settings: CoverageSettings, brand_key: str, product_key: str) -> Path:
    return settings.outputs_root / brand_key / product_key


def _coverage_out_dir(
    settings: CoverageSettings,
    brand_key: str,
    product_key: str,
    case: str,
    baseline_platform: Optional[str],
) -> Path:
    baseline_dir = baseline_platform or "all"
    return settings.outputs_root / brand_key / product_key / "coverage" / case / baseline_dir


def _compute_gap_stats(result: Any) -> Dict[str, int]:
    """
    Computes stable, deterministic gap statistics from the in-memory result
    (no need to re-parse coverage.json).

    Definitions:
      - total_topics: number of baseline topics
      - fully_covered_topics: topics matched in *every* evaluated platform
      - partially_covered_topics: topics matched in at least one platform, but not all
      - fully_uncovered_topics: topics matched in none of the evaluated platforms
      - missing_pairs: total missing topic×platform matches
      - topics_with_any_gap: topics missing at least one platform match (partially + fully uncovered)
    """
    platforms = list(getattr(result, "platforms", []) or [])
    rows = list(getattr(result, "rows", []) or [])
    total_topics = len(rows)

    fully_covered_topics = 0
    partially_covered_topics = 0
    fully_uncovered_topics = 0
    missing_pairs = 0

    for r in rows:
        matched_flags: list[bool] = []
        for p in platforms:
            cell = (r.coverage or {}).get(p, {}) if hasattr(r, "coverage") else {}
            matched = bool(cell.get("matched"))
            matched_flags.append(matched)
            if not matched:
                missing_pairs += 1

        if matched_flags and all(matched_flags):
            fully_covered_topics += 1
        elif any(matched_flags):
            partially_covered_topics += 1
        else:
            fully_uncovered_topics += 1

    topics_with_any_gap = partially_covered_topics + fully_uncovered_topics

    return {
        "total_topics": total_topics,
        "fully_covered_topics": fully_covered_topics,
        "partially_covered_topics": partially_covered_topics,
        "fully_uncovered_topics": fully_uncovered_topics,
        "missing_pairs": missing_pairs,
        "topics_with_any_gap": topics_with_any_gap,
    }

def _to_sentence_case_with_upper_formats(topic: str) -> str:
    return normalize_sentence_text(str(topic or ""))


def _render_missing_topics_md(
    *,
    brand_name: str,
    product_name: str,
    platform_name: str,
    platforms: list[str],
    rows: list[Any],
) -> str:
    missing_rows: list[tuple[str, list[str]]] = []
    for r in rows:
        coverage = getattr(r, "coverage", {}) or {}
        missing_platforms = [p.upper() for p in platforms if not bool((coverage.get(p) or {}).get("matched"))]
        if missing_platforms:
            normalized_topic = _to_sentence_case_with_upper_formats(getattr(r, "topic", ""))
            missing_rows.append((normalized_topic, missing_platforms))

    out: list[str] = []
    out.append(f"# Missing Blog Topics for {product_name}")
    out.append("")
    out.append(f"- **Brand:** {brand_name}")
    out.append(f"- **Product:** {product_name}")
    out.append(f"- **Platform:** {platform_name}")
    out.append(f"- **Total Topics:** {len(missing_rows)}")
    out.append("")
    out.append("---")
    out.append("## All Missing Topics")
    out.append("")
    out.append("| # | Topic | Missing platforms (high-impact)|")
    out.append("| --- | --- | --- |")
    for i, (topic, missing_platforms) in enumerate(missing_rows, start=1):
        out.append(f"| {i} | {topic} | {', '.join(missing_platforms)} |")
    out.append("")
    out.append("---")
    out.append("")
    return "\n".join(out)


def _send_missing_topics_to_sheet(
    *,
    settings: CoverageSettings,
    req: CoverageRunRequest,
    coverage_json_path: Path,
) -> None:
    if os.getenv("CG_SKIP_SHEETS_AUTO_POST", "").strip().lower() in {"1", "true", "yes", "on"}:
        log.info("Skipping Google Sheets export: CG_SKIP_SHEETS_AUTO_POST is enabled.")
        return

    brand_cfg = resolve_sheet_config(settings, req.brand_key)
    webhook_url = str(brand_cfg.get("webhook_url") or "").strip()
    if not webhook_url:
        log.info("Skipping Google Sheets export: no TOPICS_SHEETS webhook configured for brand=%s", req.brand_key)
        return

    token = str(brand_cfg.get("token") or "").strip()
    sheet_name = str(brand_cfg.get("sheet_name") or "All Missing Topics").strip() or "All Missing Topics"
    output_json_cfg = brand_cfg.get("output_json") or (
        settings.outputs_root / "google_sheets" / f"{req.brand_key}_{req.product_key}_missing_topics.json"
    )
    output_json = Path(str(output_json_cfg)).expanduser()
    if not output_json.is_absolute():
        output_json = (settings.repo_root / output_json).resolve()

    payload = build_payload(
        coverage_json=coverage_json_path,
        sheet_name=sheet_name,
        replace=True,
    )
    write_payload(payload, output_json)
    log.info("Wrote Google Sheets payload: %s rows=%d", output_json, payload["meta"]["row_count"])

    should_post, reason = should_post_payload(payload)
    if not should_post:
        log.info(reason)
        return

    status, text = post_payload(payload, webhook_url, token)
    ok, reason = is_successful_sheet_response(status, text)
    if not ok:
        log.warning(reason)
        return
    log.info("Google Sheets POST succeeded for brand=%s product=%s: %s", req.brand_key, req.product_key, text[:500])


def run_coverage(settings: CoverageSettings, req: CoverageRunRequest) -> Dict[str, Any]:
    """
    Deterministic orchestrator (Step 1).
    Consumes existing indexes and writes artifacts.

    Emits TWO metric events:
      1) job_type="Content Coverage Map" (run_id=coverage_run_id)
      2) job_type="Content Gap Analysis" (run_id=gap_run_id)

    Both share extra["correlation_id"] for joining.
    """
    t0 = perf_counter()

    log.info(
        "Coverage run started: brand=%s site=%s product=%s case=%s baseline=%s platforms_limit=%s no_embeddings=%s "
        "threshold_strict=%.4f threshold_loose=%.4f top_k=%d",
        req.brand_key,
        req.brand_site,
        req.product_key,
        req.case,
        req.baseline_platform or "all",
        ",".join(req.platforms) if req.platforms else "None",
        req.no_embeddings,
        req.threshold_strict,
        req.threshold_loose,
        req.top_k,
    )
    log.info("Outputs root: %s", settings.outputs_root)

    outputs_product_root = _product_root(settings, req.brand_key, req.product_key)
    log.info("Resolved product outputs root: %s", outputs_product_root)

    # Metrics sender + correlation id shared across both metric events
    sender = MetricsSender(settings=settings)
    correlation_id = new_run_id("coverage")
    coverage_run_id = new_run_id("coverage_map")
    gap_run_id = new_run_id("gap_analysis")
    log.info(
        "Metrics initialized: correlation_id=%s coverage_run_id=%s gap_run_id=%s",
        correlation_id,
        coverage_run_id,
        gap_run_id,
    )

    # Stable metric fields
    product_name = normalize_product_display_name(
        req.product_name,
        brand_key=req.brand_key,
        product_key=req.product_key,
    )
    platform_name = nor_platform_display_name(req.baseline_platform)

    website = req.brand_site
    website_section = nor_website_section_from_case(req.case)
    # item_name = f"{req.case}"
    item_name = "Articles"

    # Resolve output directory early (deterministic)
    out_dir = _coverage_out_dir(settings, req.brand_key, req.product_key, req.case, req.baseline_platform)

    try:
        # ---------------------------------------
        # Metrics Event 1: Content Coverage Map
        # IMPORTANT: Wrap the REAL work here so duration is not 0.
        # ---------------------------------------
        with MetricsRun(
            sender=sender,
            run_id=coverage_run_id,
            job_type="Content Coverage Map",
            product=product_name,
            platform=platform_name,
            website=website,
            website_section=website_section,
            item_name=item_name,
            extra={
                "correlation_id": correlation_id,
                "brand_key": req.brand_key,
                "product_key": req.product_key,
                "product_name": product_name,
                "case": req.case,
                "baseline_platform": req.baseline_platform or "all",
                "threshold_strict": req.threshold_strict,
                "threshold_loose": req.threshold_loose,
                "top_k": req.top_k,
                "platforms_limit": req.platforms or [],
                "no_embeddings": req.no_embeddings,
                "outputs_product_root": str(outputs_product_root),
                "out_dir": str(out_dir),
            },
        ) as m1:
            # Step: prerequisites
            log.info(
                "Ensuring prerequisites: product_root=%s case=%s baseline=%s",
                outputs_product_root,
                req.case,
                req.baseline_platform or "all",
            )
            t_prereq = perf_counter()
            ensure_prerequisites(outputs_product_root, req.case, req.baseline_platform)
            log.info("Prerequisites OK (%.2f ms)", (perf_counter() - t_prereq) * 1000.0)

            # Step: case dispatch / compute
            log.info("Dispatching coverage case: %s", req.case)
            t_compute = perf_counter()

            if req.case == "blogs_to_blogs":
                log.info(
                    "Running compute_blogs_to_blogs: brand=%s product=%s baseline=%s platforms_limit=%s",
                    req.brand_key,
                    req.product_key,
                    req.baseline_platform or "all",
                    ",".join(req.platforms) if req.platforms else "None",
                )
                result = compute_blogs_to_blogs(
                    brand_key=req.brand_key,
                    product_key=req.product_key,
                    outputs_product_root=outputs_product_root,
                    baseline_platform=req.baseline_platform,
                    platforms_limit=req.platforms,
                )
                platforms = list(result.platforms)
                headers = ["Topic"] + platforms
            elif req.case == "docs_to_blogs":
                log.info(
                    "Running compute_docs_to_blogs: brand=%s product=%s baseline=%s blog_platforms_limit=%s",
                    req.brand_key,
                    req.product_key,
                    req.baseline_platform or "all",
                    ",".join(req.platforms) if req.platforms else "None",
                )
                result = compute_docs_to_blogs(
                    brand_key=req.brand_key,
                    product_key=req.product_key,
                    outputs_product_root=outputs_product_root,
                    baseline_platform=req.baseline_platform,
                    platforms_limit=req.platforms,
                    threshold_strict=req.threshold_strict,
                    threshold_loose=req.threshold_loose,
                    top_k=req.top_k,
                    no_embeddings=req.no_embeddings,
                )
                platforms = list(result.platforms)
                headers = ["Category", "Subcategory", "Topic"] + platforms
            elif req.case == "docs_to_tutorials":
                log.info(
                    "Running compute_docs_to_tutorials: brand=%s product=%s baseline=%s blog_platforms_limit=%s",
                    req.brand_key,
                    req.product_key,
                    req.baseline_platform or "all",
                    ",".join(req.platforms) if req.platforms else "None",
                )
                result = compute_docs_to_tutorials(
                    brand_key=req.brand_key,
                    product_key=req.product_key,
                    outputs_product_root=outputs_product_root,
                    baseline_platform=req.baseline_platform,
                    threshold_strict=req.threshold_strict,
                    threshold_loose=req.threshold_loose,
                    top_k=req.top_k,
                    no_embeddings=req.no_embeddings,
                )
                platforms = list(result.platforms)
                headers = ["Category", "Subcategory", "Topic"] + platforms
            else:
                raise NotImplementedError(
                    f"Case '{req.case}' is not implemented yet. "
                    "Next steps: docs_to_tutorials, api_coverage."
                )
                platforms = list(result.platforms)
                headers = ["Category", "Subcategory", "Topic"] + platforms

            compute_ms = (perf_counter() - t_compute) * 1000.0
            log.info("Case compute complete: case=%s (%.2f ms)", req.case, compute_ms)

            log.info("Resolved output directory: %s", out_dir)

            # Write coverage.json
            log.info("Serializing coverage result to JSON")
            t_json = perf_counter()
            coverage_json = result.to_json()
            coverage_json["brand_name"] = req.brand_name
            coverage_json["product_name"] = product_name
            coverage_json_path = out_dir / "coverage.json"
            write_json(coverage_json_path, coverage_json)
            log.info("Wrote coverage.json (%.2f ms)", (perf_counter() - t_json) * 1000.0)

            # Compute stats once and reuse for logs + metrics
            stats = _compute_gap_stats(result)
            result_meta = dict(getattr(result, "meta", {}) or {})

            log.info(
                "Coverage summary counts: total_topics=%d fully_covered_all_platforms=%d partially_or_uncovered=%d missing_pairs=%d",
                stats["total_topics"],
                stats["fully_covered_topics"],
                stats["topics_with_any_gap"],
                stats["missing_pairs"],
            )

            # Build MD coverage matrix
            log.info("Building coverage matrix markdown")
            t_md = perf_counter()

            summary_lines = [
                f"Total baseline topics: {stats['total_topics']}",
                f"Platforms evaluated: {', '.join(platforms)}",
                f"Fully covered across all platforms: {stats['fully_covered_topics']}",
                f"Topics with gaps (missing at least one platform): {stats['topics_with_any_gap']}",
                f"Missing topic×platform pairs: {stats['missing_pairs']}",
                (
                    "Matching mode: deterministic lexical ranking; "
                    f"strict={req.threshold_strict:.2f}, loose={req.threshold_loose:.2f}, top_k={req.top_k}, "
                    f"no_embeddings={req.no_embeddings}."
                ),
            ]


            md_rows: list[list[str]] = []
            for r in result.rows:
                row = [r.category, r.sub_category, r.topic]
                for p in platforms:
                    cell = r.coverage.get(p, {})
                    if cell.get("matched"):
                        score = float(cell.get("score", 0.0))
                        url = cell.get("url")
                        if url:
                            row.append(f"[✅ ({score:.2f})]({url})")
                        else:
                            row.append(f"✅ ({score:.2f})")
                    else:
                        row.append("—")
                md_rows.append(row)

            coverage_md = render_md_matrix(
                title=f"{product_name} — {req.case} ({req.baseline_platform or 'all'})",
                summary_lines=summary_lines,
                headers=headers,
                rows=md_rows,
            )
            write_text(out_dir / "coverage.md", coverage_md)
            log.info("Wrote coverage.md (%.2f ms)", (perf_counter() - t_md) * 1000.0)

            missing_topics_md = _render_missing_topics_md(
                brand_name=req.brand_name,
                product_name=product_name,
                platform_name=(req.baseline_platform or "all").upper(),
                platforms=platforms,
                rows=list(result.rows),
            )
            missing_topics_path = (
                out_dir / f"{req.brand_key}-{req.product_key}_{(req.baseline_platform or 'all')}_missing_topics.md"
            )
            write_text(missing_topics_path, missing_topics_md)
            log.info("Wrote missing topics markdown: %s", missing_topics_path)
            _send_missing_topics_to_sheet(
                settings=settings,
                req=req,
                coverage_json_path=coverage_json_path,
            )

            # Metrics counts for Coverage Map
            coverage_discovered = int(stats["total_topics"])
            coverage_succeeded = int(stats["total_topics"])
            coverage_failed = 0

            m1.set_counts(discovered=coverage_discovered, succeeded=coverage_succeeded, failed=coverage_failed)

            # Log before send (send typically happens on __exit__)
            log.info(
                "Metrics (Coverage Map) prepared: run_id=%s correlation_id=%s discovered=%d succeeded=%d failed=%d",
                coverage_run_id,
                correlation_id,
                coverage_discovered,
                coverage_succeeded,
                coverage_failed,
            )

        # ---------------------------------------
        # Metrics Event 2: Content Gap Analysis
        # IMPORTANT: Wrap the REAL gap work here.
        # ---------------------------------------
        gap_topics = int(stats["topics_with_any_gap"])
        gap_discovered = gap_topics
        gap_succeeded = gap_topics
        gap_failed = 0

        gap_extra = {
            "correlation_id": correlation_id,
            "brand_key": req.brand_key,
            "product_key": req.product_key,
            "product_name": product_name,
            "case": req.case,
            "baseline_platform": req.baseline_platform or "all",
            "out_dir": str(out_dir),
            # gap stats
            "total_topics": int(stats["total_topics"]),
            "fully_covered_topics": int(stats["fully_covered_topics"]),
            "partially_covered_topics": int(stats["partially_covered_topics"]),
            "fully_uncovered_topics": int(stats["fully_uncovered_topics"]),
            "topics_with_any_gap": int(stats["topics_with_any_gap"]),
                "missing_pairs": int(stats["missing_pairs"]),
                "coverage_meta": result_meta,
        }

        with MetricsRun(
            sender=sender,
            run_id=gap_run_id,
            job_type="Content Gap Analysis",
            product=product_name,
            platform=platform_name,
            website=website,
            website_section=website_section,
            item_name=item_name,
            extra=gap_extra,
        ) as m2:
            t_gaps = perf_counter()
            gaps_md = render_gaps_md(
                title=f"{product_name} — Gaps ({req.case}, baseline={req.baseline_platform or 'all'})",
                coverage_json=coverage_json,
            )
            write_text(out_dir / "gaps.md", gaps_md)
            gap_ms = (perf_counter() - t_gaps) * 1000.0
            log.info("Wrote gaps.md (%.2f ms)", gap_ms)

            m2.set_counts(discovered=gap_discovered, succeeded=gap_succeeded, failed=gap_failed)

            log.info(
                "Metrics (Gap Analysis) prepared: run_id=%s correlation_id=%s discovered=%d succeeded=%d failed=%d",
                gap_run_id,
                correlation_id,
                gap_discovered,
                gap_succeeded,
                gap_failed,
            )

        total_ms = (perf_counter() - t0) * 1000.0
        log.info(
            "Coverage run completed successfully: out_dir=%s topics=%d total_time=%.2f ms correlation_id=%s",
            out_dir,
            int(stats["total_topics"]),
            total_ms,
            correlation_id,
        )

        return {
            "case": req.case,
            "baseline_platform": req.baseline_platform,
            "product_name": product_name,
            "out_dir": str(out_dir),
            "topics": int(stats["total_topics"]),
            "platforms": list(result.platforms),
            "correlation_id": correlation_id,
            "metrics_run_ids": {
                "coverage_map": coverage_run_id,
                "gap_analysis": gap_run_id,
            },
            "coverage_stats": stats,
            "coverage_meta": result_meta,
        }

    except Exception:
        log.exception(
            "Coverage run failed: brand=%s product=%s case=%s baseline=%s correlation_id=%s coverage_run_id=%s gap_run_id=%s",
            req.brand_key,
            req.product_key,
            req.case,
            req.baseline_platform or "all",
            correlation_id,
            coverage_run_id,
            gap_run_id,
        )
        raise


def run_sync(settings: CoverageSettings, req: CoverageRunRequest) -> Dict[str, Any]:
    """
    Synchronous entrypoint used by CLI.
    No OpenAI initialization here (Step 1 is deterministic).
    """
    log.info("run_sync invoked")
    return run_coverage(settings, req)


def get_openai(settings: CoverageSettings):
    """
    For Step 2+: when/if you need OpenAI (e.g., re-embedding missing vectors),
    this uses settings.py as the only source of truth.
    """
    log.info("Initializing OpenAI client (Step 2+ helper)")
    from .tools.openai_client import get_openai_client

    return get_openai_client(settings)
