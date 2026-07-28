from __future__ import annotations

from ..models.code_verification import CodeVerificationResult
from ..models.extraction import EligibleTopic
from ..models.fact_pack import FactPack
from ..models.keyword_analysis import KeywordAnalysisResult
from ..models.platform import PlatformContext
from .fetcher import FetchedPage

_INTRO_OUTLINE = [
    "Introduction",
    "Why this feature matters",
    "Brief introduction of the API (install + product/docs links)",
]
_CLOSING_OUTLINE = [
    "Get a Free License",
    "Free Additional Resources",
    "Conclusion",
    "FAQs",
    "See Also (only if related post URLs are supplied)",
]
_DEFAULT_TUTORIAL_STEP = "Step-by-step tutorial with a code example"


def build_fact_pack(
    page: FetchedPage,
    topic: EligibleTopic,
    code_verification: CodeVerificationResult,
    sdk_version: str,
    platform: PlatformContext,
    keyword_analysis: KeywordAnalysisResult | None = None,
) -> FactPack:
    """Assembles the fact pack (instructions.md step 4) from already-extracted,
    already-verified data. Deliberately has no LLM call: everything here is a
    direct copy or restructuring of fields the extractor, code verifier, and
    (optionally) the external keyword analyzer already produced, so no new
    claims can be introduced at this stage.

    When `keyword_analysis` is supplied, its SEO-refined title replaces the
    raw extracted title and its outline replaces the generic tutorial
    placeholder in `suggested_article_outline` — the writer then follows
    that outline instead of inventing its own section breakdown.
    """
    facts_confirmed = [f"Heading: {topic.heading}", topic.feature_summary]
    facts_confirmed.extend(f"API used: {api}" for api in topic.apis_used)

    warnings = []
    if code_verification.source_verified:
        warnings.append(
            "Code sample has not been executed in a sandbox, but it was matched verbatim "
            "against the product team's own release notes page; note it as reproduced "
            "from the official release notes and untested, not as unverified."
        )
    else:
        warnings.append(
            "Code sample could not be matched verbatim to the product team's release notes "
            "page and has not been executed; mark it as unverified in the article."
        )

    topic_title = keyword_analysis.title if keyword_analysis and keyword_analysis.title else topic.suggested_title
    tutorial_outline = keyword_analysis.outline if keyword_analysis and keyword_analysis.outline else [_DEFAULT_TUTORIAL_STEP]
    outline = [*_INTRO_OUTLINE, *tutorial_outline, *_CLOSING_OUTLINE]

    return FactPack(
        topic=topic_title,
        primary_source_url=page.url,
        source_title=page.title,
        sdk_version=sdk_version,
        main_problem_solved=topic.feature_summary,
        platform=platform,
        keyword_analysis=keyword_analysis,
        key_steps=[],
        code_snippets=[topic.code_sample],
        limitations=[],
        warnings=warnings,
        related_concepts=topic.classes_used + topic.methods_used,
        facts_confirmed_from_source=facts_confirmed,
        facts_needing_verification=list(topic.unsupported_or_missing_details),
        suggested_article_outline=outline,
        code_verification=code_verification,
    )
