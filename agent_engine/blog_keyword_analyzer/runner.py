# src/agents/kra/runner.py
from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Optional, List, Mapping, Any, Dict, Tuple

from .schemas import RunRequest, RunResult, Cluster, KeywordRecord
from .agents import build_keyword_workflow_agent
from .config import settings
from .tools.metrics import RunMetrics
from agent_engine.blog_keyword_analyzer.tools.normalization import (
    KeywordRefiner,
    normalize_missing_platform,
    platform_header_display,
)

logger = logging.getLogger(__name__)
refiner = KeywordRefiner()


def _dedupe_keywords(values: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for value in values:
        key = value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _keyword_groups_to_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            if isinstance(dumped, Mapping):
                return dict(dumped)
        except Exception:
            return {}
    if hasattr(value, "dict"):
        try:
            dumped = value.dict()
            if isinstance(dumped, Mapping):
                return dict(dumped)
        except Exception:
            return {}
    return {}


def _keyword_intent_key(text: str) -> str:
    s = " ".join((text or "").strip().split()).lower()
    s = re.sub(r"(?i)^(tutorial|guide|example|examples|code sample|sample)\s*:\s*", "", s)
    s = re.sub(r"(?i)\b(how to|tutorial|guide|example|examples|code sample|sample)\b", " ", s)
    s = re.sub(r"[^a-z0-9.+#]+", " ", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s




@dataclass(frozen=True)
class MissingTopicSelection:
    brand: str
    product: str
    topic: str
    row_index: int
    platforms: List[str]


def _parse_missing_topics_selection(path: Path, row_index: int) -> MissingTopicSelection:
    text = path.read_text(encoding="utf-8")

    brand_match = re.search(r"^- \*\*Brand:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    product_match = re.search(r"^- \*\*Product:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    if not brand_match or not product_match:
        raise ValueError(f"Brand/Product metadata not found in missing topics file: {path}")

    table_row_re = re.compile(
        r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$",
        re.MULTILINE,
    )
    selected_topic: Optional[str] = None
    selected_platforms: List[str] = []

    for match in table_row_re.finditer(text):
        current_row = int(match.group(1))
        if current_row != row_index:
            continue

        selected_topic = match.group(2).strip()
        platform_tokens = [p.strip() for p in match.group(3).split(",")]
        selected_platforms = []
        for token in platform_tokens:
            normalized = normalize_missing_platform(token)
            if normalized and normalized not in selected_platforms:
                selected_platforms.append(normalized)
        break

    if not selected_topic:
        raise ValueError(f"Row #{row_index} was not found in missing topics table: {path}")

    return MissingTopicSelection(
        brand=brand_match.group(1).strip(),
        product=product_match.group(1).strip(),
        topic=selected_topic,
        row_index=row_index,
        platforms=selected_platforms,
    )

def _project_root(start: Optional[Path] = None) -> Path:
    """
    Walk up from 'start' (or CWD) to find a directory containing pyproject.toml or .git.

    This keeps paths robust across local dev, containers, or CI.
    """
    p = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return Path.cwd().resolve()

def _resolve_brand_output_dir(brand_folder: str) -> Path:
    root = _project_root()
    out_dir = (root / "content" / brand_folder / "output").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _resolve_output_dir() -> Path:
    """
    Resolve KRA_OUTPUT_DIR from settings, making it absolute relative to project root.
    Ensures the directory exists.
    """
    root = _project_root()
    out_dir = Path(settings.KRA_OUTPUT_DIR)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _resolve_input_file(path_str: str | None) -> Optional[Path]:
    """
    Resolve the input file if explicitly provided via --file.

    Behavior:
      - If path_str is falsy (None / ""), return None (caller may use defaults).
      - If path_str is given but file does NOT exist -> raise FileNotFoundError.
      - Relative paths are resolved against project root for consistency.
    """
    if not path_str:
        return None

    root = _project_root()
    p = Path(path_str)

    if not p.is_absolute():
        p = (root / p).resolve()

    if not p.exists():
        raise FileNotFoundError(f"Input --file not found at: {p}")

    return p

def _get_metrics_db_path(default_dir: Path) -> Path:
    """
    Return the path to the metrics DB JSON.

    If KRA_METRICS_DB_PATH is set (via settings), use that.
    Otherwise, default to <default_dir>/kra_metrics_db.json.
    """
    if settings.KRA_METRICS_DB_PATH:
        return Path(settings.KRA_METRICS_DB_PATH).resolve()
    return default_dir / "kra_metrics_db.json"

def _normalize_topic_key(text: str) -> str:
    """
    Normalize a text (title/url/slug) into a comparable key:
      - lowercase
      - only alphanumeric + single hyphens
    """
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def _brand_slug(brand: str) -> str:
    return _normalize_topic_key(brand or "unknown")

def _print_run_title(
    *,
    brand: str,
    product: str,
    include_product_in_title: bool = True,
) -> None:
    """
    Print a simple CLI title banner. Optionally includes product name.

    Args:
        brand: Brand string shown in title context.
        product: Product string shown in title context.
        include_product_in_title: If True, append product name in title.
    """
    print("=" * 80)
    title = "Blog Keyword Analyzer"
    if include_product_in_title:
        # Include product if available; keep formatting stable
        p = (product or "").strip()
        if p:
            title = f"{title} - {p}"
    # Brand is always useful context; keep it as a subtitle line
    print(title)
    b = (brand or "").strip()
    if b:
        print(f"Brand: {b}")
    print("=" * 80)
    print()


def _summarize_cluster_scores(clusters: List[Cluster]) -> dict:
    """
    Compute simple summary statistics for cluster scores.
    """
    scores = [c.metrics.score for c in clusters if c.metrics is not None]
    if not scores:
        return {"count": 0, "min": None, "max": None, "avg": None}
    return {
        "count": len(scores),
        "min": min(scores),
        "max": max(scores),
        "avg": mean(scores),
    }

def write_topics_markdown(
    result: RunResult,
    output_dir: Path,
    platform: Optional[str] = None,
    file_name: Optional[str] = None,
) -> Path:
    """
    Write a Markdown file with the generated topics for this run.
    Example: <runid>_<product>_<platform>_topics.md
    """
    from collections.abc import Mapping  # local import to avoid touching global imports

    # Respect the caller-provided output_dir (workflow sets KRA_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_product = _brand_slug(result.product)
    safe_platform = _brand_slug(platform or "all")

    run_suffix = result.run_id[:8] if result.run_id else "run"
    md_path = output_dir / (file_name or f"{run_suffix}_{safe_product}_{safe_platform}_topics.md")
    print(md_path)

    lines: List[str] = []
    heading = f"# Blog Topics for {result.product}"
    lines.append(heading)
    lines.append("")
    lines.append(f"- **Brand:** {result.brand}")
    lines.append(f"- **Product:** {result.product}")
    lines.append(f"- **Platform:** {platform_header_display(platform)}")
    lines.append(f"- **Run ID:** {result.run_id}")
    lines.append(f"- **Topics:** {len(result.topics)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    def _to_mapping(obj: Any) -> Dict[str, Any]:
        """Support dict topics + Pydantic v1/v2 models."""
        if isinstance(obj, Mapping):
            return dict(obj)
        if hasattr(obj, "model_dump"):  # Pydantic v2
            try:
                return obj.model_dump()
            except Exception:
                return {}
        if hasattr(obj, "dict"):  # Pydantic v1
            try:
                return obj.dict()
            except Exception:
                return {}
        return {}

    for idx, t in enumerate(result.topics, start=1):
        data = _to_mapping(t)

        def pick(key: str, default: Any = None) -> Any:
            v = getattr(t, key, None)
            if v is not None:
                return v
            return data.get(key, default)

        title = pick("title", "") or ""
        cluster_id = pick("cluster_id")
        angle = pick("angle")

        # Refine Keywords
        primary_kw_r = pick("primary_keyword")
        primary_kw = refiner.refine(primary_kw_r)

        supporting_kws_r = pick("supporting_keywords", []) or []

        def _flatten(x: Any) -> List[Any]:
            if x is None:
                return []
            if isinstance(x, (list, tuple)):
                out: List[Any] = []
                for item in x:
                    out.extend(_flatten(item))
                return out
            return [x]

        # Normalize/flatten to a list of items
        if isinstance(supporting_kws_r, str) or hasattr(supporting_kws_r, "keyword"):
            supporting_kws_r = [supporting_kws_r]
        else:
            supporting_kws_r = _flatten(supporting_kws_r)

        # Refine each keyword
        supporting_kws = [refiner.refine(k) for k in supporting_kws_r]
        supporting_kws = [k for k in supporting_kws if k]
        primary_intent_key = _keyword_intent_key(primary_kw)
        supporting_kws = [k for k in supporting_kws if _keyword_intent_key(k) != primary_intent_key]

        # Optional: de-dupe (case-insensitive) while keeping order
        seen = set()
        supporting_kws = [k for k in supporting_kws if not (k.lower() in seen or seen.add(k.lower()))]

        outline = pick("outline", []) or []
        persona = pick("target_persona")
        keyword_groups = _keyword_groups_to_mapping(pick("keyword_groups", {}) or {})
        editorial_notes = pick("editorial_notes", []) or []

        topic_title = refiner.to_title_case(title)
        lines.append(f"## {idx}. {topic_title}")
        if cluster_id is not None:
            lines.append(f"- **Cluster ID:** `{cluster_id}`")
        if persona:
            lines.append(f"- **Target persona:** {persona}")
        if angle:
            lines.append(f"- **Blog post angle:** {angle}")
        if primary_kw:
            lines.append(f"- **Primary keyword:** `{primary_kw}`")

        if keyword_groups:
            core = [refiner.refine(k) for k in (keyword_groups.get("core_seo_keywords") or []) if k]
            long_tail = [refiner.refine(k) for k in (keyword_groups.get("long_tail_keywords") or []) if k]
            context = [refiner.refine(k) for k in (keyword_groups.get("context_keywords") or []) if k]
            core = [k for k in core if _keyword_intent_key(k) != primary_intent_key]
            long_tail = [k for k in long_tail if _keyword_intent_key(k) != primary_intent_key]
            context = [k for k in context if _keyword_intent_key(k) != primary_intent_key]
            core = _dedupe_keywords(core)
            long_tail = _dedupe_keywords(long_tail)
            context = _dedupe_keywords(context)
        else:
            core, long_tail, context = [], [], []

        secondary_keywords = _dedupe_keywords(core or supporting_kws)
        if secondary_keywords:
            lines.append(
                f"- **Secondary keywords (Core SEO Keywords):** {', '.join(f'`{kw}`' for kw in secondary_keywords)}"
            )

        if long_tail:
            lines.append(f"- **Long Tails keywords:** {', '.join(f'`{k}`' for k in long_tail)}")
        if context:
            lines.append(f"- **Semantic SEO keywords:** {', '.join(f'`{k}`' for k in context)}")

        if outline:
            lines.append("")
            lines.append("**Outline for the article:**")
            for bullet in outline:
                line_item = refiner.to_title_case(bullet)
                lines.append(f"- {line_item}")

        if editorial_notes:
            lines.append("")
            lines.append("**Other important and relevant things:**")
            for note in editorial_notes:
                lines.append(f"- {refiner.to_sentence_case(note)}")

        lines.append("")
        lines.append("---")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved topics markdown to %s", md_path)
    return md_path


def write_missing_topics_markdown(
    *,
    selection: MissingTopicSelection,
    runs: List[Tuple[str, RunResult]],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_product = _brand_slug(selection.product)
    safe_topic = _brand_slug(selection.topic)[:60] or f"row-{selection.row_index}"
    md_path = output_dir / f"missing-topic-{selection.row_index}_{safe_product}_{safe_topic}_topics.md"

    lines: List[str] = []
    lines.append(f"# Blog Topics for {selection.product}")
    lines.append("")
    lines.append(f"- **Brand:** {selection.brand}")
    lines.append(f"- **Product:** {selection.product}")
    lines.append(f"- **Missing topic row:** {selection.row_index}")
    lines.append(f"- **Seed topic:** {selection.topic}")
    lines.append(f"- **Platforms covered:** {', '.join(platform for platform, _ in runs)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for platform, result in runs:
        lines.append(f"## {platform}")
        lines.append("")
        for idx, topic in enumerate(result.topics, start=1):
            lines.append(f"### {idx}. {refiner.to_title_case(topic.title)}")
            lines.append(f"- **Cluster ID:** `{topic.cluster_id}`")
            lines.append(f"- **Target persona:** {topic.target_persona}")
            lines.append(f"- **Blog post angle:** {topic.angle}")
            lines.append(f"- **Primary keyword:** `{refiner.refine(topic.primary_keyword)}`")

            supporting = [refiner.refine(k) for k in topic.supporting_keywords or []]
            supporting = [k for k in supporting if k]

            keyword_groups = _keyword_groups_to_mapping(getattr(topic, "keyword_groups", None))
            if keyword_groups:
                core = [refiner.refine(k) for k in (keyword_groups.get("core_seo_keywords") or []) if k]
                long_tail = [refiner.refine(k) for k in (keyword_groups.get("long_tail_keywords") or []) if k]
                context = [refiner.refine(k) for k in (keyword_groups.get("context_keywords") or []) if k]
                core = _dedupe_keywords(core)
                long_tail = _dedupe_keywords(long_tail)
                context = _dedupe_keywords(context)
            else:
                core, long_tail, context = [], [], []

            secondary_keywords = _dedupe_keywords(core or supporting)
            if secondary_keywords:
                lines.append(
                    f"- **Secondary keywords (Core SEO Keywords):** {', '.join(f'`{k}`' for k in secondary_keywords)}"
                )
            if long_tail:
                lines.append(f"- **Long Tails keywords:** {', '.join(f'`{k}`' for k in long_tail)}")
            if context:
                lines.append(f"- **Semantic SEO keywords:** {', '.join(f'`{k}`' for k in context)}")

            if topic.outline:
                lines.append("")
                lines.append("**Outline for the article:**")
                for bullet in topic.outline:
                    lines.append(f"- {refiner.to_title_case(bullet)}")

            editorial_notes = getattr(topic, "editorial_notes", []) or []
            if editorial_notes:
                lines.append("")
                lines.append("**Other important and relevant things:**")
                for note in editorial_notes:
                    lines.append(f"- {refiner.to_sentence_case(note)}")

            lines.append("")
        lines.append("---")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved missing-topics markdown to %s", md_path)
    return md_path

def append_metrics_db_entry(
    result: RunResult,
    metrics: RunMetrics,
    output_dir: Path,
    metrics_db_path: Path | None = None,
) -> Path:
    """
    Append a single run's metrics to a small JSON 'DB' file.

    File: kra_metrics_db.json
    Structure:
    {
      "runs": [
        {
          "run_id": "...",
          "timestamp": "...",
          "brand": "...",
          "product": "...",
          "platform": "...",
          "locale": "...",
          "input_file": "...",
          "num_clusters": 10,
          "num_topics": 42,
          "llm_prompt_tokens": 1234,
          "llm_completion_tokens": 567,
          "llm_total_tokens": 1801,
          "wall_time_seconds": 12.34
        },
        ...
      ]
    }
    """
    if metrics_db_path is None:
        metrics_db_path = output_dir / "kra_metrics_db.json"

    db_path = metrics_db_path

    # Load existing DB if present
    if db_path.is_file():
        try:
            db = json.loads(db_path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to parse existing metrics DB; recreating: %s", db_path)
            db = {"runs": []}
    else:
        db = {"runs": []}

    # Safely pull fields from metrics (they may or may not exist)
    brand = getattr(metrics, "brand", None)
    product = getattr(metrics, "product", None)
    platform = getattr(metrics, "platform", None)  # may be None
    file_path = getattr(metrics, "file_path", None)

    # Volumes
    keywords_processed = getattr(metrics, "keywords_processed", None)
    clusters_created = getattr(metrics, "clusters_created", None)
    clusters_used = getattr(metrics, "clusters_used_for_topics", None)
    topics_generated_raw = getattr(metrics, "topics_generated_raw", None)
    topics_after_dedup = getattr(metrics, "topics_after_dedup", None)
    existing_topics = getattr(metrics, "existing_topics_loaded", None)
    duplicates_dropped = getattr(metrics, "duplicates_dropped", None)

    # LLM / content index
    llm_requests = getattr(metrics, "llm_requests", None)
    llm_failures = getattr(metrics, "llm_failures", None)

    content_index_calls = getattr(metrics, "content_index_requests", None)
    content_index_errs = getattr(metrics, "content_index_failures", None)
    content_index_time = getattr(metrics, "content_index_duration_seconds", None)

    llm_prompt_tokens = getattr(metrics, "llm_prompt_tokens", None)
    llm_completion_tokens = getattr(metrics, "llm_completion_tokens", None)
    llm_duration_total = getattr(metrics, "llm_duration_seconds", None)

    run_duration = getattr(metrics, "run_duration_seconds", None)
    success = getattr(metrics, "success", None)

    llm_total_tokens = getattr(metrics, "llm_total_tokens", None)

    try:
        summary_text = metrics.as_cli_summary()
    except Exception as e:
        logger.warning("Failed to build CLI summary from metrics: %s", e)
        summary_text = None

    entry: Dict[str, Any] = {
        "run_id": result.run_id,
        # Use timezone-aware UTC (fixes DeprecationWarning)
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "brand": brand,
        "product": product,
        "platform": platform,
        "file_path": file_path,

        # Volumes
        "keywords_processed": keywords_processed,
        "clusters_created": clusters_created,
        "clusters_used": clusters_used,
        "topics_generated_raw": topics_generated_raw,
        "topics_after_dedup": topics_after_dedup,
        "existing_topics": existing_topics,
        "duplicates_dropped": duplicates_dropped,

        # LLM / content index
        "llm_requests": llm_requests,
        "llm_failures": llm_failures,
        "llm_duration_total": llm_duration_total,
        "llm_prompt_tokens": llm_prompt_tokens,
        "llm_completion_tokens": llm_completion_tokens,
        "llm_total_tokens": llm_total_tokens,
        "content_index_calls": content_index_calls,
        "content_index_errs": content_index_errs,
        "content_index_time": content_index_time,
        "run_duration": run_duration,
        "success": success,
        "summary": summary_text,
    }

    db.setdefault("runs", []).append(entry)
    db_path.write_text(json.dumps(db, indent=2), encoding="utf-8")
    logger.info("Appended metrics entry to %s", db_path)
    return db_path

def _print_summary(result: RunResult) -> None:
    """
    Human-readable summary for CLI usage.
    Logging already contains detailed metrics.
    """
    print(f"\nRun ID: {result.run_id}")
    print(f"Brand: {result.brand} | Product: {result.product} | Locale: {result.locale}")
    print(f"Top {len(result.clusters)} clusters (score desc):")
    for c in result.clusters[:5]:
        print(
            f"  - {c.cluster_id} [{c.metrics.intent}] "
            f"score={c.metrics.score:.3f} brand_fit={c.metrics.brand_fit:.2f} "
            f"label='{c.label}' (n={len(c.members)})"
        )

    print("\nTopic ideas:")
    for t in result.topics[:10]:
        print(f"  - {t.title}  (cluster={t.cluster_id})")

def _setup_logging() -> None:
    """
    Basic logging configuration for CLI usage.

    Library users can ignore this and configure logging themselves.
    """
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger.debug("Logging initialized with level=%s", logging.getLevelName(level))


def run_sync(
    req: RunRequest,
    platform: Optional[str] = None,
    use_content_index: bool = True,
    records: Optional[List[KeywordRecord]] = None,
    seed_topic: Optional[str] = None,
    include_product_in_title: bool = True,
    source: str = "csv",
) -> tuple[RunResult, RunMetrics]:
    workflow_agent = build_keyword_workflow_agent(source)
    return workflow_agent.execute(
        req=req,
        platform=platform,
        use_content_index=use_content_index,
        seed_topic=seed_topic,
        include_product_in_title=include_product_in_title,
        provided_records=records,
    )




def main() -> None:
    """
    CLI entrypoint.

    If --file is omitted or empty, the importer will look in sensible defaults:
      - {KRA_DATA_DIR}/keywords.xlsx|csv
      - ./src/data/samples/keywords.xlsx|csv
      - /mnt/data/samples/keywords.xlsx|csv

    If --file is provided but does not exist, we EXIT with an error and DO NOT
    silently fall back to any default file.
    """
    _setup_logging()

    parser = argparse.ArgumentParser(
        description="Run Blog Keyword Analyzer agent on a CSV/XLSX file."
    )
    parser.add_argument("--file", dest="file_path", default="", help="Path to CSV/XLSX (optional).")
    parser.add_argument(
        "--missing-topics-file",
        dest="missing_topics_file",
        default="",
        help="Path to a missing-topics markdown file with Brand/Product metadata and a table.",
    )
    parser.add_argument(
        "--missing-topic-row",
        dest="missing_topic_row",
        type=int,
        default=0,
        help="1-based row number from the missing-topics table to process.",
    )
    parser.add_argument("--brand", default="Aspose")
    parser.add_argument("--product", default="Aspose.Cells")
    parser.add_argument(
        "--platform",
        dest="platform",
        default="",
        help="Optional target platform, e.g. python, java, csharp (used to avoid duplicates).",
    )
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--k", dest="clustering_k", type=int, default=None, help="Force number of clusters.")
    parser.add_argument("--top", dest="top_clusters", type=int, default=settings.TOP_CLUSTERS)
    parser.add_argument("--max-rows", dest="max_rows", type=int, default=settings.MAX_ROWS)
    # By default we DO use content index; this flag turns it OFF.
    parser.add_argument(
        "--no-content-index",
        dest="use_content_index",
        action="store_false",
        help="Disable search for existing topics via content index service.",
    )
    parser.set_defaults(use_content_index=True)

    # NEW: SerpAPI options
    parser.add_argument(
        "--use-serp-api",
        action="store_true",
        help="Fetch keywords from Google SERP via SerpAPI instead of reading a file.",
    )
    parser.add_argument(
        "--use-llm-keywords",
        action="store_true",
        help="Skip SerpAPI and fetch keywords directly from the built-in LLM keyword generator.",
    )
    parser.add_argument(
        "--serp-topic",
        dest="serp_topic",
        default="",
        help="Topic/angle to seed the SerpAPI query, e.g. 'convert CSV to Excel'.",
    )

    # NEW: Include product name in title banner (default True)
    parser.add_argument(
        "--include-product-in-title",
        dest="include_product_in_title",
        action="store_true",
        help="Include product name in the printed title banner (default: enabled).",
    )
    parser.add_argument(
        "--no-product-in-title",
        dest="include_product_in_title",
        action="store_false",
        help="Do not include product name in the printed title banner.",
    )
    parser.set_defaults(include_product_in_title=True)

    args = parser.parse_args()

    if args.use_serp_api and args.use_llm_keywords:
        raise SystemExit("Use only one of --use-serp-api or --use-llm-keywords.")

    if args.missing_topics_file:
        try:
            missing_topics_path = _resolve_input_file(args.missing_topics_file)
        except FileNotFoundError as e:
            print(f"\n{e}")
            raise SystemExit(1)

        if args.missing_topic_row < 1:
            raise SystemExit("--missing-topic-row must be a positive table row index.")

        assert missing_topics_path is not None
        selection = _parse_missing_topics_selection(missing_topics_path, args.missing_topic_row)
        if not selection.platforms:
            print(
                f"Row #{selection.row_index} only contains GENERAL or unsupported platforms; nothing to generate."
            )
            raise SystemExit(0)

        req = RunRequest(
            brand=selection.brand,
            product=selection.product,
            locale=args.locale,
            file_path="",
            clustering_k=args.clustering_k,
            top_clusters=args.top_clusters,
            max_rows=args.max_rows,
        )

        logger.info(
            "CLI invoked in missing-topics mode: brand=%s product=%s row=%s topic=%s platforms=%s",
            selection.brand,
            selection.product,
            selection.row_index,
            selection.topic,
            ",".join(selection.platforms),
        )

        md_paths: List[Path] = []
        for platform in selection.platforms:
            result, metrics = run_sync(
                req,
                platform=platform,
                use_content_index=args.use_content_index,
                seed_topic=selection.topic,
                include_product_in_title=args.include_product_in_title,
                source="llm" if args.use_llm_keywords else "serp",
            )

            _print_summary(result)
            print()
            print(metrics.as_cli_summary())
            print()

            safe_product = _brand_slug(selection.product)
            safe_topic = _brand_slug(selection.topic)[:60] or f"row-{selection.row_index}"
            if len(selection.platforms) == 1:
                file_name = f"missing-topic-{selection.row_index}_{safe_product}_{safe_topic}_topics.md"
            else:
                file_name = (
                    f"missing-topic-{selection.row_index}_{safe_product}_{platform}_{safe_topic}_topics.md"
                )

            brand_out_dir = _resolve_brand_output_dir(selection.brand)
            md_paths.append(
                write_topics_markdown(
                    result,
                    output_dir=brand_out_dir,
                    platform=platform,
                    file_name=file_name,
                )
            )

        for md_path in md_paths:
            print(md_path)
        return

    # Decide ingestion mode: file vs SerpAPI
    if args.use_serp_api or args.use_llm_keywords:
        # We won't use file import, so no need to resolve a file path
        resolved_input: Optional[Path] = None
    else:
        # Old behavior: require and resolve the file
        if not args.file_path:
            raise SystemExit(
                "Input file is required unless you specify --use-serp-api or --use-llm-keywords."
            )

        try:
            resolved_input = _resolve_input_file(args.file_path)
        except FileNotFoundError as e:
            print(f"\nâŒ {e}")
            raise SystemExit(1)

    # Build request (defaults come from .env-backed settings)
    req = RunRequest(
        brand=args.brand,
        product=args.product,
        locale=args.locale,
        # If resolved_input is None, we pass empty string -> importer may search defaults
        file_path=str(resolved_input) if resolved_input is not None else "",
        clustering_k=args.clustering_k,
        top_clusters=args.top_clusters,
        max_rows=args.max_rows,
        # weights keep defaults from model unless you want to override here
    )

    logger.info(
        "CLI invoked with brand=%s product=%s locale=%s platform=%s file_path=%s",
        req.brand,
        req.product,
        req.locale,
        args.platform or None,
        req.file_path,
    )

    # Orchestrate
    result, metrics = run_sync(
        req,
        platform=args.platform or None,
        use_content_index=args.use_content_index,
        seed_topic=(args.serp_topic.strip() or args.product) if (args.use_serp_api or args.use_llm_keywords) else None,
        include_product_in_title=args.include_product_in_title,
        source="llm" if args.use_llm_keywords else ("serp" if args.use_serp_api else "csv"),
    )

    # Print a brief human summary of clusters/topics (optional)
    _print_summary(result)

    # Save JSON artifact under KRA_OUTPUT_DIR
    out_dir = _resolve_output_dir()
    brand_slug = _brand_slug(result.brand)
    out_path = out_dir / f"kra_result_{brand_slug}_{result.run_id}.json"
    # Uncomment this section if you want to save JSON file
    """
    with open(out_path, "w", encoding="utf-8") as f:
        # pydantic v2
        f.write(result.model_dump_json(indent=2))

    print(f"\nSaved full result to {out_path}")
    """

    # New: derived artifacts
    try:
        platform = args.platform or None
        brand_out_dir = _resolve_brand_output_dir(result.brand)
        print(brand_out_dir)
        # Save the generated topics in MD file
        write_topics_markdown(result, output_dir=brand_out_dir, platform=platform)

        # Insert the metrics in DB file
        # metrics_db_path = _get_metrics_db_path(out_dir)
        # append_metrics_db_entry(
        #     result,
        #     metrics,
        #     output_dir=out_dir,
        #     metrics_db_path=metrics_db_path,
        # )
    except Exception as e:
        logger.warning("Post-processing (topics/metrics) failed: %s", e, exc_info=True)

    # ðŸ”¹ NOW print metrics summary right after JSON file line
    print()  # blank line for spacing
    print(metrics.as_cli_summary())
    print()  # trailing newline



if __name__ == "__main__":
    main()
