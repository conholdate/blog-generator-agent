"""
Blog Orchestrator MCP Server (HTTP)

Wraps the existing BlogOrchestrator so it can be called remotely over MCP
(Streamable HTTP) instead of only via `python main.py` on the CLI.

This is an additional entrypoint only - it does not change main.py,
orchestrator.py, mcp_tools.py, or any of the internal stdio MCP servers,
which continue to work exactly as before.
"""

import sys
import os
import uuid
import asyncio
import traceback

from fastmcp import FastMCP

# agent_engine/blog_generator uses bare imports (e.g. `from config import settings`,
# `from tools.mcp_tools import ...`) and mcp_tools.py spawns the internal stdio
# servers using paths relative to that directory (e.g. "../../mcp-servers/...").
# main.py works because it is normally run *from* that directory, so we replicate
# both the sys.path entry and the working directory here before importing it.
BLOG_GENERATOR_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "agent_engine", "blog_generator")
)
sys.path.insert(0, BLOG_GENERATOR_DIR)
os.chdir(BLOG_GENERATOR_DIR)

from agent_logic.orchestrator import BlogOrchestrator  # noqa: E402

mcp = FastMCP("blog-orchestrator")

# In-memory job store. Generation is async and can take minutes, so tool calls
# return a job_id immediately instead of blocking the MCP connection.
_jobs: dict[str, dict] = {}


def _build_message(result: dict) -> str:
    """
    Human-readable confirmation message, mirroring the console output
    orchestrator.py already prints (e.g. "Blog post generation completed! ...File: ...").
    Reconstructed here rather than in orchestrator.py, since its return dict
    only carries folder_name/brand, not the full filepath. Path pattern matches
    the sanitization file-generator/server.py applies to brand names.
    """
    if not result:
        return "Blog post generation finished with no result (topic may already be skipped)."

    status = result.get("status")
    if status == "success":
        brand = result.get("brand", "")
        folder_name = result.get("folder_name", "")
        brand_safe = brand.replace(".", "_").replace("-", "_")
        filepath = f"../../content/blogPosts/{brand_safe}/{folder_name}/index.md"
        return f"✅ Blog post generation completed!\n📄 File: {filepath}"

    if status == "skipped":
        return f"⏭️ Blog post generation skipped: {result.get('message', 'no reason given')}"

    if status == "error":
        return f"❌ Blog post generation failed: {result.get('message', 'unknown error')}"

    return f"Blog post generation finished with status: {status}"


async def _run_job(job_id: str, brand: str, author: str) -> None:
    try:
        orchestrator = BlogOrchestrator(brand=brand)
        result = await orchestrator.create_blog_autonomously(author=author)
        _jobs[job_id] = {
            "status": "success",
            "result": result,
            "message": _build_message(result),
        }
    except Exception as e:
        _jobs[job_id] = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@mcp.tool()
async def generate_blog_post(brand: str, author: str) -> dict:
    """
    Start autonomous blog post generation for a brand.

    Pulls the next approved topic from that brand's Google Sheet queue and
    runs the same generation flow as `python main.py --brand <brand> --author <author>`.
    Does not block until completion - poll get_job_status with the returned
    job_id to retrieve the result.

    Args:
        brand: Brand domain, e.g. "aspose.com", "groupdocs.com", "conholdate.com"
        author: Author name to attribute the generated post to

    Returns:
        Dictionary with job_id and status ("running")
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running"}
    asyncio.create_task(_run_job(job_id, brand, author))
    return {"job_id": job_id, "status": "running"}


@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Check the status/result of a job started by generate_blog_post.

    Args:
        job_id: The job_id returned by generate_blog_post

    Returns:
        Dictionary with status ("running" | "success" | "error" | "not_found"),
        and once finished, a human-readable "message" plus the raw "result" payload
        (or error details).
    """
    job = _jobs.get(job_id)
    if job is None:
        return {"status": "not_found"}
    return {"job_id": job_id, **job}


if __name__ == "__main__":
    # Localhost only, no auth - matches current testing scope.
    mcp.run(transport="http", host="127.0.0.1", port=8800)
