from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .. import metrics_api
from ..config import Settings
from ..llm.base import LLMClient
from ..models.article import BlogPost
from ..models.platform import PlatformContext
from ..models.security import EngineeringSignals
from . import banner_generator, code_verifier, fact_checker, fetcher, keyword_analyzer, quality_gate, related_posts, security_gate, seo_editor, writer
from .extractor import extract_topics
from .platform import detect_platform, fallback_platform

logger = logging.getLogger(__name__)


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


def run(
    url: str,
    llm: LLMClient,
    settings: Settings,
    engineering_signals: EngineeringSignals | None = None,
) -> PipelineResult:
    """Runs the full URL -> blog draft pipeline described in instructions.md,
    gated by the security check from Engineering-signals.md.

    `engineering_signals` defaults to "nothing detected" since this pipeline
    reads a public release-notes URL, not a repository; callers that also
    scan a source repo can pass real signals in to enforce the same gate.
    """
    run_started = time.perf_counter()
    run_id = str(uuid.uuid4())
    run_calls_before, run_tokens_before = llm.api_calls, llm.total_tokens
    logger.info("Starting pipeline run for %s", url)

    gate = security_gate.assess(engineering_signals or EngineeringSignals())
    if not gate.safe_to_generate_blog:
        logger.error("Security gate blocked this run: %s", gate.blocker_reason)
        return PipelineResult(
            source_url=url,
            publication_readiness=gate.publication_readiness,
            blocker_reason=gate.blocker_reason,
            remediation_report=security_gate.build_remediation_report(gate),
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

    logger.info("Extracting eligible topics (code-sample-first filter)")
    extraction = extract_topics(page, llm)
    logger.info(
        "Extraction complete: %d eligible topic(s), %d section(s) rejected",
        len(extraction.eligible_topics),
        len(extraction.rejected_sections),
    )
    for section in extraction.rejected_sections:
        logger.debug("Rejected %r: %s", section.heading, section.reason_for_rejection)

    topic_results: list[TopicResult] = []
    run_platform_ctx: PlatformContext | None = None
    items_succeeded = 0
    items_failed = 0
    total = len(extraction.eligible_topics)
    for index, topic in enumerate(extraction.eligible_topics, start=1):
        topic_started = time.perf_counter()
        logger.info("[%d/%d] Processing topic: %r", index, total, topic.heading)

        try:
            verification = code_verifier.verify(topic, page.sections)
            logger.debug(
                "[%d/%d] Code verification: source_verified=%s, syntax_valid=%s",
                index, total, verification.source_verified, verification.syntax_valid,
            )

            platform = page_platform or fallback_platform(topic.language)
            if run_platform_ctx is None:
                run_platform_ctx = platform
            if not page_platform:
                logger.info("[%d/%d] Using fallback platform from code sample: %s", index, total, platform.language)

            logger.info("[%d/%d] Running keyword analysis (this can take a couple of minutes)...", index, total)
            keywords = keyword_analyzer.analyze_topic(topic, platform, settings)
            if keywords:
                logger.info("[%d/%d] Keyword analysis done: title=%r, primary_keyword=%r", index, total, keywords.title, keywords.primary_keyword)
            else:
                logger.info("[%d/%d] Keyword analysis unavailable; writer will generate its own title/tags", index, total)

            fact_pack = fact_checker.build_fact_pack(
                page,
                topic,
                verification,
                sdk_version=extraction.release_title,
                platform=platform,
                keyword_analysis=keywords,
            )

            logger.info("[%d/%d] Writing article...", index, total)
            blog_post = writer.write_article(fact_pack, llm, settings)
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

            topic_results.append(TopicResult(heading=topic.heading, blog_post=blog_post, seo_issues=seo_issues, cover_image_path=cover_image_path))
            items_succeeded += 1
            logger.info("[%d/%d] Done in %.1fs", index, total, time.perf_counter() - topic_started)
        except Exception:
            logger.exception("[%d/%d] Failed to process topic %r", index, total, topic.heading)
            if run_platform_ctx is None:
                run_platform_ctx = page_platform or fallback_platform(topic.language)
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
        rejected_sections=[section.heading for section in extraction.rejected_sections],
    )
