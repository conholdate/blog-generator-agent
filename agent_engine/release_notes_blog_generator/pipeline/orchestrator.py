from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .. import metrics_api
from ..config import Settings
from ..llm.base import LLMClient
from ..models.article import BlogPost
from ..models.code_verification import CodeVerificationResult
from ..models.fact_pack import FactPack
from ..models.keyword_analysis import KeywordAnalysisResult
from ..models.platform import PlatformContext
from ..models.security import EngineeringSignals
from . import banner_generator, code_verifier, docs_extractor, fact_checker, fetcher, keyword_analyzer, quality_gate, related_posts, security_gate, seo_editor, writer
from .extractor import extract_topics
from .platform import detect_platform, fallback_platform

logger = logging.getLogger(__name__)

# CLI-facing names for the two use cases (see cli.py --source-type).
SOURCE_TYPE_RELEASE_NOTES = "release-notes"
SOURCE_TYPE_DOCS = "docs"
SOURCE_TYPES = (SOURCE_TYPE_RELEASE_NOTES, SOURCE_TYPE_DOCS)


@dataclass
class TopicResult:
    heading: str
    blog_post: BlogPost | None
    seo_issues: list[str] = field(default_factory=list)
    cover_image_path: Path | None = None


@dataclass
class PipelineResult:
    source_url: str
    publication_readiness: str  # "blocked" | "insufficient_code_samples" | "draft_ready"
    blocker_reason: str | None
    remediation_report: str | None = None
    topics: list[TopicResult] = field(default_factory=list)
    rejected_sections: list[str] = field(default_factory=list)
    source_type: str = SOURCE_TYPE_RELEASE_NOTES


@dataclass
class _PlannedPost:
    """One blog post the run is going to write, with the two source-specific
    steps (code verification and fact-pack assembly) already bound to the data
    they need.

    Both use cases converge here: release notes plan one `_PlannedPost` per
    code-backed section, a docs article plans exactly one covering the whole
    page. Everything after this point — keyword analysis, writing, Read More,
    banner, SEO, quality, metrics, export — is shared and unaware of which
    kind of URL started the run.
    """

    heading: str
    keyword_topic: object  # anything exposing `suggested_title` (keyword_analyzer.TitledTopic)
    language: str
    verify: Callable[[], CodeVerificationResult]
    build_fact_pack: Callable[[CodeVerificationResult, PlatformContext, KeywordAnalysisResult | None], FactPack]
    writer_prompt: Path | None = None


def run(
    url: str,
    llm: LLMClient,
    settings: Settings,
    engineering_signals: EngineeringSignals | None = None,
    source_type: str = SOURCE_TYPE_RELEASE_NOTES,
) -> PipelineResult:
    """Runs the full URL -> blog draft pipeline described in instructions.md,
    gated by the security check from Engineering-signals.md.

    `source_type` picks the use case:
    - "release-notes" (default): the original flow — a release-notes URL fans
      out to one draft per code-backed feature section.
    - "docs": a documentation-article URL fans in to a single, longer draft
      covering every topic on that page.

    Only the extraction/verification/fact-pack stages differ between the two;
    the rest of the pipeline is identical, so the default argument keeps every
    existing caller on exactly the previous behaviour.

    `engineering_signals` defaults to "nothing detected" since this pipeline
    reads a public URL, not a repository; callers that also scan a source repo
    can pass real signals in to enforce the same gate.
    """
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Unknown source_type {source_type!r}; expected one of {', '.join(SOURCE_TYPES)}")

    run_started = time.perf_counter()
    run_id = str(uuid.uuid4())
    run_calls_before, run_tokens_before = llm.api_calls, llm.total_tokens
    logger.info("Starting %s pipeline run for %s", source_type, url)

    gate = security_gate.assess(engineering_signals or EngineeringSignals())
    if not gate.safe_to_generate_blog:
        logger.error("Security gate blocked this run: %s", gate.blocker_reason)
        return PipelineResult(
            source_url=url,
            publication_readiness=gate.publication_readiness,
            blocker_reason=gate.blocker_reason,
            remediation_report=security_gate.build_remediation_report(gate),
            source_type=source_type,
        )
    logger.info("Security gate: clear")

    logger.info("Fetching and cleaning %s", url)
    page = fetcher.fetch_and_clean(url, settings)
    logger.info("Fetched %r (%d sections, %d with code samples)", page.title, len(page.sections), sum(1 for s in page.sections if s.code_blocks))

    page_platform = detect_platform(page.url, page.title)
    if page_platform:
        logger.info("Detected platform from URL: %s (%s)", page_platform.platform_name, page_platform.language)
    else:
        logger.info("Could not detect platform from URL; will fall back to each topic's code-sample language")

    if source_type == SOURCE_TYPE_DOCS:
        planned_posts, rejected_sections = _plan_docs_article(page, llm)
    else:
        planned_posts, rejected_sections = _plan_release_notes(page, llm)

    topic_results: list[TopicResult] = []
    run_platform_ctx: PlatformContext | None = None
    items_succeeded = 0
    items_failed = 0
    total = len(planned_posts)
    for index, planned in enumerate(planned_posts, start=1):
        topic_started = time.perf_counter()
        logger.info("[%d/%d] Processing topic: %r", index, total, planned.heading)

        try:
            verification = planned.verify()
            logger.debug(
                "[%d/%d] Code verification: source_verified=%s, syntax_valid=%s",
                index, total, verification.source_verified, verification.syntax_valid,
            )

            platform = page_platform or fallback_platform(planned.language)
            if run_platform_ctx is None:
                run_platform_ctx = platform
            if not page_platform:
                logger.info("[%d/%d] Using fallback platform from code sample: %s", index, total, platform.language)

            logger.info("[%d/%d] Running keyword analysis (this can take a couple of minutes)...", index, total)
            keywords = keyword_analyzer.analyze_topic(planned.keyword_topic, platform, settings)
            if keywords:
                logger.info("[%d/%d] Keyword analysis done: title=%r, primary_keyword=%r", index, total, keywords.title, keywords.primary_keyword)
            else:
                logger.info("[%d/%d] Keyword analysis unavailable; writer will generate its own title/tags", index, total)

            fact_pack = planned.build_fact_pack(verification, platform, keywords)

            logger.info("[%d/%d] Writing article...", index, total)
            blog_post = writer.write_article(fact_pack, llm, settings, prompt_path=planned.writer_prompt)
            logger.info("[%d/%d] Article written: slug=%s, %d word(s)", index, total, blog_post.slug, len(blog_post.body_markdown.split()))

            related = related_posts.find_related_posts(blog_post, settings)
            blog_post.body_markdown = related_posts.append_read_more_section(blog_post.body_markdown, related)
            logger.info("[%d/%d] Read More: %d related post(s) linked", index, total, len(related))

            logger.info("[%d/%d] Generating cover image...", index, total)
            cover_image_path = banner_generator.generate_cover_image(blog_post, settings)
            if cover_image_path:
                logger.info("[%d/%d] Cover image generated: %s", index, total, cover_image_path)
            else:
                logger.info("[%d/%d] Cover image unavailable; export will leave the images/ placeholder empty", index, total)

            seo_issues = seo_editor.review(blog_post, cover_image_generated=cover_image_path is not None)
            logger.info("[%d/%d] SEO review: %d issue(s) found", index, total, len(seo_issues))
            for issue in seo_issues:
                logger.debug("[%d/%d] SEO issue: %s", index, total, issue)

            blog_post.quality = quality_gate.assess(blog_post, seo_issues)
            logger.info("[%d/%d] Quality assessment: publication_status=%s", index, total, blog_post.quality.publication_status.value)

            topic_results.append(TopicResult(heading=planned.heading, blog_post=blog_post, seo_issues=seo_issues, cover_image_path=cover_image_path))
            items_succeeded += 1
            logger.info("[%d/%d] Done in %.1fs", index, total, time.perf_counter() - topic_started)
        except Exception:
            logger.exception("[%d/%d] Failed to process topic %r", index, total, planned.heading)
            if run_platform_ctx is None:
                run_platform_ctx = page_platform or fallback_platform(planned.language)
            items_failed += 1

    run_platform = page_platform or run_platform_ctx
    metrics_deliveries = metrics_api.send_run_metrics(
        run_id=run_id,
        platform=run_platform.platform_name if run_platform else "",
        product=f"Aspose.{run_platform.product_display}" if run_platform and run_platform.product_display else "",
        items_discovered=total,
        items_succeeded=items_succeeded,
        items_failed=items_failed,
        duration_seconds=time.perf_counter() - run_started,
        api_calls_count=llm.api_calls - run_calls_before,
        token_usage=llm.total_tokens - run_tokens_before,
        log=logger.info,
    )
    sent = any(d.get("sent") for d in metrics_deliveries)
    reasons = sorted({d["reason"] for d in metrics_deliveries if d.get("reason")})
    logger.info(
        "Metrics summary: %s%s",
        "sent" if sent else "not sent",
        f" (reasons: {', '.join(reasons)})" if reasons else "",
    )

    logger.info("Pipeline run complete in %.1fs: %d draft(s) generated", time.perf_counter() - run_started, len(topic_results))

    return PipelineResult(
        source_url=page.url,
        publication_readiness="draft_ready" if topic_results else "insufficient_code_samples",
        blocker_reason=None,
        topics=topic_results,
        rejected_sections=rejected_sections,
        source_type=source_type,
    )


def _plan_release_notes(page: fetcher.FetchedPage, llm: LLMClient) -> tuple[list[_PlannedPost], list[str]]:
    """Release-notes use case: one planned post per code-backed section."""
    logger.info("Extracting eligible topics (code-sample-first filter)")
    extraction = extract_topics(page, llm)
    logger.info(
        "Extraction complete: %d eligible topic(s), %d section(s) rejected",
        len(extraction.eligible_topics),
        len(extraction.rejected_sections),
    )
    # At INFO when nothing survived: a run that generates no drafts still exits
    # 0, so the rejection reasons are the only thing in the CI log explaining
    # why. Kept at DEBUG otherwise to avoid drowning out the per-topic progress.
    rejection_log = logger.debug if extraction.eligible_topics else logger.info
    for section in extraction.rejected_sections:
        rejection_log("Rejected %r: %s", section.heading, section.reason_for_rejection)

    planned = [
        _PlannedPost(
            heading=topic.heading,
            keyword_topic=topic,
            language=topic.language,
            verify=lambda topic=topic: code_verifier.verify(topic, page.sections),
            build_fact_pack=lambda verification, platform, keywords, topic=topic: fact_checker.build_fact_pack(
                page,
                topic,
                verification,
                sdk_version=extraction.release_title,
                platform=platform,
                keyword_analysis=keywords,
            ),
        )
        for topic in extraction.eligible_topics
    ]
    return planned, [section.heading for section in extraction.rejected_sections]


def _plan_docs_article(page: fetcher.FetchedPage, llm: LLMClient) -> tuple[list[_PlannedPost], list[str]]:
    """Docs-article use case: the whole page becomes one planned post covering
    every topic it documents."""
    logger.info("Extracting documentation topics (whole-article, code-backed)")
    extraction = docs_extractor.extract_docs_article(page, llm)
    if extraction is None:
        logger.info("No code-backed documentation topics found on %s", page.url)
        return [], []

    code_topics = extraction.code_backed_topics
    logger.info(
        "Extraction complete: %d topic(s) to cover (%d with code samples), %d section(s) skipped",
        len(extraction.topics),
        len(code_topics),
        len(extraction.skipped_sections),
    )
    for topic in extraction.topics:
        logger.debug("Covering %r (%s)", topic.heading, "code sample" if topic.code_sample.strip() else "explanation only")
    for section in extraction.skipped_sections:
        logger.debug("Skipped %r: %s", section.heading, section.reason_for_skipping)

    language = extraction.primary_language or next((topic.language for topic in code_topics if topic.language), "")
    planned = _PlannedPost(
        heading=extraction.article_title,
        keyword_topic=extraction,
        language=language,
        verify=lambda: code_verifier.verify_all(list(code_topics), page.sections),
        build_fact_pack=lambda verification, platform, keywords: fact_checker.build_docs_fact_pack(
            page,
            extraction,
            verification,
            platform=platform,
            keyword_analysis=keywords,
        ),
        writer_prompt=writer.DOCS_PROMPT_PATH,
    )
    return [planned], [section.heading for section in extraction.skipped_sections]
