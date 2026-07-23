from __future__ import annotations

import logging

from ..config import Settings
from ..models.extraction import EligibleTopic
from ..models.keyword_analysis import KeywordAnalysisResult, KeywordGroups
from ..models.platform import PlatformContext
from . import mcp_client
from .mcp_client import McpToolError

logger = logging.getLogger(__name__)

_KEYWORDS_SERVER = "keywords_auto/server.py"


def analyze_topic(topic: EligibleTopic, platform: PlatformContext, settings: Settings) -> KeywordAnalysisResult | None:
    """Calls the keywords_auto MCP server (mcp-servers/keywords_auto) over
    stdio for SEO keyword groups — the same MCP-over-stdio convention
    agent_engine/blog_generator uses for its own fetch_keywords_auto() call
    (see pipeline/mcp_client.py).

    This is best-effort enrichment, not a pipeline requirement: any failure
    (server disabled, unreachable, timeout, empty response) returns None and
    is logged as a warning, so the writer falls back to generating its own
    title/tags exactly as before.
    """
    if not settings.keyword_analyzer_enabled:
        logger.debug("Keyword analyzer disabled (keyword_analyzer_enabled=False)")
        return None

    product = f"Aspose.{platform.product_display}" if platform.product_display else "Aspose"
    logger.info(
        "Keyword analyzer input: topic=%r product=%r platform=%r",
        topic.suggested_title, product, platform.platform_key,
    )

    try:
        response = mcp_client.call_tool(
            _KEYWORDS_SERVER,
            "fetch_keywords",
            {
                "topic": topic.suggested_title,
                "product_name": product,
                "platform": platform.platform_key or "",
            },
            settings,
            # keywords_auto's own config.py reads PROFESSIONALIZE_API_KEY_2, which
            # isn't set in its .env (only _1 is) — pass our key through as a
            # process env var, which pydantic-settings prefers over its .env file,
            # rather than editing that repo's .env.
            extra_env={"PROFESSIONALIZE_API_KEY_2": settings.professionalize_api_key}
            if settings.professionalize_api_key
            else None,
        )
    except (McpToolError, OSError, TimeoutError) as exc:
        logger.warning("Keyword analyzer skipped: %s", exc)
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
