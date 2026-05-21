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

_TRAILING_CONNECTOR_RE = re.compile(r"(?i)\s+(?:or|and|with|using|for|in)\s*$")


@dataclass(frozen=True)
class TopicAcceptanceResult:
    title: str
    primary_keyword: str
    accepted: bool
    notes: list[str] = field(default_factory=list)


def _clean(value: str) -> str:
    text = re.sub(r"\s{2,}", " ", (value or "").strip()).strip(" -,:;")
    return _fix_acronyms(text)


def _fix_acronyms(value: str) -> str:
    text = value or ""
    text = re.sub(r"(?i)\b2d\b", "2D", text)
    text = re.sub(r"(?i)\b3d\b", "3D", text)
    text = re.sub(r"(?i)\bgis\b", "GIS", text)
    return text


def _clean_step_by_step_phrase(value: str) -> tuple[str, list[str]]:
    text = value or ""
    notes: list[str] = []
    before = text
    text = text.replace("\u2013", " - ").replace("\u2014", " - ")
    text = re.sub(r"(?i)\bstep\s*[- ]\s*by\s*[- ]\s*step\b", "Step-by-Step", text)
    text = re.sub(r"(?i)^\s*Step-by-Step\s+Guide\s*:\s*", "", text).strip()
    text = re.sub(r"(?i)\s*[-:]\s*Step-by-Step\s+Guide\s*$", "", text).strip()
    text = re.sub(r"(?i)\s+Step-by-Step\s+Guide\s*$", "", text).strip()
    text = _clean(text)
    if text != _clean(before):
        notes.append("Normalized Step-by-Step guide phrasing.")
    return text, notes


def _clean_malformed_action_phrase(value: str) -> tuple[str, list[str]]:
    text = value or ""
    notes: list[str] = []
    before = text
    action_verbs = (
        "add",
        "build",
        "create",
        "delete",
        "draw",
        "edit",
        "extract",
        "generate",
        "insert",
        "merge",
        "modify",
        "remove",
        "render",
        "replace",
        "split",
        "update",
    )
    action_pattern = "|".join(action_verbs)
    text = re.sub(
        rf"(?i)^\s*how\s+to\s+convert\s+({action_pattern})\b",
        lambda m: f"How to {m.group(1)}",
        text,
    )
    text = re.sub(
        rf"(?i)^\s*convert\s+({action_pattern})\b",
        lambda m: m.group(1).capitalize(),
        text,
    )
    text = _clean(text)
    if text != _clean(before):
        notes.append("Removed malformed Convert prefix from action phrase.")
    return text, notes


def _clean_malformed_topic_phrase(value: str, platform: Optional[str] = None) -> tuple[str, list[str]]:
    notes: list[str] = []
    text = _clean(value)
    if not text:
        return "", notes

    text, step_notes = _clean_step_by_step_phrase(text)
    notes.extend(step_notes)
    text, action_notes = _clean_malformed_action_phrase(text)
    notes.extend(action_notes)

    platform_label = _platform_label(platform)
    if platform_label:
        before = text
        platform_pattern = re.escape(platform_label)
        text = re.sub(
            rf"(?i)\s+(?:or|and)\s+(?:using|with|for|in)\s+{platform_pattern}\s*$",
            f" in {platform_label}",
            text,
        )
        text = re.sub(
            rf"(?i)\s+(?:using|with|for)\s+{platform_pattern}\s*$",
            f" in {platform_label}",
            text,
        )
        if text != before:
            notes.append("Rewrote malformed platform connector phrasing.")

    before = text
    while True:
        cleaned = _TRAILING_CONNECTOR_RE.sub("", text).strip()
        if cleaned == text:
            break
        text = cleaned
    if text != before:
        notes.append("Removed trailing connector from topic phrase.")

    return _clean(text), notes


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
    cleaned, _ = _clean_malformed_topic_phrase(primary_keyword, platform)
    return _fix_acronyms(refiner.refine(cleaned))


def finalize_topic_acceptance(
    *,
    title: str,
    primary_keyword: str,
    platform: Optional[str] = None,
) -> TopicAcceptanceResult:
    notes: list[str] = []
    optimized_primary = optimize_primary_keyword(primary_keyword, platform)
    cleaned_title, cleanup_notes = _clean_malformed_topic_phrase(title, platform)
    optimized_title = _direct_conversion_phrase(cleaned_title, platform) or cleaned_title
    notes.extend(cleanup_notes)

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
        title=_fix_acronyms(refiner.refine(title_for_checks)),
        primary_keyword=optimized_primary,
        accepted=accepted,
        notes=notes,
    )
