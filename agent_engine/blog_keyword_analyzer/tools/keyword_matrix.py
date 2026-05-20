from __future__ import annotations

import re
from typing import Optional

from agent_engine.blog_keyword_analyzer.schemas import KeywordRecord
from agent_engine.blog_keyword_analyzer.tools.normalization import canonical_platform_label
from agent_engine.blog_keyword_analyzer.tools.taxonomy import resolve_product_taxonomy


_FORMAT_CATEGORY = {
    "word": "Word",
    "doc": "DOC",
    "docx": "DOCX",
    "pdf": "PDF",
    "excel": "Excel",
    "xls": "XLS",
    "xlsx": "XLSX",
    "csv": "CSV",
    "powerpoint": "PowerPoint",
    "ppt": "PPT",
    "pptx": "PPTX",
    "html": "HTML",
    "image": "image",
    "png": "PNG",
    "jpg": "JPG",
}


def _display_format(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "", (value or "").lower())
    return _FORMAT_CATEGORY.get(key, value)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        cleaned = " ".join((value or "").strip().split())
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def _primary_category(product: str) -> str:
    short = product.lower()
    if "words" in short:
        return "Word"
    if "pdf" in short:
        return "PDF"
    if "cells" in short:
        return "Excel"
    if "slides" in short:
        return "PowerPoint"
    if "html" in short:
        return "HTML"
    return "document"


def generate_local_matrix_keywords(
    *,
    topic: Optional[str],
    product: str,
    brand: str = "Aspose",
    platform: Optional[str] = None,
    max_keywords: int = 40,
) -> list[str]:
    taxonomy = resolve_product_taxonomy(product, brand)
    platform_label = canonical_platform_label(platform) or ""
    category = _primary_category(product)
    formats = [_display_format(str(fmt)) for fmt in (taxonomy.get("formats") or [])]
    actions = [str(action).lower() for action in (taxonomy.get("actions") or [])]

    topic_clean = " ".join((topic or "").strip().split())
    candidates: list[str] = []
    if topic_clean:
        candidates.append(topic_clean)
        if platform_label and platform_label.lower() not in topic_clean.lower():
            candidates.append(f"{topic_clean} in {platform_label}")
            candidates.append(f"How to {topic_clean} in {platform_label}")
        if platform_label:
            candidates.append(f"{topic_clean} API for {platform_label}")
            candidates.append(f"{topic_clean} library for {platform_label}")

    if platform_label:
        candidates.extend(
            [
                f"{category} API for {platform_label}",
                f"{category} SDK for {platform_label}",
                f"best {category} API for {platform_label}",
            ]
        )
    candidates.extend(
        [
            f"{category} API",
            f"{category} SDK",
            f"best {category} API for developers",
        ]
    )

    # Keep the matrix deliberately compact. These are strategic anchors, not a full combinatorial dump.
    priority_formats = _dedupe(
        [fmt for fmt in formats if fmt.lower() in {"docx", "word", "pdf", "xlsx", "excel", "pptx", "powerpoint", "html"}]
        + formats[:4]
    )[:6]
    priority_actions = [a for a in actions if a in {"convert", "create", "merge", "split", "extract", "edit", "protect", "render"}][:6]

    for action in priority_actions:
        for fmt in priority_formats:
            if platform_label:
                if action == "convert" and fmt.upper() not in {"PDF"}:
                    candidates.append(f"convert {fmt} to PDF in {platform_label}")
                    candidates.append(f"how to convert {fmt} to PDF in {platform_label}")
                elif action == "merge":
                    candidates.append(f"merge {fmt} files in {platform_label}")
                elif action == "split":
                    candidates.append(f"split {fmt} files in {platform_label}")
                elif action == "extract":
                    candidates.append(f"extract text from {fmt} in {platform_label}")
                elif action == "create":
                    candidates.append(f"create {fmt} file in {platform_label}")
                elif action == "edit":
                    candidates.append(f"edit {fmt} file in {platform_label}")
                elif action == "protect":
                    candidates.append(f"password protect {fmt} in {platform_label}")
                elif action == "render":
                    candidates.append(f"render {fmt} as image in {platform_label}")
            else:
                candidates.append(f"{action} {fmt} files")

    return _dedupe(candidates)[:max_keywords]


def generate_local_matrix_records(
    *,
    topic: Optional[str],
    product: str,
    brand: str = "Aspose",
    platform: Optional[str] = None,
    locale: str = "en-US",
    max_keywords: int = 40,
) -> list[KeywordRecord]:
    return [
        KeywordRecord(
            keyword=keyword,
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
        for keyword in generate_local_matrix_keywords(
            topic=topic,
            product=product,
            brand=brand,
            platform=platform,
            max_keywords=max_keywords,
        )
    ]
