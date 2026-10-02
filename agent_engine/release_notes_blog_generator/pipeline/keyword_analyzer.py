from __future__ import annotations

import logging
from typing import Protocol

from ..config import Settings
from ..models.keyword_analysis import KeywordAnalysisResult, KeywordGroups
from ..models.platform import PlatformContext
from . import mcp_client
from .mcp_client import McpToolError

logger = logging.getLogger(__name__)

# Use blog-keyword-analyzer agent via MCP wrapper. Falls back to keywords_auto if not available.
_KEYWORDS_SERVER = "blog-keyword-analyzer/server.py"
_KEYWORDS_SERVER_FALLBACK = "keywords_auto/server.py"


class TitledTopic(Protocol):
    """The only thing the keyword server needs from a topic. Satisfied by
    `models.extraction.EligibleTopic` (one release-notes feature) and by
    `models.docs_extraction.DocsArticleExtraction` (a whole docs article),
    so the same MCP call serves both use cases.
    """

    suggested_title: str


def analyze_topic(topic: TitledTopic, platform: PlatformContext, settings: Settings) -> KeywordAnalysisResult | None:
    """Calls the blog-keyword-analyzer MCP server (mcp-servers/blog-keyword-analyzer)
    over stdio for SEO keyword groups. Falls back to keywords_auto if blog-keyword-analyzer
    is unavailable.

    This is best-effort enrichment, not a pipeline requirement: any failure
    (server disabled, unreachable, timeout, empty response) returns None and
    is logged as a warning, so the writer falls back to generating its own
    title/tags exactly as before.
    """
    if not settings.keyword_analyzer_enabled:
        logger.debug("Keyword analyzer disabled (keyword_analyzer_enabled=False)")
        return None

    product = platform.product_full_name or platform.brand_name or platform.product_display
    logger.info(
        "Keyword analyzer input: topic=%r product=%r platform=%r",
        topic.suggested_title, product, platform.platform_key,
    )

    # Try blog-keyword-analyzer first, fall back to keywords_auto if it fails
    response = _call_keyword_analyzer(
        topic.suggested_title,
        product,
        platform.platform_key or "",
        settings,
    )

    if response is None:
        return None

    if not isinstance(response, dict) or response.get("status") == "error":
        logger.warning(
            "Keyword analyzer skipped: %s",
            response.get("error") if isinstance(response, dict) else f"malformed response: {response!r}",
        )
        return None

    result = _to_keyword_analysis_result(response.get("keywords") or {})
    if not (result.keyword_groups.core_seo_keywords or result.keyword_groups.context_keywords or result.keyword_groups.long_tail_keywords):
        logger.warning("Keyword analyzer skipped: no keywords returned")
        return None

    logger.info(
        "Keyword analyzer finished: %d primary, %d secondary, %d long-tail keyword(s)",
        len(result.keyword_groups.core_seo_keywords),
        len(result.keyword_groups.context_keywords),
        len(result.keyword_groups.long_tail_keywords),
    )
    return result


def _call_keyword_analyzer(
    topic: str,
    product: str,
    platform: str,
    settings: Settings,
) -> dict | None:
    """Try blog-keyword-analyzer first, fall back to keywords_auto if it fails."""
    try:
        # Try the primary blog-keyword-analyzer server
        logger.debug("Trying blog-keyword-analyzer MCP server")
        return mcp_client.call_tool(
            _KEYWORDS_SERVER,
            "fetch_keywords",
            {
                "topic": topic,
                "product_name": product,
                "platform": platform,
                "brand": "Aspose",
            },
            settings,
        )
    except (McpToolError, OSError, TimeoutError) as exc:
        logger.warning("blog-keyword-analyzer unavailable: %s; trying fallback keywords_auto", exc)

        # Fall back to keywords_auto if blog-keyword-analyzer fails
        try:
            return mcp_client.call_tool(
                _KEYWORDS_SERVER_FALLBACK,
                "fetch_keywords",
                {
                    "topic": topic,
                    "product_name": product,
                    "platform": platform,
                },
                settings,
                extra_env={"PROFESSIONALIZE_API_KEY_2": settings.professionalize_api_key}
                if settings.professionalize_api_key
                else None,
            )
        except (McpToolError, OSError, TimeoutError) as exc2:
            logger.warning("Both keyword analyzers failed: %s", exc2)
            return None


def _to_keyword_analysis_result(keywords: dict) -> KeywordAnalysisResult:
    primary = [kw for kw in (keywords.get("primary") or []) if kw]
    secondary = [kw for kw in (keywords.get("secondary") or []) if kw]
    long_tail = [kw for kw in (keywords.get("long_tail") or []) if kw]

    # title/outline/target_persona/editorial_notes stay at their model
    # defaults ("" / []): the keywords_auto MCP server only returns keyword
    # groups today, not a full TopicIdea (title/outline/persona). writer.py
    # and fact_checker.py already fall back to the writer's own title/outline
    # when these are empty, and writer_agent.md documents this explicitly —
    # if keywords_auto is ever extended to return them, they'll flow through
    # here with no other changes needed.
    return KeywordAnalysisResult(
        title="",
        primary_keyword=primary[0] if primary else "",
        supporting_keywords=[*primary[1:], *secondary, *long_tail],
        keyword_groups=KeywordGroups(
            core_seo_keywords=primary,
            long_tail_keywords=long_tail,
            context_keywords=secondary,
        ),
    )
