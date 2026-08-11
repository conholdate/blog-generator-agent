from __future__ import annotations

from ..models.code_verification import CodeVerificationResult
from ..models.docs_extraction import DocsArticleExtraction
from ..models.extraction import EligibleTopic
from ..models.fact_pack import SOURCE_TYPE_DOCS, FactPack
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

# A docs post covers a whole article rather than one release feature, so the
# fixed sections around the tutorial are worded for the set of tasks, not for
# "this feature", and it gains a comparison section the release-notes post has
# no use for (see prompts/docs_writer_agent.md).
_DOCS_INTRO_OUTLINE = [
    "Introduction",
    "Why these tasks matter",
    "Brief introduction of the API (install + product/docs links)",
    "Prerequisites (only if the documentation stated any)",
]
_DOCS_CLOSING_OUTLINE = [
    "Choosing the Right Approach (only if more than one code-backed topic was covered)",
    *_CLOSING_OUTLINE,
]


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


def build_docs_fact_pack(
    page: FetchedPage,
    extraction: DocsArticleExtraction,
    code_verification: CodeVerificationResult,
    platform: PlatformContext,
    keyword_analysis: KeywordAnalysisResult | None = None,
) -> FactPack:
    """Docs-article counterpart of `build_fact_pack`.

    Same contract — no LLM call, every field a copy or restructuring of what
    the docs extractor and code verifier already produced — but it collapses a
    whole documentation page into *one* fact pack instead of one per feature.
    The per-heading breakdown survives in `doc_topics`, and the article outline
    is built from those headings so the writer covers every topic the page
    covers rather than picking one.

    `keyword_analysis.outline`, when the analyzer supplies one, still wins: an
    SEO-researched section breakdown is a deliberate override, the same as on
    the release-notes path.
    """
    topics = extraction.topics
    code_topics = extraction.code_backed_topics

    facts_confirmed = [f"Documentation article: {extraction.article_title}", extraction.overview]
    for topic in topics:
        facts_confirmed.append(f"Section '{topic.heading}': {topic.summary}")
        facts_confirmed.extend(f"'{topic.heading}' fact: {point}" for point in topic.key_points)
        facts_confirmed.extend(f"'{topic.heading}' API used: {api}" for api in topic.apis_used)

    if not code_topics:
        warnings = ["No code sample was extracted from the documentation page; do not invent one."]
    elif code_verification.source_verified:
        warnings = [
            f"All {len(code_topics)} code sample(s) have not been executed in a sandbox, but each was "
            "matched verbatim against Aspose's own documentation page; note them as reproduced from "
            "the official documentation and untested, not as unverified."
        ]
    else:
        warnings = [
            "At least one code sample could not be matched verbatim to the documentation page and "
            "none have been executed; mark the samples as unverified in the article."
        ]

    topic_title = keyword_analysis.title if keyword_analysis and keyword_analysis.title else extraction.suggested_title
    # Every topic becomes a section, code-backed or not: the framing headings
    # ("Load a Document") are what make the post read as one tutorial rather
    # than a list of disconnected snippets.
    tutorial_outline = (
        keyword_analysis.outline
        if keyword_analysis and keyword_analysis.outline
        else [topic.heading for topic in topics] or [_DEFAULT_TUTORIAL_STEP]
    )
    outline = [*_DOCS_INTRO_OUTLINE, *tutorial_outline, *_DOCS_CLOSING_OUTLINE]

    related_concepts = []
    for topic in topics:
        related_concepts.extend(topic.classes_used)
        related_concepts.extend(topic.methods_used)

    return FactPack(
        topic=topic_title,
        primary_source_url=page.url,
        source_title=page.title,
        # Documentation pages are not versioned the way release notes are, so
        # there is no version to attribute the feature to; the docs writer
        # prompt is told to omit version claims when this is empty.
        sdk_version="",
        main_problem_solved=extraction.overview,
        platform=platform,
        source_type=SOURCE_TYPE_DOCS,
        keyword_analysis=keyword_analysis,
        key_steps=[topic.heading for topic in topics],
        code_snippets=[topic.code_sample for topic in code_topics],
        limitations=[],
        warnings=warnings,
        related_concepts=_dedupe(related_concepts),
        facts_confirmed_from_source=[fact for fact in facts_confirmed if fact.strip()],
        facts_needing_verification=list(extraction.unsupported_or_missing_details),
        suggested_article_outline=outline,
        code_verification=code_verification,
        prerequisites=list(extraction.prerequisites),
        doc_topics=topics,
    )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    return [value for value in values if not (value in seen or seen.add(value))]
