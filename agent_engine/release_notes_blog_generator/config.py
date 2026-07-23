from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "professionalize"  # "anthropic" | "openai" | "professionalize"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"

    # In-house OpenAI-compatible gateway (Chat Completions API at a custom base_url).
    professionalize_base_url: str | None = None
    # professionalize_api_key: str | None = None
    professionalize_api_key: str | None = Field(
        default=None,
        validation_alias="PROFESSIONALIZE_API_KEY_1",
    )
    professionalize_llm_model: str = "gpt-oss"
    professionalize_embedding_model: str = "qwen3-embedding-8b"

    allowed_domains: list[str] = Field(
        default_factory=lambda: ["releases.aspose.com", "docs.aspose.com"]
    )
    request_timeout_seconds: float = 20.0
    output_dir: str = "output"

    # DEBUG | INFO | WARNING | ERROR — progress logging verbosity. INFO shows one
    # line per pipeline stage/topic; DEBUG also shows raw LLM call timing.
    log_level: str = "INFO"

    # Front-matter "author" field on generated drafts (Professional Blogging Guide
    # examples all attribute posts to a named author). Override via .env if wrong.
    default_author: str = "Muzammil Khan"

    # MCP-server integrations — calls agent_engine's sibling agents over stdio
    # via the MCP protocol (StdioServerParameters + stdio_client + ClientSession),
    # the same calling convention agent_engine/blog_generator uses in
    # tools/mcp_tools.py to invoke its own sibling agents (banner generator,
    # keyword fetcher, etc.).
    mcp_servers_dir: str = r"C:\GitHub\blog-generator-agent\mcp-servers"
    mcp_python_executable: str | None = None  # defaults to sys.executable
    mcp_call_timeout_seconds: float = 90.0

    # Banner generator (mcp-servers/blog-banner-generator) — renders the post's
    # real cover image before export instead of leaving images/ empty.
    banner_generator_enabled: bool = True

    # Keyword analyzer (mcp-servers/keywords_auto) — SEO keyword groups fed into
    # the fact pack before the writer runs, instead of letting the writer invent
    # its own tags. Best-effort: any failure degrades to None.
    keyword_analyzer_enabled: bool = True

    # Read More section (pipeline/related_posts.py) — links to other published
    # posts for the same product, scraped from blog.aspose.com and appended
    # deterministically after the writer runs. Best-effort: any failure
    # degrades to no section at all, same as banner/keyword analyzer.
    related_posts_enabled: bool = True
    related_posts_count: int = 3
