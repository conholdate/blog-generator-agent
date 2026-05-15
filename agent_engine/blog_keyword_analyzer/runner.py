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
    canonical_blog_platform_key,
    KeywordRefiner,
    canonical_product_name,
    canonical_platform_label,
    normalize_missing_platform,
    normalize_product_short_name,
    platform_base_display,
    platform_header_display,
    require_supported_platform,
    supported_platform_error,
    supported_platform_options_text,
)
from agent_engine.blog_keyword_analyzer.tools.google_sheets import (
    append_output_row,
    build_output_row,
    ensure_output_headers,
    fetch_topic_sheet_selection,
    normalize_spreadsheet_id,
)
from agent_engine.blog_keyword_analyzer.workflow_support import clean_keyword_phrase

logger = logging.getLogger(__name__)
refiner = KeywordRefiner()


def _platform_matches_selection(selected_platform: str, available_platforms: List[str]) -> bool:
    if selected_platform == "general":
        return any(str(platform).strip().lower() == "general" for platform in available_platforms)
    if selected_platform in available_platforms:
        return True

    selected_blog_key = canonical_blog_platform_key(selected_platform)
    if not selected_blog_key:
        return False

    for platform in available_platforms:
        if canonical_blog_platform_key(platform) == selected_blog_key:
            return True
    return False


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


def _display_keyword(value: Any, product: str) -> str:
    text = refiner.refine(value)
    if not text:
        return ""
    text = clean_keyword_phrase(text)
    short_product = normalize_product_short_name(product)
    if short_product:
        text = re.sub(r"(?i)\bAsp(?:\.{3}|…)\b", short_product, text)
        text = re.sub(r"(?i)\bGroup(?:\.{3}|…)\b", short_product, text)
    text = _sanitize_display_text(text)
    return re.sub(r"\s{2,}", " ", text).strip(" -,:;")


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
    invalid_platforms: List[str] = []

    for match in table_row_re.finditer(text):
        current_row = int(match.group(1))
        if current_row != row_index:
            continue

        selected_topic = match.group(2).strip()
        platform_tokens = [p.strip() for p in match.group(3).split(",")]
        selected_platforms = []
        for token in platform_tokens:
            if not token:
                continue
            normalized = normalize_missing_platform(token)
            if normalized and normalized not in selected_platforms:
                selected_platforms.append(normalized)
            elif not normalized and token.upper() != "GENERAL":
                invalid_platforms.append(token)
        break

    if not selected_topic:
        raise ValueError(f"Row #{row_index} was not found in missing topics table: {path}")
    if invalid_platforms:
        invalid = ", ".join(invalid_platforms)
        raise ValueError(
            f"Row #{row_index} contains unsupported platform value(s): {invalid}. "
            f"{supported_platform_error(invalid_platforms[0])}"
        )

    return MissingTopicSelection(
        brand=brand_match.group(1).strip(),
        product=canonical_product_name(
            brand_match.group(1).strip(),
            product_match.group(1).strip(),
        ),
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

def _canonical_brand_folder(brand: str) -> str:
    normalized = " ".join(str(brand or "").strip().split())
    brand_key = normalized.lower().replace(" ", "")
    folder_map = {
        "aspose": "Aspose",
        "conholdate": "Conholdate",
        "familiarize": "Familiarize",
        "groupdocs": "GroupDocs",
        "aspose.cloud": "Aspose.Cloud",
        "aspose-cloud": "Aspose.Cloud",
        "conholdate.cloud": "Conholdate.Cloud",
        "conholdate-cloud": "Conholdate.Cloud",
        "groupdocs.cloud": "GroupDocs.Cloud",
        "groupdocs-cloud": "GroupDocs.Cloud",
    }
    return folder_map.get(brand_key, normalized or "unknown")

def _resolve_brand_output_dir(brand_folder: str) -> Path:
    root = _project_root()
    canonical_folder = _canonical_brand_folder(brand_folder)
    out_dir = (root / "content" / canonical_folder / "output").resolve()
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


def _topic_title_platform_display(title: str, platform: Optional[str]) -> str:
    out = " ".join((title or "").strip().split())
    canonical = canonical_platform_label(platform)
    base = platform_base_display(platform)
    if not out or not canonical or not base or canonical == base:
        return out
    return _sanitize_display_text(re.sub(re.escape(canonical), base, out, flags=re.IGNORECASE), platform)


def _sanitize_display_text(text: str, platform: Optional[str] = None) -> str:
    out = " ".join((text or "").strip().split())
    if not out:
        return ""
    out = out.replace("â€‘", "-").replace("â€“", "-").replace("â€”", "-")
    out = out.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    out = re.sub(r"(?i)\bwith\s+in\s+\.net\b", "in .NET", out)
    out = re.sub(r"(?i)\bwith\s+for\s+\.net\b", "for .NET", out)
    out = re.sub(r"(?i)\bin\s+in\s+\.net\b", "in .NET", out)
    out = re.sub(r"(?i)\bwith\s+in\s+([A-Za-z0-9.+#]+)\b", r"in \1", out)
    out = re.sub(r"(?i)\badd\s+pages\s+to\s+PDF\s+with\s+for\s+in\s+\.NET\b", "add pages to PDF in .NET", out)
    out = re.sub(r"(?i)\badd\s+pages\s+to\s+PDF\s+with\s+for\s+in\s+([A-Za-z0-9.+#]+)\b", r"add pages to PDF in \1", out)
    out = re.sub(r"(?i)\bfor[-\s]?in\s+loop\b", "foreach loop", out)
    out = re.sub(r"(?i)\bfor\s+in\s+loop\b", "foreach loop", out)
    out = re.sub(r"(?i)\busing\s+a\s+for\s+in\s+loop\b", "using a loop", out)
    out = re.sub(r"(?i)\bfor\s+in\s+syntax\b", "foreach syntax", out)
    out = re.sub(r"(?i)\busing\s+a\s+foreach\s+loop\b", "using a loop", out)
    out = re.sub(r"(?i)\s+with\s+Aspose\.PDF\s+with\s+Aspose\.PDF\b", " with Aspose.PDF", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" -,:;")
    return out


def _content_platform_display(text: str, platform: Optional[str]) -> str:
    out = " ".join((text or "").strip().split())
    canonical = canonical_platform_label(platform)
    header = platform_header_display(platform)
    base = platform_base_display(platform)
    if not out or not canonical or not base or canonical == base:
        return out

    for value in {canonical, header}:
        if value and value != base:
            out = re.sub(re.escape(value), base, out, flags=re.IGNORECASE)
    return _sanitize_display_text(out, platform)


def _fix_step_by_step_case(text: str) -> str:
    return re.sub(r"(?i)\bSTEP\s*[- ]\s*by\s*[- ]\s*STEP\b", "Step-by-Step", text or "")


def _display_question(text: str, platform: Optional[str]) -> str:
    had_question_mark = str(text or "").strip().endswith("?")
    out = _content_platform_display(text, platform)
    out = _fix_step_by_step_case(refiner.to_sentence_case(out))
    out = re.sub(r"\bi\b", "I", out)
    out = re.sub(r"(?i)\bextract\s+Pages\b", "extract pages", out)
    out = re.sub(r"(?i)\bextract\s+Images\b", "extract images", out)
    out = re.sub(r"(?i)\bextract\s+Text\b", "extract text", out)
    out = re.sub(r"(?i)\bPDF\s+Pages\b", "PDF pages", out)
    out = re.sub(r"(?i)\bPDF\s+Images\b", "PDF images", out)
    canonical = platform_base_display(platform) or canonical_platform_label(platform)
    if canonical and canonical.lower() not in out.lower():
        out = out.rstrip("?")
        out = f"{out} in {canonical}"
    if had_question_mark and not out.endswith("?"):
        out = out.rstrip(".") + "?"
    return out


def _display_editorial_note(text: str, platform: Optional[str]) -> str:
    out = _content_platform_display(text, platform)
    def _clean_note(value: str) -> str:
        value = re.sub(
            r"(?i)creating\s+a\s+Document\s+inserting\s+pages\s+and\s+saving\s+the\s+result",
            "creating a Document, inserting pages, and saving the result",
            value,
        )
        value = re.sub(r"(?i)\bAspose\.PDF\s+s\b", "Aspose.PDF's", value)
        value = re.sub(r"(?i)\blarge\s+pdfs\b", "large PDFs", value)
        value = re.sub(r"(?i)\bseo\b", "SEO", value)
        value = re.sub(r"(?i)\bserp\b", "SERP", value)
        value = re.sub(r"(?i)\bfaq\b", "FAQ", value)
        value = re.sub(r"(?i)\bc#\b", "C#", value)
        value = re.sub(r"(?i)\bfor\s+in\s+loop\s+syntax\b", "foreach syntax", value)
        value = re.sub(r"(?i)\bfor\s+in\s+loop\b", "foreach loop", value)
        return value

    out = _clean_note(out)
    out = re.sub(
        r"(?i)(answer questions such as)\s+(.+)$",
        lambda m: f"{m.group(1)} {_display_question(m.group(2), platform).rstrip('?')}",
        out,
    )
    out = _fix_step_by_step_case(refiner.to_sentence_case(out))
    out = _clean_note(out)
    out = re.sub(r"\bi\b", "I", out)
    return out

def _brand_slug(brand: str) -> str:
    return _normalize_topic_key(brand or "unknown")


def _derive_output_sheet_name(product: str) -> str:
    short_name = normalize_product_short_name(product)
    if "." in short_name:
        return short_name.split(".", 1)[1].strip() or short_name
    return short_name or product


def _resolve_output_sheet_name(
    *,
    product: str,
    configured_name: str,
    mode: str,
) -> str:
    configured = (configured_name or "").strip()
    normalized_mode = (mode or "product_suffix").strip().lower()
    short_name = normalize_product_short_name(product)

    if normalized_mode == "fixed":
        if not configured:
            raise ValueError(
                "--google-sheet-output-worksheet is required when "
                "--google-sheet-output-mode is 'fixed'."
            )
        return configured

    if normalized_mode == "product_full":
        return short_name or product

    if normalized_mode == "product_suffix":
        return _derive_output_sheet_name(product)

    raise ValueError(
        "Unsupported google sheet output mode "
        f"'{mode}'. Allowed values: product_suffix, product_full, fixed."
    )

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


def _opportunity_group_key(opportunity: Any) -> str:
    formats = sorted(str(fmt).lower() for fmt in (getattr(opportunity, "formats", []) or []))
    action = (getattr(opportunity, "action", None) or "").lower()
    language = (getattr(opportunity, "language", None) or "").lower()
    page_type = (getattr(opportunity, "best_page_type", "") or "").lower()
    recommendation = (getattr(opportunity, "recommended_action", "") or "").lower()
    if formats or action or language:
        return "|".join([",".join(formats), action, language, page_type, recommendation])
    return _keyword_intent_key(getattr(opportunity, "keyword", "") or "")


def _group_keyword_opportunities(opportunities: List[Any]) -> List[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for opportunity in opportunities:
        key = _opportunity_group_key(opportunity)
        if not key:
            continue
        group = groups.setdefault(key, {"primary": opportunity, "variants": []})
        primary = group["primary"]
        if getattr(opportunity, "final_priority_score", 0) > getattr(primary, "final_priority_score", 0):
            group["variants"].append(primary)
            group["primary"] = opportunity
        else:
            group["variants"].append(opportunity)
    return sorted(
        groups.values(),
        key=lambda item: getattr(item["primary"], "final_priority_score", 0),
        reverse=True,
    )


def _product_page_opportunities(result: RunResult, product_name: str, platform: Optional[str]) -> List[str]:
    values: List[str] = []
    for opportunity in result.keyword_opportunities or []:
        if getattr(opportunity, "recommended_action", "") != "product_page":
            continue
        keyword = _content_platform_display(_display_keyword(opportunity.keyword, product_name), platform)
        if keyword:
            values.append(keyword)
    return _dedupe_keywords(values)[:5]


def _keyword_group_key(text: str) -> str:
    return _keyword_intent_key(text)


def _platform_specific(text: str, platform: Optional[str]) -> bool:
    if not platform:
        return True
    canonical = canonical_platform_label(platform)
    if not canonical:
        return True
    lower = (text or "").lower()
    canonical_lower = canonical.lower()
    if canonical_lower in lower:
        return True
    if canonical_lower == ".net":
        return any(token in lower for token in (".net", "c#", "csharp", "dotnet"))
    if canonical_lower == "node.js":
        return any(token in lower for token in ("node.js", "nodejs", "node "))
    return False


def _normalize_keyword_groups_for_display(
    *,
    core: List[str],
    long_tail: List[str],
    context: List[str],
    primary_intent_key: str,
    platform: Optional[str],
) -> tuple[List[str], List[str], List[str]]:
    core_out: List[str] = []
    long_out: List[str] = []
    context_out: List[str] = list(context)
    seen: set[str] = {primary_intent_key}

    for kw in _dedupe_keywords(core):
        key = _keyword_group_key(kw)
        if not key or key in seen:
            continue
        if platform and not _platform_specific(kw, platform):
            context_out.append(kw)
            continue
        core_out.append(kw)
        seen.add(key)

    for kw in _dedupe_keywords(long_tail):
        key = _keyword_group_key(kw)
        if not key or key in seen:
            continue
        long_out.append(kw)
        seen.add(key)

    if re.search(r"(?i)\b(add|insert)\s+pages?\s+(?:to|into)\s+pdf\b", " ".join([*core, *long_tail, *context])):
        context_out.extend(
            [
                "PDF page insertion",
                "PDF editing workflow",
                "PDF document modification",
                "page order management",
                "blank PDF pages",
            ]
        )

    context_clean: List[str] = []
    context_seen: set[str] = set(seen)
    for kw in _dedupe_keywords(context_out):
        key = _keyword_group_key(kw)
        if not key or key in context_seen:
            continue
        context_clean.append(kw)
        context_seen.add(key)

    return core_out, long_out, context_clean

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
    product_name = result.product

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

    if not result.topics:
        lines.append("_No valid topics were generated for this run._")
        lines.append("")
        md_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Saved topics markdown to %s", md_path)
        return md_path

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
        primary_kw = _display_keyword(primary_kw_r, product_name)

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
        supporting_kws = [_display_keyword(k, product_name) for k in supporting_kws_r]
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
        keyword_analysis = _keyword_groups_to_mapping(pick("keyword_analysis", {}) or {})
        product_page_opportunities = _product_page_opportunities(result, product_name, platform)

        topic_title = _fix_step_by_step_case(refiner.to_title_case(_topic_title_platform_display(title, platform)))
        topic_title = _sanitize_display_text(topic_title, platform)
        lines.append(f"## {idx}. {topic_title}")
        if cluster_id is not None:
            lines.append(f"- **Cluster ID:** `{cluster_id}`")
        if persona:
            lines.append(f"- **Target persona:** {_sanitize_display_text(_content_platform_display(persona, platform), platform)}")
        if angle:
            lines.append(f"- **Blog post angle:** {_sanitize_display_text(_fix_step_by_step_case(_content_platform_display(angle, platform)), platform)}")
        if primary_kw:
            lines.append(f"- **Primary keyword:** `{_content_platform_display(primary_kw, platform)}`")

        if keyword_groups:
            core = [_display_keyword(k, product_name) for k in (keyword_groups.get("core_seo_keywords") or []) if k]
            long_tail = [_display_keyword(k, product_name) for k in (keyword_groups.get("long_tail_keywords") or []) if k]
            context = [_display_keyword(k, product_name) for k in (keyword_groups.get("context_keywords") or []) if k]
            core = [k for k in core if _keyword_intent_key(k) != primary_intent_key]
            long_tail = [k for k in long_tail if _keyword_intent_key(k) != primary_intent_key]
            context = [k for k in context if _keyword_intent_key(k) != primary_intent_key]
            core, long_tail, context = _normalize_keyword_groups_for_display(
                core=core,
                long_tail=long_tail,
                context=context,
                primary_intent_key=primary_intent_key,
                platform=platform,
            )
        else:
            core, long_tail, context = [], [], []

        secondary_keywords = _dedupe_keywords(core or supporting_kws)
        if secondary_keywords:
            lines.append(
                "- **Secondary keywords (Core SEO Keywords):** "
                + ", ".join(f'`{_content_platform_display(kw, platform)}`' for kw in secondary_keywords)
            )

        if long_tail:
            lines.append(
                f"- **Long Tails keywords:** {', '.join(f'`{_content_platform_display(k, platform)}`' for k in long_tail)}"
            )
        if context:
            lines.append(
                f"- **Semantic SEO keywords:** {', '.join(f'`{_content_platform_display(k, platform)}`' for k in context)}"
            )
        if product_page_opportunities:
            lines.append(
                "- **Product-page opportunities:** "
                + ", ".join(f"`{kw}`" for kw in product_page_opportunities)
            )
        question_keywords = keyword_analysis.get("question_keywords") or []
        entities = keyword_analysis.get("entities") or []
        if question_keywords:
            lines.append(
                f"- **Question keywords:** {', '.join(f'`{_display_question(q, platform)}`' for q in question_keywords[:5])}"
            )
        if entities:
            display_entities = []
            for entity in entities:
                entity_text = _content_platform_display(str(entity), platform)
                if not entity_text or re.search(r"(?i)\b(with\s+in|for\s+in|with\s+for|for[-\s]?in)\b", entity_text):
                    continue
                if len(entity_text.split()) > 4 and not re.search(r"(?i)\b(Aspose|Java|Python|\.NET|C#|PDF|DOCX|XLSX|PPTX)\b", entity_text):
                    continue
                display_entities.append(entity_text)
            display_entities = _dedupe_keywords(display_entities)[:5]
        else:
            display_entities = []
        if display_entities:
            lines.append(
                f"- **Entity keywords:** {', '.join(f'`{e}`' for e in display_entities)}"
            )
        primary_analysis = keyword_analysis.get("primary_keyword") or {}
        if isinstance(primary_analysis, Mapping) and primary_analysis.get("placement"):
            placements = primary_analysis.get("placement") or []
            if placements:
                lines.append(
                    "- **Primary keyword placement:** "
                    + ", ".join(f"`{_content_platform_display(str(p), platform)}`" for p in placements)
                )
        if outline:
            lines.append("")
            lines.append("**Outline for the article:**")
            for bullet in outline:
                line_item = _sanitize_display_text(_fix_step_by_step_case(refiner.to_title_case(_content_platform_display(bullet, platform))), platform)
                lines.append(f"- {line_item}")

        if editorial_notes:
            lines.append("")
            lines.append("**Other important and relevant things:**")
            for note in editorial_notes:
                lines.append(f"- {_display_editorial_note(note, platform)}")

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
        product_page_opportunities = _product_page_opportunities(result, selection.product, platform)
        lines.append(f"## {platform}")
        lines.append("")
        for idx, topic in enumerate(result.topics, start=1):
            lines.append(f"### {idx}. {_sanitize_display_text(refiner.to_title_case(_topic_title_platform_display(topic.title, platform)), platform)}")
            lines.append(f"- **Cluster ID:** `{topic.cluster_id}`")
            lines.append(f"- **Target persona:** {_sanitize_display_text(_content_platform_display(topic.target_persona, platform), platform)}")
            lines.append(f"- **Blog post angle:** {_sanitize_display_text(_fix_step_by_step_case(_content_platform_display(topic.angle, platform)), platform)}")
            lines.append(
                f"- **Primary keyword:** `{_content_platform_display(_display_keyword(topic.primary_keyword, selection.product), platform)}`"
            )

            supporting = [_display_keyword(k, selection.product) for k in topic.supporting_keywords or []]
            supporting = [k for k in supporting if k]

            keyword_groups = _keyword_groups_to_mapping(getattr(topic, "keyword_groups", None))
            primary_intent_key = _keyword_intent_key(_display_keyword(topic.primary_keyword, selection.product))
            if keyword_groups:
                core = [_display_keyword(k, selection.product) for k in (keyword_groups.get("core_seo_keywords") or []) if k]
                long_tail = [_display_keyword(k, selection.product) for k in (keyword_groups.get("long_tail_keywords") or []) if k]
                context = [_display_keyword(k, selection.product) for k in (keyword_groups.get("context_keywords") or []) if k]
                core, long_tail, context = _normalize_keyword_groups_for_display(
                    core=core,
                    long_tail=long_tail,
                    context=context,
                    primary_intent_key=primary_intent_key,
                    platform=platform,
                )
            else:
                core, long_tail, context = [], [], []

            secondary_keywords = _dedupe_keywords(core or supporting)
            if secondary_keywords:
                lines.append(
                    "- **Secondary keywords (Core SEO Keywords):** "
                    + ", ".join(f'`{_content_platform_display(k, platform)}`' for k in secondary_keywords)
                )
            if long_tail:
                lines.append(
                    f"- **Long Tails keywords:** {', '.join(f'`{_content_platform_display(k, platform)}`' for k in long_tail)}"
                )
            if context:
                lines.append(
                    f"- **Semantic SEO keywords:** {', '.join(f'`{_content_platform_display(k, platform)}`' for k in context)}"
                )
            if product_page_opportunities:
                lines.append(
                    "- **Product-page opportunities:** "
                    + ", ".join(f"`{_content_platform_display(k, platform)}`" for k in product_page_opportunities)
                )

            if topic.outline:
                lines.append("")
                lines.append("**Outline for the article:**")
                for bullet in topic.outline:
                    lines.append(f"- {_sanitize_display_text(refiner.to_title_case(_content_platform_display(bullet, platform)), platform)}")

            editorial_notes = getattr(topic, "editorial_notes", []) or []
            if editorial_notes:
                lines.append("")
                lines.append("**Other important and relevant things:**")
                for note in editorial_notes:
                    lines.append(f"- {_display_editorial_note(note, platform)}")

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
    parser.add_argument(
        "--google-sheet-input-id",
        dest="google_sheet_input_id",
        default="",
        help="Google Sheets spreadsheet ID for the live topic-input sheet.",
    )
    parser.add_argument(
        "--google-sheet-input-worksheet",
        dest="google_sheet_input_worksheet",
        default="",
        help="Worksheet/tab name in the live topic-input sheet.",
    )
    parser.add_argument(
        "--google-sheet-row",
        dest="google_sheet_row",
        type=int,
        default=0,
        help="1-based sheet row to process from the live topic-input sheet.",
    )
    parser.add_argument(
        "--google-sheet-output-id",
        dest="google_sheet_output_id",
        default="",
        help="Google Sheets spreadsheet ID for appending generated topic results.",
    )
    parser.add_argument(
        "--google-sheet-output-worksheet",
        dest="google_sheet_output_worksheet",
        default="",
        help="Worksheet/tab name in the live topic-output sheet.",
    )
    parser.add_argument(
        "--google-sheet-output-mode",
        dest="google_sheet_output_mode",
        default="product_suffix",
        help="How to choose the output worksheet: product_suffix, product_full, or fixed.",
    )
    parser.add_argument("--brand", default="Aspose")
    parser.add_argument("--product", default="Aspose.Cells")
    parser.add_argument(
        "--platform",
        dest="platform",
        default="",
        help=f"Optional target platform. Allowed values: {supported_platform_options_text()}",
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

    live_sheet_mode = bool(args.google_sheet_input_id or args.google_sheet_input_worksheet or args.google_sheet_row)
    missing_topics_mode = bool(args.missing_topics_file)
    if live_sheet_mode and missing_topics_mode:
        raise SystemExit(
            "Use only one of missing-topics mode or live Google Sheet mode in the same run."
        )

    selected_platform: Optional[str] = None
    if args.platform:
        if args.platform.strip().lower() == "general":
            selected_platform = "general"
        else:
            try:
                selected_platform = require_supported_platform(args.platform)
            except ValueError as e:
                raise SystemExit(str(e))

    if live_sheet_mode:
        if not settings.GOOGLE_SERVICE_ACCOUNT_FILE:
            raise SystemExit(
                "GOOGLE_SERVICE_ACCOUNT_FILE must be set to use live Google Sheet mode."
            )
        if not args.google_sheet_input_id:
            raise SystemExit("--google-sheet-input-id is required in live Google Sheet mode.")
        if not args.google_sheet_input_worksheet:
            raise SystemExit("--google-sheet-input-worksheet is required in live Google Sheet mode.")
        if args.google_sheet_row < 2:
            raise SystemExit("--google-sheet-row must be >= 2 because row 1 contains headers.")
        if not args.platform:
            raise SystemExit(
                "--platform is required in live Google Sheet mode and must target one supported platform or General."
            )

        try:
            selection = fetch_topic_sheet_selection(
                credentials_file=settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                spreadsheet_id=args.google_sheet_input_id,
                worksheet_name=args.google_sheet_input_worksheet,
                row_index=args.google_sheet_row,
            )
        except Exception as e:
            raise SystemExit(str(e))

        if not selection.platforms:
            raise SystemExit(
                f"Row #{selection.row_index} has no missing supported platform columns marked as NO."
            )
        if not _platform_matches_selection(selected_platform, selection.platforms):
            available = ", ".join(
                "General" if str(p).strip().lower() == "general" else platform_header_display(p)
                for p in selection.platforms
            )
            selected_platform_display = (
                "General" if selected_platform == "general" else platform_header_display(selected_platform)
            )
            raise SystemExit(
                f"Row #{selection.row_index} does not include the selected platform "
                f"'{selected_platform_display}'. Available platforms: {available}."
            )

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
            "CLI invoked in live-sheet mode: brand=%s product=%s row=%s topic=%s platform=%s",
            selection.brand,
            selection.product,
            selection.row_index,
            selection.topic,
            "General" if selected_platform == "general" else selected_platform,
        )

        run_platform = None if selected_platform == "general" else selected_platform

        output_spreadsheet_id = normalize_spreadsheet_id(
            args.google_sheet_output_id or args.google_sheet_input_id
        )
        output_worksheet_name = _resolve_output_sheet_name(
            product=selection.product,
            configured_name=args.google_sheet_output_worksheet,
            mode=args.google_sheet_output_mode,
        )
        logger.info(
            "Live-sheet output target resolved: spreadsheet=%s worksheet=%s mode=%s",
            output_spreadsheet_id,
            output_worksheet_name,
            args.google_sheet_output_mode,
        )

        result, metrics = run_sync(
            req,
            platform=run_platform,
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
        file_name = (
            f"sheet-topic-{selection.row_index}_{safe_product}_{selected_platform}_{safe_topic}_topics.md"
        )

        brand_out_dir = _resolve_brand_output_dir(selection.brand)
        md_path = write_topics_markdown(
            result,
            output_dir=brand_out_dir,
            platform=run_platform,
            file_name=file_name,
        )

        try:
            ensure_output_headers(
                credentials_file=settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                spreadsheet_id=output_spreadsheet_id,
                worksheet_name=output_worksheet_name,
            )
            append_output_row(
                credentials_file=settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                spreadsheet_id=output_spreadsheet_id,
                worksheet_name=output_worksheet_name,
                row_payload=build_output_row(
                    selection=selection,
                    selected_platform="General" if selected_platform == "general" else selected_platform,
                    result=result,
                    markdown_path=str(md_path),
                ),
            )
        except Exception as e:
            logger.warning("Google Sheet output append failed: %s", e, exc_info=True)
            raise SystemExit(f"Run completed but failed to append output row: {e}")

        print(md_path)
        return

    if args.missing_topics_file:
        try:
            missing_topics_path = _resolve_input_file(args.missing_topics_file)
        except FileNotFoundError as e:
            print(f"\n{e}")
            raise SystemExit(1)
        except ValueError as e:
            raise SystemExit(str(e))

        if args.missing_topic_row < 1:
            raise SystemExit("--missing-topic-row must be a positive table row index.")

        assert missing_topics_path is not None
        selection = _parse_missing_topics_selection(missing_topics_path, args.missing_topic_row)
        if not selection.platforms:
            print(
                f"Row #{selection.row_index} only contains GENERAL or unsupported platforms; nothing to generate."
            )
            raise SystemExit(0)

        if not selected_platform:
            raise SystemExit(
                "--platform is required in missing-topics mode and must target one supported platform."
            )
        if not _platform_matches_selection(selected_platform, selection.platforms):
            available = ", ".join(platform_header_display(p) for p in selection.platforms)
            raise SystemExit(
                f"Row #{selection.row_index} does not include the selected platform "
                f"'{platform_header_display(selected_platform)}'. Available platforms: {available}."
            )

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
            selected_platform,
        )

        platform_label = platform_header_display(selected_platform)
        print(
            f"Processing missing topic row #{selection.row_index} for platform: {platform_label}"
        )
        print()

        result, metrics = run_sync(
            req,
            platform=selected_platform,
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
        file_name = (
            f"missing-topic-{selection.row_index}_{safe_product}_{selected_platform}_{safe_topic}_topics.md"
        )

        brand_out_dir = _resolve_brand_output_dir(selection.brand)
        md_path = write_topics_markdown(
            result,
            output_dir=brand_out_dir,
            platform=selected_platform,
            file_name=file_name,
        )

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
        selected_platform,
        req.file_path,
    )

    # Orchestrate
    result, metrics = run_sync(
        req,
        platform=selected_platform,
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
        platform = selected_platform
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
