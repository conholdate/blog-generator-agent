from __future__ import annotations

import re
from typing import Iterable, Optional

from agent_engine.blog_keyword_analyzer.schemas import KeywordOpportunity, KeywordRecord
from agent_engine.blog_keyword_analyzer.tools.keyword_classifier import KeywordClassification, classify_keyword
from agent_engine.blog_keyword_analyzer.tools.taxonomy import resolve_product_taxonomy


_BLOG_ACTIONS = {"new_blog_tutorial", "commercial_comparison_post", "refresh_existing_blog"}
_STOP = {
    "a",
    "an",
    "and",
    "api",
    "best",
    "by",
    "file",
    "files",
    "for",
    "from",
    "guide",
    "how",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "tutorial",
    "using",
    "with",
}


def keyword_intent_key(text: str) -> str:
    tokens = [
        token
        for token in re.findall(r"[a-z0-9.+#]+", (text or "").lower())
        if len(token) > 1 and token not in _STOP
    ]
    # conversion variants become closer without losing the important source/dest formats.
    tokens = ["convert" if token in {"conversion", "converting"} else token for token in tokens]
    return " ".join(dict.fromkeys(tokens))


def _existing_intent_keys(existing_topics: Iterable[dict]) -> set[str]:
    keys: set[str] = set()
    for topic in existing_topics or []:
        for field in ("title", "slug", "url"):
            value = topic.get(field) if isinstance(topic, dict) else None
            if value:
                key = keyword_intent_key(str(value))
                if key:
                    keys.add(key)
    return keys


def _duplicate_penalty(keyword: str, existing_topics: Iterable[dict]) -> tuple[int, str]:
    key = keyword_intent_key(keyword)
    if not key:
        return 0, "safe_to_generate"
    key_tokens = set(key.split())
    for existing_key in _existing_intent_keys(existing_topics):
        if not existing_key:
            continue
        if key == existing_key:
            return 5, "possible_duplicate"
        existing_tokens = set(existing_key.split())
        if key_tokens and len(key_tokens.intersection(existing_tokens)) >= max(3, len(key_tokens) - 1):
            return 3, "possible_refresh"
    return 0, "safe_to_generate"


def _business_fit_score(classification: KeywordClassification, product: str, brand: str) -> int:
    taxonomy = resolve_product_taxonomy(product, brand)
    supported_formats = {str(f).lower() for f in taxonomy.get("formats") or []}
    supported_actions = {str(a).lower() for a in taxonomy.get("actions") or []}
    format_hit = any(fmt.lower() in supported_formats for fmt in classification.formats)
    action_hit = bool(classification.action and classification.action.lower() in supported_actions)
    if format_hit and action_hit:
        return 5
    if action_hit or format_hit:
        return 4
    if classification.has_api_modifier:
        return 3
    return 2


def _developer_intent_score(classification: KeywordClassification) -> int:
    if classification.action and classification.language:
        return 5
    if classification.action and classification.formats:
        return 4
    if classification.has_api_modifier:
        return 4
    if classification.formats:
        return 3
    return 1


def _conversion_score(classification: KeywordClassification) -> int:
    if classification.intent == "transactional":
        return 5
    if classification.intent == "commercial":
        return 5
    if classification.action and classification.language:
        return 4
    if classification.action:
        return 3
    return 1


def _specificity_score(keyword: str) -> int:
    wc = len((keyword or "").split())
    if wc >= 5:
        return 5
    if wc == 4:
        return 4
    if wc == 3:
        return 3
    if wc == 2:
        return 2
    return 1


def _blog_suitability_score(classification: KeywordClassification) -> int:
    if classification.recommended_action in {"new_blog_tutorial", "commercial_comparison_post"}:
        return 5
    if classification.recommended_action == "refresh_existing_blog":
        return 4
    if classification.recommended_action == "monitor":
        return 2
    return 1


def _genericness_penalty(classification: KeywordClassification, keyword: str) -> int:
    lower = (keyword or "").lower()
    if classification.is_generic_low_value:
        return 4
    wc = len((keyword or "").split())
    if wc <= 2 and not classification.has_api_modifier:
        return 3
    if not classification.action and not classification.has_commercial_modifier:
        return 2
    if re.search(
        r"(?i)\b(batch|streaming|performance|settings|multithreaded|high fidelity|"
        r"preserve|tables|hyperlinks|images|secure)\b",
        lower,
    ):
        return 2
    return 0


def _priority_label(score: float, recommended_action: str) -> str:
    if recommended_action == "reject" or score < 8:
        return "Reject"
    if score >= 25:
        return "Very High"
    if score >= 20:
        return "High"
    if score >= 14:
        return "Medium"
    return "Low"


def score_keyword_record(
    record: KeywordRecord,
    *,
    product: str,
    brand: str,
    platform: Optional[str],
    existing_topics: Iterable[dict] = (),
) -> KeywordOpportunity:
    classification = classify_keyword(
        record.keyword,
        product=product,
        brand=brand,
        platform=platform,
    )
    duplicate_penalty, duplicate_status = _duplicate_penalty(record.keyword, existing_topics)
    recommended_action = classification.recommended_action
    if duplicate_status == "possible_refresh" and recommended_action in _BLOG_ACTIONS:
        recommended_action = "refresh_existing_blog"
    elif duplicate_status == "possible_duplicate" and recommended_action in _BLOG_ACTIONS:
        recommended_action = "possible_duplicate"

    business_fit = _business_fit_score(classification, product, brand)
    developer_intent = _developer_intent_score(classification)
    conversion = _conversion_score(classification)
    cluster_value = 5 if classification.strategic_cluster else 3
    specificity = _specificity_score(record.keyword)
    blog_suitability = _blog_suitability_score(
        KeywordClassification(**{**classification.__dict__, "recommended_action": recommended_action})
    )
    genericness = _genericness_penalty(classification, record.keyword)
    final_score = (
        business_fit
        + developer_intent
        + conversion
        + cluster_value
        + specificity
        + blog_suitability
        - genericness
        - duplicate_penalty
    )
    rationale = list(classification.rationale)
    if duplicate_penalty:
        rationale.append(f"Existing-content overlap detected: {duplicate_status}.")
    if business_fit >= 4:
        rationale.append("Strong product fit based on local taxonomy.")
    if recommended_action in _BLOG_ACTIONS:
        rationale.append("Eligible for blog topic generation.")
    elif recommended_action == "product_page":
        rationale.append("Better suited to a product or landing page than a blog tutorial.")

    return KeywordOpportunity(
        keyword=record.keyword,
        source=record.source,
        formats=classification.formats,
        action=classification.action,
        language=classification.language,
        product_family=classification.product_family,
        strategic_cluster=classification.strategic_cluster,
        intent=classification.intent,  # type: ignore[arg-type]
        funnel_stage=classification.funnel_stage,  # type: ignore[arg-type]
        best_page_type=classification.best_page_type,
        recommended_action=recommended_action,
        internal_link_target=classification.internal_link_target,
        conversion_cta=classification.conversion_cta,
        business_fit_score=business_fit,
        developer_intent_score=developer_intent,
        conversion_potential_score=conversion,
        cluster_value_score=cluster_value,
        specificity_score=specificity,
        blog_suitability_score=blog_suitability,
        genericness_penalty=genericness,
        duplicate_penalty=duplicate_penalty,
        final_priority_score=float(final_score),
        priority_label=_priority_label(final_score, recommended_action),  # type: ignore[arg-type]
        duplicate_status=duplicate_status,
        rationale=rationale,
    )


def build_keyword_opportunities(
    records: Iterable[KeywordRecord],
    *,
    product: str,
    brand: str,
    platform: Optional[str],
    existing_topics: Iterable[dict] = (),
) -> list[KeywordOpportunity]:
    opportunities = [
        score_keyword_record(
            record,
            product=product,
            brand=brand,
            platform=platform,
            existing_topics=existing_topics,
        )
        for record in records
    ]
    opportunities.sort(key=lambda item: item.final_priority_score, reverse=True)
    return opportunities


def is_blog_suitable(opportunity: KeywordOpportunity) -> bool:
    return opportunity.recommended_action in _BLOG_ACTIONS and opportunity.priority_label != "Reject"
