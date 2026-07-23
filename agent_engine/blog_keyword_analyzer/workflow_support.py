from __future__ import annotations

import logging
import re
from typing import Any, List, Mapping, Optional, Tuple

from agent_engine.config_sources import get_metric_context
from .schemas import Cluster, KeywordRecord
from .tools.content_index import get_existing_posts
from agent_engine.blog_keyword_analyzer.tools.normalization import (
    canonical_blog_platform_key,
    detect_file_formats_in_text,
    seo_platform_label,
)

logger = logging.getLogger(__name__)


def keyword_intent_key(text: str) -> str:
    s = " ".join((text or "").strip().split()).lower()
    s = re.sub(r"(?i)^(tutorial|guide|example|examples|code sample|sample)\s*:\s*", "", s)
    s = re.sub(r"(?i)\b(step-by-step|how to|using)\b", "", s)
    s = re.sub(r"[^a-z0-9.+#]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def clean_keyword_phrase(text: str) -> str:
    out = " ".join((text or "").strip().split())
    if not out:
        return ""
    out = re.sub(r"(?i)\busing\s+in\s+([a-z0-9.+#]+)\b", r"in \1", out)
    out = re.sub(r"(?i)\bwith\s+in\s+([a-z0-9.+#]+)\b", r"in \1", out)
    out = re.sub(r"(?i)\bvia\s+in\s+([a-z0-9.+#]+)\b", r"in \1", out)
    out = re.sub(r"(?i)\binsert\s+pages?\s+to\s+pdf\b", "insert pages into PDF", out)
    out = re.sub(r"(?i)\badd\s+pages?\s+in\s+pdf\b", "add pages to PDF", out)
    out = re.sub(r"(?i)\badd\s+pages?\s+into\s+pdf\b", "add pages to PDF", out)
    out = re.sub(r"(?i)\bremove\s+pages?\s+from\s+pdf\b", "remove pages from PDF", out)
    out = re.sub(r"(?i)\bextract\s+ranges?\s+of\s+pages?\s+from\s+pdf\b", "extract page ranges from PDF", out)
    out = re.sub(r"(?i)\bstep\s*[- ]\s*by\s*[- ]\s*step\b", "Step-by-Step", out)
    return re.sub(r"\s{2,}", " ", out).strip(" -,:;")


def _seed_anchor_tokens(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "api", "best", "by", "file", "files", "for", "from", "guide",
        "how", "in", "into", "of", "on", "or", "the", "to", "tutorial", "using", "with",
    }
    return {
        token for token in re.findall(r"[a-z0-9.+#]+", (text or "").lower())
        if len(token) > 1 and token not in stopwords
    }


def _seed_format_tokens(text: str) -> set[str]:
    return {fmt.lower() for fmt in detect_file_formats_in_text(text)}


def _off_scope_seed_modifier(text: str, seed_topic: str) -> bool:
    seed_lower = (seed_topic or "").lower()
    text_lower = (text or "").lower()
    strict_modifiers = {"searchable", "ocr"}
    return any(mod in text_lower and mod not in seed_lower for mod in strict_modifiers)


def _platform_phrase(platform: Optional[str]) -> str:
    return seo_platform_label(platform)


def focus_records_for_seed_topic(
    records: List[KeywordRecord],
    *,
    seed_topic: Optional[str],
    platform: Optional[str],
    locale: str,
) -> List[KeywordRecord]:
    if not seed_topic:
        return records

    seed_clean = clean_keyword_phrase(seed_topic)
    anchors = _seed_anchor_tokens(seed_clean)
    if not anchors:
        return records

    required_overlap = 2 if len(anchors) >= 3 else 1
    seed_formats = _seed_format_tokens(seed_clean)
    focused: List[KeywordRecord] = []
    for record in records:
        text = clean_keyword_phrase(record.keyword)
        tokens = set(re.findall(r"[a-z0-9.+#]+", text.lower()))
        if len(tokens.intersection(anchors)) < required_overlap:
            continue
        record_formats = _seed_format_tokens(text)
        # For conversion-style seeds with explicit formats, keep candidates on the same
        # format pair. This prevents "HTML to PDF" from leaking into "DOCX to PDF" runs.
        if len(seed_formats) >= 2 and not seed_formats.issubset(record_formats):
            continue
        if _off_scope_seed_modifier(text, seed_clean):
            continue
        focused.append(KeywordRecord(**{**record.model_dump(), "keyword": text}))

    if len(focused) >= 3:
        return focused

    label = _platform_phrase(platform)
    synthetic_keywords = [seed_clean]
    if label and label.lower() not in seed_clean.lower():
        synthetic_keywords.extend([
            f"{seed_clean} in {label}",
            f"How to {seed_clean} in {label}",
            f"{seed_clean} using {label}",
        ])
    else:
        synthetic_keywords.extend([
            f"How to {seed_clean}",
            f"{seed_clean} tutorial",
        ])

    synthetic_records = [
        KeywordRecord(
            keyword=kw,
            source="llm",
            locale=locale,
            volume=None,
            cpc=None,
            kd=None,
            clicks=None,
            url=None,
            competition=None,
            competition_label=None,
        )
        for kw in synthetic_keywords
    ]

    merged: List[KeywordRecord] = []
    seen = set()
    for record in focused + synthetic_records:
        key = keyword_intent_key(record.keyword)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(record)
    return merged


def normalize_topic_key(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def brand_slug(brand: str) -> str:
    return normalize_topic_key(brand or "unknown")


def _canonical_platform(platform: Optional[str]) -> Optional[str]:
    return canonical_blog_platform_key(platform)


def _derive_product_code(product: str) -> str:
    p = (product or "").strip().lower()
    if not p:
        return ""
    tokens = re.split(r"[.\s/\\_-]+", p)
    tokens = [t for t in tokens if t]
    if not tokens:
        return p
    return tokens[-1]


def load_existing_topics_for_prompt(
    product: str,
    platform: Optional[str],
    use_content_index: bool = True,
) -> List[dict]:
    if not use_content_index:
        logger.info(
            "Content index lookup disabled (use_content_index=False); skipping existing topic search."
        )
        return []

    product_code = _derive_product_code(product)
    fw_canonical = _canonical_platform(platform)

    logger.info(
        "Loading existing topics for product=%r -> product_code=%r, platform=%r -> fw_canonical=%r",
        product,
        product_code,
        platform,
        fw_canonical,
    )

    try:
        entries = get_existing_posts(product=product_code, platform=fw_canonical)
    except Exception as e:
        logger.warning("Failed to search existing blogs: %s", e, exc_info=True)
        return []

    topics_for_prompt: List[dict] = []
    for entry in entries:
        if hasattr(entry, "dict"):
            data: Mapping[str, Any] = entry.dict()
        elif isinstance(entry, Mapping):
            data = entry
        else:
            data = getattr(entry, "__dict__", {})

        topics_for_prompt.append(
            {
                "title": (data.get("title") or "").strip(),
                "url": data.get("url"),
                "slug": data.get("slug"),
                "platforms": data.get("platforms"),
            }
        )

    return topics_for_prompt


def _build_existing_keys(existing_topics: List[dict]) -> set[str]:
    keys: set[str] = set()
    for topic in existing_topics:
        for field in ("url", "title", "slug"):
            value = topic.get(field)
            if value:
                keys.add(normalize_topic_key(str(value)))
                break
    return keys


def filter_duplicate_topics(topics: list[Any], existing_topics: List[dict]) -> list[Any]:
    existing_keys = _build_existing_keys(existing_topics)
    if not existing_keys:
        return topics

    filtered = []
    for topic in topics:
        title = getattr(topic, "title", "") or ""
        if normalize_topic_key(title) in existing_keys:
            continue
        filtered.append(topic)
    return filtered


def build_retry_existing_topics(
    rejected_topics: list[Any],
    existing_topics: List[dict],
) -> List[dict]:
    """
    Given topics that were all filtered out as duplicates, return an
    existing_topics list augmented with those rejected titles, so a retry
    generation call can be told explicitly which titles to avoid repeating.
    """
    rejected_titles = [getattr(t, "title", "") or "" for t in rejected_topics]
    rejected_titles = [title for title in rejected_titles if title]
    return list(existing_topics) + [{"title": title} for title in rejected_titles]


def resolve_metric_context(brand: str) -> Tuple[str, str]:
    website, section = get_metric_context(brand)

    if not website or not section:
        raise ValueError(
            f"Invalid brand config for '{brand}': website/section cannot be empty."
        )

    return website, section


def summarize_cluster_scores(clusters: List[Cluster]) -> dict:
    scores = [cluster.metrics.score for cluster in clusters if cluster.metrics is not None]
    if not scores:
        return {"count": 0, "min": None, "max": None, "avg": None}
    return {
        "count": len(scores),
        "min": min(scores),
        "max": max(scores),
        "avg": sum(scores) / len(scores),
    }
