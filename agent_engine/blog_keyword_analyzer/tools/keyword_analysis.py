from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable, Optional

from agent_engine.blog_keyword_analyzer.schemas import (
    KeywordAnalysis,
    KeywordClusterGroup,
    KeywordInsight,
    TopicProfile,
)
from agent_engine.blog_keyword_analyzer.tools.normalization import (
    canonical_platform_label,
    normalize_platform_mentions,
)

_STOPWORDS = {
    "a", "an", "and", "api", "best", "by", "example", "examples", "for", "from", "guide",
    "how", "in", "into", "of", "on", "or", "the", "to", "tutorial", "using", "with",
}
_QUESTION_STARTERS = ("what", "why", "how", "when", "where", "which", "can", "does", "is", "are", "should")
_COMMERCIAL_MARKERS = {"best", "top", "review", "reviews", "comparison", "compare", "vs", "alternative", "alternatives", "tools", "software", "pricing"}
_TRANSACTIONAL_MARKERS = {"buy", "hire", "demo", "trial", "pricing", "coupon", "download", "template", "service", "agency", "consultant"}
_NAV_MARKERS = {"login", "dashboard", "official", "support", "app", "account", "docs", "documentation"}
_LONG_TAIL_MARKERS = {"example", "examples", "tutorial", "guide", "workflow", "automation", "strategy", "template", "checklist"}
_SEMANTIC_MARKERS = {"automation", "workflow", "integration", "processing", "conversion", "editing", "rendering", "export", "import", "format", "file"}
_SECONDARY_MARKERS = {"strategy", "campaign", "campaigns", "automation", "tools", "software", "benefits", "examples", "retention", "segmentation"}
_ENTITY_MARKERS = {
    "shopify", "woocommerce", "mailchimp", "hubspot", "klaviyo", "omnisend", "magento",
    "google analytics", "meta ads", "crm", "cdp", "salesforce", "wordpress",
    "excel", "word", "powerpoint", "pdf", "docx", "xlsx", "pptx", "csv", "json", "xml",
}


def _clean_text(value: str) -> str:
    text = normalize_platform_mentions((value or "").strip(), None)
    text = re.sub(r"\s+", " ", text).strip(" -,:;")
    return text


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9.+#]+", (value or "").lower())


def _meaningful_tokens(value: str) -> list[str]:
    return [token for token in _tokenize(value) if len(token) > 1 and token not in _STOPWORDS]


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    bag_seen: set[tuple[str, ...]] = set()
    for value in values:
        cleaned = _clean_text(value)
        if not cleaned:
            continue
        key = re.sub(r"[^a-z0-9.+#]+", " ", cleaned.lower()).strip()
        bag = tuple(sorted(_meaningful_tokens(cleaned)))
        if not key or key in seen or (bag and bag in bag_seen):
            continue
        seen.add(key)
        if bag:
            bag_seen.add(bag)
        out.append(cleaned)
    return out


def _classify_intent(keyword: str) -> str:
    lower = keyword.lower()
    if any(marker in lower for marker in _TRANSACTIONAL_MARKERS):
        return "transactional"
    if any(marker in lower for marker in _COMMERCIAL_MARKERS):
        return "commercial"
    if any(marker in lower for marker in _NAV_MARKERS):
        return "navigational"
    if "near me" in lower:
        return "local"
    return "informational"


def _funnel_stage(intent: str) -> str:
    if intent in {"transactional", "local"}:
        return "decision"
    if intent == "commercial":
        return "consideration"
    if intent == "navigational":
        return "retention"
    return "awareness"


def _is_question(keyword: str) -> bool:
    lower = keyword.lower().strip()
    return lower.startswith(_QUESTION_STARTERS) or lower.endswith("?")


def _is_entity(keyword: str) -> bool:
    lower = keyword.lower()
    if lower in _ENTITY_MARKERS:
        return True
    if "." in keyword and any(part for part in keyword.split(".") if part):
        return True
    return False


def _is_long_tail(keyword: str) -> bool:
    lower = keyword.lower()
    return len(keyword.split()) >= 4 or _is_question(keyword) or any(marker in lower for marker in _LONG_TAIL_MARKERS)


def _specificity(keyword: str) -> str:
    wc = len(keyword.split())
    if wc >= 5 or _is_question(keyword):
        return "specific"
    if wc <= 2:
        return "broad"
    return "mid"


def _placement(keyword_type: str, intent: str) -> list[str]:
    placements = {
        "primary": ["SEO title", "H1", "URL", "intro", "conclusion"],
        "secondary": ["H2", "body"],
        "long_tail": ["H2", "H3", "FAQ", "snippet answer"],
        "semantic": ["body", "examples", "tables"],
        "question": ["FAQ", "AEO section"],
        "entity": ["comparison section", "tools section", "examples"],
        "intent_based": ["body"],
        "aio_aeo": ["FAQ", "snippet answer", "comparison table"],
    }
    base = list(placements.get(keyword_type, ["body"]))
    if intent == "commercial":
        base.append("comparison table")
    if intent == "transactional":
        base.append("CTA section")
    return _dedupe_preserve_order(base)


def _topic_profile(topic: str, platform: Optional[str]) -> TopicProfile:
    raw = _clean_text(topic)
    normalized = raw.lower()
    platform_label = canonical_platform_label(platform)

    modifiers: list[str] = []
    industry_context: list[str] = []
    audience: list[str] = []
    implied_intent: list[str] = []

    if " for " in normalized:
        tail = normalized.split(" for ", 1)[1].strip()
        if tail:
            industry_context.append(tail)
            audience.append(tail)
            modifiers.append(f"for {tail}")
    if " vs " in normalized:
        modifiers.append("comparison")
        implied_intent.append("compare options")
    if any(token in normalized for token in ("how to", "guide", "tutorial")):
        implied_intent.append("learn")
    if any(token in normalized for token in ("best", "top", "pricing", "tools", "software")):
        implied_intent.append("choose tools")
    if any(token in normalized for token in ("increase", "improve", "optimize", "conversion")):
        implied_intent.append("improve results")
    if platform_label:
        modifiers.append(platform_label)
        audience.append(f"{platform_label} developers")

    core_topic = normalized
    if " for " in normalized:
        core_topic = normalized.split(" for ", 1)[0].strip()
    core_topic = re.sub(r"(?i)^(how to|guide to|tutorial for)\s+", "", core_topic).strip()

    search_type = [_classify_intent(raw)]
    if search_type[0] == "commercial":
        search_type.append("informational")

    return TopicProfile(
        original_topic=raw,
        normalized_topic=normalized,
        core_topic=core_topic,
        modifiers=_dedupe_preserve_order(modifiers),
        industry_context=_dedupe_preserve_order(industry_context),
        audience=_dedupe_preserve_order(audience),
        implied_intent=_dedupe_preserve_order(implied_intent or ["learn"]),
        search_type=_dedupe_preserve_order(search_type),
    )


def _relevance_score(keyword: str, topic: str) -> float:
    topic_tokens = set(_meaningful_tokens(topic))
    keyword_tokens = set(_meaningful_tokens(keyword))
    if not topic_tokens or not keyword_tokens:
        return 0.0
    overlap = len(topic_tokens.intersection(keyword_tokens))
    return min(10.0, (overlap / max(1, len(topic_tokens))) * 10.0)


def _intent_clarity_score(keyword: str) -> float:
    lower = keyword.lower()
    if _is_question(keyword):
        return 9.0
    if any(marker in lower for marker in _COMMERCIAL_MARKERS | _TRANSACTIONAL_MARKERS | _NAV_MARKERS):
        return 8.5
    return 6.5


def _specificity_score(keyword: str) -> float:
    wc = len(keyword.split())
    if wc >= 6:
        return 9.0
    if wc >= 4:
        return 8.0
    if wc == 3:
        return 6.5
    return 4.5


def _usefulness_score(keyword: str) -> float:
    lower = keyword.lower()
    if _is_question(keyword):
        return 9.0
    if any(marker in lower for marker in _LONG_TAIL_MARKERS | _COMMERCIAL_MARKERS):
        return 8.5
    if any(marker in lower for marker in _SEMANTIC_MARKERS):
        return 7.0
    return 6.0


def _conversion_score(intent: str) -> float:
    return {
        "transactional": 9.0,
        "commercial": 8.0,
        "navigational": 6.5,
        "local": 8.5,
        "informational": 5.5,
    }.get(intent, 5.5)


def _aeo_score(keyword: str) -> float:
    lower = keyword.lower()
    if _is_question(keyword):
        return 9.5
    if any(marker in lower for marker in ("how to", "what is", "best", "vs", "pricing", "example", "template")):
        return 8.5
    if len(keyword.split()) >= 4:
        return 7.5
    return 5.0


def _keyword_score(keyword: str, topic: str, intent: str) -> tuple[float, float]:
    relevance = _relevance_score(keyword, topic)
    intent_clarity = _intent_clarity_score(keyword)
    specificity = _specificity_score(keyword)
    usefulness = _usefulness_score(keyword)
    conversion = _conversion_score(intent)
    aeo = _aeo_score(keyword)
    score = (
        (relevance * 0.30)
        + (intent_clarity * 0.20)
        + (specificity * 0.15)
        + (usefulness * 0.15)
        + (conversion * 0.10)
        + (aeo * 0.10)
    )
    return round(score, 2), round(aeo, 2)


def _choose_primary_keyword(topic: str, candidates: list[str], preferred_primary: Optional[str]) -> str:
    if preferred_primary:
        return _clean_text(preferred_primary)

    if not candidates:
        return _clean_text(topic)

    broad_candidates = [
        candidate for candidate in candidates
        if not _is_question(candidate)
        and not candidate.lower().startswith("how to ")
        and not any(marker in candidate.lower() for marker in _COMMERCIAL_MARKERS | _TRANSACTIONAL_MARKERS)
        and 2 <= len(candidate.split()) <= 4
    ]
    if broad_candidates:
        candidates = broad_candidates

    scored = []
    for candidate in candidates:
        intent = _classify_intent(candidate)
        score, _ = _keyword_score(candidate, topic, intent)
        lower = candidate.lower()
        broadness_bonus = 1.0 if 2 <= len(candidate.split()) <= 4 else 0.0
        question_penalty = -2.0 if _is_question(candidate) or lower.startswith("how to ") else 0.0
        commercial_penalty = -0.75 if any(marker in lower for marker in _COMMERCIAL_MARKERS | _TRANSACTIONAL_MARKERS) else 0.0
        exactish_bonus = 1.25 if topic and (candidate == topic or candidate in topic or topic in candidate) else 0.0
        scored.append(
            (
                score + broadness_bonus + question_penalty + commercial_penalty + exactish_bonus,
                _relevance_score(candidate, topic),
                -abs(len(candidate.split()) - len(topic.split() or [topic])),
                candidate,
            )
        )
    scored.sort(reverse=True)
    return scored[0][3]


def _cluster_bucket(keyword: str) -> str:
    lower = keyword.lower()
    if _is_question(keyword):
        return "Questions"
    if any(marker in lower for marker in ("strategy", "best practice", "plan", "checklist")):
        return "Strategy"
    if any(marker in lower for marker in ("automation", "workflow", "sequence", "flow")):
        return "Automation"
    if any(marker in lower for marker in ("tool", "software", "platform", "pricing", "vs", "compare")):
        return "Tools"
    if any(marker in lower for marker in ("example", "template")):
        return "Examples"
    if any(marker in lower for marker in ("what is", "meaning", "benefits", "basics")):
        return "Basics"
    return "Core"


def _question_variants(topic: str, primary_keyword: str) -> list[str]:
    base = _clean_text(primary_keyword or topic)
    if not base:
        return []
    variants = [
        f"What is {base}?",
        f"How to use {base}?",
        f"Why is {base} important?",
        f"What are the best ways to implement {base}?",
    ]
    return _dedupe_preserve_order(variants)


def _semantic_terms(topic: str, candidates: list[str], platform: Optional[str]) -> list[str]:
    items: list[str] = []
    for candidate in candidates:
        lower = candidate.lower()
        if any(marker in lower for marker in _SEMANTIC_MARKERS) or len(candidate.split()) <= 3:
            items.append(candidate)
    profile = _topic_profile(topic, platform)
    if profile.core_topic:
        items.extend(
            [
                f"{profile.core_topic} workflow",
                f"{profile.core_topic} automation",
                f"{profile.core_topic} integration",
            ]
        )
    return _dedupe_preserve_order(items)


def analyze_keywords(
    *,
    topic: str,
    candidate_keywords: Iterable[str],
    product: str = "",
    platform: Optional[str] = None,
    preferred_primary: Optional[str] = None,
) -> KeywordAnalysis:
    del product  # reserved for future refinement rules

    topic_clean = _clean_text(topic)
    platform_label = canonical_platform_label(platform)
    candidates = _dedupe_preserve_order(candidate_keywords)

    rejected: list[str] = []
    accepted: list[str] = []
    for candidate in candidates:
        lower = candidate.lower()
        tokens = _meaningful_tokens(candidate)
        if not tokens:
            rejected.append(candidate)
            continue
        if len(tokens) == 1 and tokens[0] not in {"pdf", "docx", "xlsx", "pptx"}:
            if not _is_entity(candidate):
                rejected.append(candidate)
                continue
        if topic_clean and not set(tokens).intersection(_meaningful_tokens(topic_clean)) and not _is_question(candidate):
            if not _is_entity(candidate) and not any(entity in lower for entity in _ENTITY_MARKERS):
                rejected.append(candidate)
                continue
        accepted.append(candidate)

    primary_text = _choose_primary_keyword(topic_clean, accepted, preferred_primary)
    primary_intent = _classify_intent(primary_text)
    primary_score, primary_aeo = _keyword_score(primary_text, topic_clean, primary_intent)
    primary_keyword = KeywordInsight(
        keyword=primary_text,
        keyword_type="primary",
        intent=primary_intent,
        funnel_stage=_funnel_stage(primary_intent),
        specificity=_specificity(primary_text),
        placement=_placement("primary", primary_intent),
        score=primary_score,
        aeo_score=primary_aeo,
    )

    inventory: list[KeywordInsight] = []
    secondary: list[KeywordInsight] = []
    long_tail: list[KeywordInsight] = []
    intent_based: list[KeywordInsight] = []
    aio_aeo: list[KeywordInsight] = []
    questions: list[str] = []
    entities: list[str] = []

    for keyword in _dedupe_preserve_order([primary_text] + accepted):
        if keyword == primary_text:
            inventory.append(primary_keyword)
            continue

        intent = _classify_intent(keyword)
        score, aeo_score = _keyword_score(keyword, topic_clean, intent)
        keyword_type = "secondary"
        if _is_question(keyword):
            keyword_type = "question"
            questions.append(keyword if keyword.endswith("?") else f"{keyword}?")
        elif _is_entity(keyword):
            keyword_type = "entity"
            entities.append(keyword)
        elif any(marker in keyword.lower() for marker in _SECONDARY_MARKERS):
            keyword_type = "secondary"
        elif _is_long_tail(keyword):
            keyword_type = "long_tail"
        elif len(keyword.split()) <= 3:
            keyword_type = "semantic"

        insight = KeywordInsight(
            keyword=keyword,
            keyword_type=keyword_type,  # type: ignore[arg-type]
            intent=intent,  # type: ignore[arg-type]
            funnel_stage=_funnel_stage(intent),  # type: ignore[arg-type]
            specificity=_specificity(keyword),  # type: ignore[arg-type]
            placement=_placement(keyword_type, intent),
            score=score,
            aeo_score=aeo_score,
        )
        inventory.append(insight)

        if keyword_type == "secondary" and len(secondary) < 15:
            secondary.append(insight)
        if (keyword_type == "long_tail" or _is_long_tail(keyword)) and len(long_tail) < 25:
            long_tail.append(insight)
        if intent in {"commercial", "transactional", "navigational", "local"} and len(intent_based) < 15:
            intent_based.append(
                insight.model_copy(update={"keyword_type": "intent_based"})
            )
        if aeo_score >= 8.0 and len(aio_aeo) < 15:
            aio_aeo.append(
                insight.model_copy(update={"keyword_type": "aio_aeo", "placement": _placement("aio_aeo", intent)})
            )

    if not questions:
        questions = _question_variants(topic_clean, primary_text)
    if not entities:
        entities = _dedupe_preserve_order(
            [entity for entity in accepted if _is_entity(entity)] + ([platform_label] if platform_label else [])
        )

    semantic = _dedupe_preserve_order(
        [item.keyword for item in inventory if item.keyword_type == "semantic"] + _semantic_terms(topic_clean, accepted, platform)
    )[:40]

    cluster_map: dict[str, list[str]] = defaultdict(list)
    for item in inventory:
        cluster_map[_cluster_bucket(item.keyword)].append(item.keyword)
    keyword_clusters = [
        KeywordClusterGroup(cluster_name=name, keywords=_dedupe_preserve_order(values)[:10])
        for name, values in cluster_map.items()
        if values
    ]

    return KeywordAnalysis(
        topic=topic_clean,
        topic_profile=_topic_profile(topic_clean, platform),
        primary_keyword=primary_keyword,
        secondary_keywords=secondary[:15],
        long_tail_keywords=long_tail[:25],
        semantic_keywords=semantic,
        question_keywords=questions[:15],
        entities=entities[:20],
        intent_based_keywords=intent_based[:15],
        aio_aeo_keywords=aio_aeo[:15],
        keyword_clusters=keyword_clusters[:8],
        rejected_keywords=_dedupe_preserve_order(rejected),
        keyword_inventory=inventory,
    )
