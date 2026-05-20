from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from agent_engine.blog_keyword_analyzer.tools.normalization import (
    KeywordRefiner,
    canonical_platform_label,
    contains_platform_variant,
)


refiner = KeywordRefiner()


_WEAK_TITLE_MARKERS = (
    "conversion script",
    "converter script",
    "create a script",
    "build a script",
    "write a script",
)


@dataclass(frozen=True)
class TopicAcceptanceResult:
    title: str
    primary_keyword: str
    accepted: bool
    notes: list[str] = field(default_factory=list)


def _clean(value: str) -> str:
    return re.sub(r"\s{2,}", " ", (value or "").strip()).strip(" -,:;")


def _canonical_format(value: str) -> str:
    text = _clean(value)
    if not text:
        return ""
    lower = text.lower()
    known = {
        "png": "PNG",
        "jpg": "JPG",
        "jpeg": "JPEG",
        "pdf": "PDF",
        "doc": "DOC",
        "docx": "DOCX",
        "xls": "XLS",
        "xlsx": "XLSX",
        "ppt": "PPT",
        "pptx": "PPTX",
        "svg": "SVG",
        "html": "HTML",
        "shp": "SHP",
    }
    if lower in known:
        return known[lower]
    return refiner.refine(text)


def _platform_label(platform: Optional[str], fallback: str = "") -> str:
    return canonical_platform_label(platform) or refiner.refine(fallback)


def _direct_conversion_phrase(value: str, platform: Optional[str]) -> Optional[str]:
    text = _clean(value)
    if not text:
        return None

    patterns = [
        re.compile(
            r"(?i)^(?:how\s+to\s+)?(?:create|build|write|generate)\s+(?:a|an)?\s*"
            r"(?P<src>.+?)\s+to\s+(?P<dst>[a-z0-9.+#]+)\s+conversion\s+"
            r"(?:script|tool|program|utility)(?:\s+(?:in|with|using)\s+(?P<platform>[a-z0-9.+# ]+))?$"
        ),
        re.compile(
            r"(?i)^(?:how\s+to\s+)?(?:create|build|write|generate)\s+(?:a|an)?\s*"
            r"(?:script|tool|program|utility)\s+(?:to|for)\s+convert\s+"
            r"(?P<src>.+?)\s+to\s+(?P<dst>[a-z0-9.+#]+)(?:\s+(?:in|with|using)\s+(?P<platform>[a-z0-9.+# ]+))?$"
        ),
    ]

    for pattern in patterns:
        match = pattern.match(text)
        if not match:
            continue
        src = _canonical_format(match.group("src"))
        dst = _canonical_format(match.group("dst"))
        detected_platform = _platform_label(platform, match.groupdict().get("platform") or "")
        if not src or not dst:
            return None
        phrase = f"Convert {src} to {dst}"
        if detected_platform:
            phrase = f"{phrase} in {detected_platform}"
        return phrase
    return None


def optimize_primary_keyword(primary_keyword: str, platform: Optional[str] = None) -> str:
    """Rewrite weak implementation-wrapper phrasing into direct search-intent phrasing."""
    direct = _direct_conversion_phrase(primary_keyword, platform)
    if direct:
        return direct
    return refiner.refine(_clean(primary_keyword))


def finalize_topic_acceptance(
    *,
    title: str,
    primary_keyword: str,
    platform: Optional[str] = None,
) -> TopicAcceptanceResult:
    notes: list[str] = []
    optimized_primary = optimize_primary_keyword(primary_keyword, platform)
    optimized_title = _direct_conversion_phrase(title, platform) or _clean(title)

    if optimized_primary != _clean(primary_keyword):
        notes.append("Rewrote primary keyword to direct task/search-intent phrasing.")
    if optimized_title != _clean(title):
        notes.append("Rewrote title to remove script/tool wrapper phrasing.")

    title_for_checks = optimized_title or optimized_primary
    lower_title = title_for_checks.lower()
    if any(marker in lower_title for marker in _WEAK_TITLE_MARKERS):
        notes.append("Title still contains weak implementation-wrapper phrasing.")
    if platform and not contains_platform_variant(title_for_checks, platform):
        notes.append("Title does not mention the selected platform.")
    if optimized_primary and optimized_primary.lower() not in title_for_checks.lower():
        notes.append("Title does not include the finalized primary keyword.")

    accepted = not any("still contains" in note or "does not" in note for note in notes)
    return TopicAcceptanceResult(
        title=refiner.refine(title_for_checks),
        primary_keyword=optimized_primary,
        accepted=accepted,
        notes=notes,
    )
