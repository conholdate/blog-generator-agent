from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..config import Settings

logger = logging.getLogger(__name__)


class McpToolError(RuntimeError):
    """Raised when an MCP server can't be reached or returns no usable content."""


def call_tool(
    server_relative_path: str,
    tool_name: str,
    arguments: dict[str, Any],
    settings: Settings,
    extra_env: dict[str, str] | None = None,
) -> Any:
    """Calls a tool on one of agent_engine's sibling MCP servers over stdio —
    the same calling convention agent_engine/blog_generator uses in
    tools/mcp_tools.py (StdioServerParameters + stdio_client +
    ClientSession.call_tool) to invoke its own sibling agents, so this
    pipeline can call the same servers (banner generator, keyword fetcher)
    once it's embedded alongside them under agent_engine/.

    Synchronous wrapper: the rest of this pipeline is sync (LLMClient.
    complete_structured is a blocking call), so each call gets its own
    short-lived event loop rather than threading async through every stage.
    """
    server_script = Path(settings.mcp_servers_dir) / server_relative_path
    if not server_script.exists():
        raise McpToolError(f"MCP server script not found: {server_script}")

    try:
        return asyncio.run(_call_tool(server_script, tool_name, arguments, settings, extra_env))
    except McpToolError:
        raise
    except Exception as exc:
        # Callers treat these servers as best-effort enrichment and catch
        # McpToolError, but a server that *starts* and then dies (missing
        # dependency, import error) surfaces as McpError, and stdio_client
        # wraps failures in an ExceptionGroup. Neither is an McpToolError, so
        # both used to escape the best-effort handlers and abort the topic —
        # turning a skipped banner or keyword lookup into zero drafts.
        raise McpToolError(f"{tool_name} on {server_script.name} failed: {exc!r}") from exc


async def _call_tool(
    server_script: Path,
    tool_name: str,
    arguments: dict[str, Any],
    settings: Settings,
    extra_env: dict[str, str] | None,
) -> Any:
    python = settings.mcp_python_executable or sys.executable
    params = StdioServerParameters(command=python, args=[str(server_script)], env=extra_env)

    logger.debug("Connecting to MCP server %s for tool %r", server_script, tool_name)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments),
                timeout=settings.mcp_call_timeout_seconds,
            )

    if not result.content:
        raise McpToolError(f"{tool_name} returned no content")

    content = result.content[0]
    text = getattr(content, "text", None)
    if text is None:
        raise McpToolError(f"{tool_name} returned non-text content: {content!r}")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text
