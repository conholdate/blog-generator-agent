from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from agent_engine.blog_keyword_analyzer.tools.normalization import (
    canonical_blog_platform_key,
    canonical_platform_label,
    detect_file_formats_in_text,
    detect_platform_families_in_text,
    file_format_to_display,
    normalize_product_short_name,
)
from agent_engine.blog_keyword_analyzer.tools.taxonomy import (
    page_target,
    resolve_product_taxonomy,
)


_ACTION_ALIASES: dict[str, tuple[str, ...]] = {
    "convert": ("convert", "conversion", "export", "save as", "to pdf", "to word"),
    "create": ("create", "generate", "make", "build"),
    "edit": ("edit", "update", "modify", "replace"),
    "merge": ("merge", "combine", "join"),
    "split": ("split", "separate", "divide"),
    "extract": ("extract", "read", "parse", "get text", "get images"),
    "protect": ("protect", "password", "encrypt", "secure"),
    "sign": ("sign", "signature", "digitally sign"),
    "compress": ("compress", "reduce size", "optimize"),
    "render": ("render", "preview", "image"),
    "compare": ("compare", "diff"),
    "import": ("import",),
    "write": ("write",),
}

_COMMERCIAL = re.compile(r"\b(best|top|compare|comparison|alternative|alternatives|vs\.?|review)\b", re.I)
_QUESTION = re.compile(r"\b(how to|tutorial|guide|example|examples|code sample|sample)\b", re.I)
_NAV = re.compile(r"\b(docs?|documentation|reference|login|account|support)\b", re.I)
_TRANSACTIONAL = re.compile(r"\b(api|sdk|library|component|buy|price|pricing|trial|download|license)\b", re.I)
_GENERIC_LOW_VALUE = re.compile(r"\b(what is|meaning|definition|examples of|file format examples)\b", re.I)


@dataclass(frozen=True)
class KeywordClassification:
    keyword: str
    formats: list[str] = field(default_factory=list)
    action: Optional[str] = None
    language: Optional[str] = None
    product_family: Optional[str] = None
    strategic_cluster: Optional[str] = None
    intent: str = "informational"
    funnel_stage: str = "awareness"
    best_page_type: str = "blog_tutorial"
    recommended_action: str = "new_blog_tutorial"
    internal_link_target: Optional[str] = None
    conversion_cta: Optional[str] = None
    is_generic_low_value: bool = False
    has_api_modifier: bool = False
    has_commercial_modifier: bool = False
    rationale: list[str] = field(default_factory=list)


def detect_action(text: str, allowed_actions: list[str]) -> Optional[str]:
    lower = (text or "").lower()
    allowed = {a.lower() for a in allowed_actions}
    if "convert" in allowed and (
        re.search(r"(?i)\b\w+\s+to\s+\w+\b", lower)
        or re.search(r"(?i)\b\w+\s+from\s+\w+\b", lower)
        or re.search(r"(?i)\b(export|transformation|generate\s+\w+\s+from)\b", lower)
    ):
        return "convert"
    for action, aliases in _ACTION_ALIASES.items():
        if allowed and action not in allowed:
            continue
        for alias in aliases:
            if re.search(rf"(?i)(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", lower):
                return action
    return None


def _detect_language(text: str, selected_platform: Optional[str]) -> Optional[str]:
    if selected_platform:
        label = canonical_platform_label(selected_platform)
        if label:
            return label
    families = detect_platform_families_in_text(text)
    if not families:
        return None
    return canonical_platform_label(families[0]) or families[0]


def _intent(text: str, *, brand: str, product: str) -> tuple[str, str]:
    lower = (text or "").lower()
    product_short = normalize_product_short_name(product).lower()
    brand_lower = (brand or "").lower()
    branded = bool(brand_lower and brand_lower in lower) or bool(product_short and product_short.lower() in lower)

    if branded and _NAV.search(lower):
        return "navigational", "retention"
    if _COMMERCIAL.search(lower):
        return "commercial", "consideration"
    if _TRANSACTIONAL.search(lower):
        return "transactional", "decision"
    if _QUESTION.search(lower):
        return "informational", "awareness"
    return "informational", "awareness"


def classify_keyword(
    keyword: str,
    *,
    product: str,
    brand: str = "Aspose",
    platform: Optional[str] = None,
) -> KeywordClassification:
    text = " ".join((keyword or "").strip().split())
    taxonomy = resolve_product_taxonomy(product, brand)
    allowed_actions = [str(a).lower() for a in taxonomy.get("actions") or []]
    raw_formats = detect_file_formats_in_text(text)
    formats = [file_format_to_display(fmt) for fmt in raw_formats]
    action = detect_action(text, allowed_actions)
    language = _detect_language(text, platform)
    intent, funnel = _intent(text, brand=brand, product=product)

    has_api_modifier = bool(_TRANSACTIONAL.search(text))
    has_commercial_modifier = bool(_COMMERCIAL.search(text))
    is_generic_low_value = bool(_GENERIC_LOW_VALUE.search(text))
    strategic_cluster = str(taxonomy.get("strategic_cluster") or "")
    product_family = str(taxonomy.get("product") or product)
    internal_link_target = page_target(product, platform, brand=brand, target_type="money_pages") or None
    docs_target = page_target(product, platform, brand=brand, target_type="docs_pages") or None

    rationale: list[str] = []
    best_page_type = "blog_tutorial"
    recommended_action = "new_blog_tutorial"
    conversion_cta = "Link to product page, docs, and trial/download"

    if is_generic_low_value and not action:
        best_page_type = "informational_glossary"
        recommended_action = "reject"
        conversion_cta = None
        rationale.append("Generic informational query with weak developer-task intent.")
    elif intent == "navigational":
        best_page_type = "docs_page" if docs_target else "navigation_page"
        recommended_action = "docs_page"
        internal_link_target = docs_target or internal_link_target
        conversion_cta = "Improve navigation to docs or product page"
        rationale.append("Brand/navigation intent is better served by docs or product navigation.")
    elif has_commercial_modifier:
        best_page_type = "comparison_post"
        recommended_action = "commercial_comparison_post"
        rationale.append("Commercial investigation query is suitable for comparison content.")
    elif has_api_modifier and not _QUESTION.search(text):
        best_page_type = "product_page"
        recommended_action = "product_page"
        rationale.append("API/SDK query has product or landing-page intent.")
    elif action and (language or platform):
        best_page_type = "blog_tutorial"
        recommended_action = "new_blog_tutorial"
        rationale.append("Developer task plus platform is suitable for a tutorial post.")
    elif action and formats:
        best_page_type = "blog_tutorial"
        recommended_action = "new_blog_tutorial"
        rationale.append("Format/action keyword can support a practical tutorial.")
    else:
        best_page_type = "monitor"
        recommended_action = "monitor"
        rationale.append("Keyword needs more specific task, format, or platform signals.")

    if formats:
        rationale.append("Detected file format intent: " + ", ".join(formats[:3]) + ".")
    if action:
        rationale.append(f"Detected action intent: {action}.")
    if language:
        rationale.append(f"Detected platform/language intent: {language}.")

    return KeywordClassification(
        keyword=text,
        formats=formats,
        action=action,
        language=language,
        product_family=product_family,
        strategic_cluster=strategic_cluster,
        intent=intent,
        funnel_stage=funnel,
        best_page_type=best_page_type,
        recommended_action=recommended_action,
        internal_link_target=internal_link_target,
        conversion_cta=conversion_cta,
        is_generic_low_value=is_generic_low_value,
        has_api_modifier=has_api_modifier,
        has_commercial_modifier=has_commercial_modifier,
        rationale=rationale,
    )


def blog_platform_key(value: Optional[str]) -> str:
    return canonical_blog_platform_key(value or "") or ""
