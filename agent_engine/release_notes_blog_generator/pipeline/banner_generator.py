from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from ..config import Settings
from ..models.article import BlogPost
from . import mcp_client
from .mcp_client import McpToolError

logger = logging.getLogger(__name__)

_BANNER_SERVER = "blog-banner-generator/tools/public-release-post-cover/banner_mcp_server.py"
_PRODUCT_LABEL_ALIGNMENT = "Left"


def generate_cover_image(post: BlogPost, settings: Settings) -> Path | None:
    """Calls the banner generator MCP server (mcp-servers/blog-banner-generator)
    to render the post's real cover image, following the same
    generate_blog_image(...) call agent_engine/blog_generator makes.

    Writes to a temp file rather than the final output_dir directly: this
    pipeline stage runs inside the orchestrator loop (before seo_editor.review,
    so the placeholder issue can be suppressed once a real image exists), while
    the final <publish_date>-<slug>/images/ folder is only created later by
    output/markdown_exporter.export(), which moves the temp file into place.

    Best-effort: any failure returns None, and the caller leaves the
    placeholder cover image issue in place exactly as before this integration
    existed.
    """
    if not settings.banner_generator_enabled:
        logger.debug("Banner generator disabled (banner_generator_enabled=False)")
        return None

    platform = post.fact_pack.platform
    product_family = f"Aspose.{platform.product_display} for {platform.platform_name}" if platform.product_display else "Aspose"
    output_path = Path(tempfile.gettempdir()) / f"aspose-blog-cover-{post.slug}.jpg"

    try:
        response = mcp_client.call_tool(
            _BANNER_SERVER,
            "generate_blog_image",
            {
                "product_family": product_family,
                "main_Heading": post.front_matter.title,
                "product_label_alignment": _PRODUCT_LABEL_ALIGNMENT,
                "output_path": str(output_path),
            },
            settings,
        )
    except (McpToolError, OSError, TimeoutError) as exc:
        logger.warning("Banner generator skipped: %s", exc)
        return None

    generated_path = response.get("output_path") if isinstance(response, dict) else None
    if not generated_path or not Path(generated_path).exists():
        logger.warning("Banner generator skipped: no output file produced (response=%r)", response)
        return None

    logger.info("Banner generated: %s", generated_path)
    return Path(generated_path)
