"""
Blog Keyword Analyzer MCP Server
Exposes the blog-keyword-analyzer agent as an MCP tool for integration with other agents.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

# Setup logging (stderr only to keep stdout clean for JSON-RPC)
logging.basicConfig(
    level=logging.WARNING,
    format='%(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

import sys
print("MCP Server (blog-keyword-analyzer) starting...", file=sys.stderr, flush=True)

from fastmcp import FastMCP
from .runner import run_sync
from .schemas import RunRequest, TopicIdea

# Thread pool for running sync code from async context
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="blog-kwa")

mcp = FastMCP("blog-keyword-analyzer")


@mcp.tool()
async def fetch_keywords(
    topic: str,
    product_name: str = "Aspose.Cells",
    platform: str = "general",
    brand: str = "Aspose",
) -> dict:
    """
    Analyze keywords for a topic using the blog-keyword-analyzer workflow.

    Takes a topic/title and returns SEO keyword groups: primary, secondary (context),
    and long-tail keywords, along with topic metadata (title, angle, outline, persona).

    Args:
        topic: The topic/title to analyze keywords for
        product_name: Product name (default: Aspose.Cells)
        platform: Blog platform/context (default: general)
        brand: Brand name (default: Aspose)

    Returns:
        Dictionary with status, keywords dict (primary/secondary/long_tail),
        and optional topic_idea with full analysis metadata.

    Example response:
        {
            "status": "success",
            "topic": "How to read Excel files in Python",
            "keywords": {
                "primary": ["read excel files python"],
                "secondary": ["python xlsx library", "pandas excel"],
                "long_tail": ["how to read xlsx in python", "python openpyxl tutorial"],
                "metadata": {
                    "title": "...",
                    "angle": "...",
                    "outline": [...],
                    "target_persona": "...",
                    "editorial_notes": [...]
                }
            },
            "topic_idea": { ... }  # Full TopicIdea object
        }
    """
    try:
        # Build RunRequest for the workflow
        run_request = RunRequest(
            brand=brand,
            product=product_name,
            locale="en-US",
            file_path="",  # Not used when records are provided
            top_clusters=3,  # Limit to top 3 clusters for faster processing
            max_rows=50000,
        )

        logger.debug(
            "Analyzing keywords for topic=%r product=%r platform=%r brand=%r",
            topic, product_name, platform, brand
        )

        # Run the keyword analysis workflow (run_sync is synchronous)
        # Pass seed_topic and empty records to skip CSV file loading
        # Use thread pool to avoid nested event loop error in FastMCP async context
        loop = asyncio.get_running_loop()
        run_result, metrics = await loop.run_in_executor(
            _executor,
            lambda: run_sync(
                run_request,
                platform=platform,
                seed_topic=topic,
                records=[],  # Skip file loading; use seed_topic only
                use_content_index=False,  # Skip content index lookup
                source="llm",  # Use LLM for keyword generation from seed_topic
            ),
        )

        if not run_result or not run_result.topics:
            logger.warning("No topics generated for %r", topic)
            return {
                "status": "error",
                "error": "No topics generated",
                "topic": topic,
                "keywords": {
                    "primary": [topic],
                    "secondary": [],
                    "long_tail": [],
                },
            }

        # Use the top-ranked topic idea
        topic_idea: TopicIdea = run_result.topics[0]

        # Convert to the keyword format consumers expect
        keywords = {
            "primary": [topic_idea.primary_keyword] if topic_idea.primary_keyword else [topic],
            "secondary": topic_idea.keyword_groups.context_keywords or [],
            "long_tail": topic_idea.keyword_groups.long_tail_keywords or [],
            "metadata": {
                "title": topic_idea.title,
                "angle": topic_idea.angle,
                "outline": topic_idea.outline,
                "target_persona": topic_idea.target_persona,
                "editorial_notes": topic_idea.editorial_notes,
                "cluster_id": topic_idea.cluster_id,
                "internal_links": topic_idea.internal_links,
            }
        }

        logger.info(
            "Keywords analyzed: topic=%r title=%r keywords=%d",
            topic, topic_idea.title,
            len(keywords["primary"]) + len(keywords["secondary"]) + len(keywords["long_tail"])
        )

        return {
            "status": "success",
            "topic": topic,
            "keywords": keywords,
            "topic_idea": topic_idea.model_dump(),  # Full analysis for advanced consumers
        }

    except (Exception, SystemExit) as e:
        error_msg = str(e)
        logger.exception("Keyword analysis failed for topic %r: %s", topic, error_msg)

        # SystemExit typically means missing API key or config — let consumers fall back gracefully
        if isinstance(e, SystemExit):
            error_msg = f"Configuration error: {error_msg}"

        return {
            "status": "error",
            "error": error_msg,
            "topic": topic,
            "keywords": {
                "primary": [topic],
                "secondary": [],
                "long_tail": [],
            },
        }


if __name__ == "__main__":
    mcp.run()
