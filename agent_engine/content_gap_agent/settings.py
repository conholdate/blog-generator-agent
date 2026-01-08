"""
settings.py

Centralized settings + .env loading for Content Gap Analyzer.

- Loads .env from:
  1) current working directory
  2) repo root-ish folder (parent of the package directory)

- Provides a Settings dataclass with sane defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def _load_env_files() -> None:
    """Load .env in a predictable order (without overriding already-set env vars)."""
    # 1) CWD/.env
    load_dotenv(override=False)

    # 2) repo root-ish: <agent_engine>/.env
    # settings.py is typically: agent_engine/content_gap_agent/settings.py
    # parents[0] = content_gap_agent, parents[1] = agent_engine
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=repo_root / ".env", override=False)


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    return val if val not in (None, "") else default


def _env_bool(name: str, default: bool = False) -> bool:
    v = (os.getenv(name) or "").strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    return default


@dataclass(frozen=True)
class Settings:
    # Auth / LLM
    PROFESSIONALIZE_API_KEY: Optional[str]
    llm_api_key: Optional[str]

    PROFESSIONALIZE_BASE_URL: Optional[str]
    PROFESSIONALIZE_LLM_MODEL: Optional[str]
    PROFESSIONALIZE_EMBEDDING_MODEL: Optional[str]
    openai_api_style: str  # "responses" or "chat_completions"

    # Defaults (can be overridden by CLI args)
    blog: str
    product: Optional[str]
    platform: Optional[str]

    # Paths
    config_dir: str
    output_dir: str
    repo_cache_dir: str

    # Behavior
    flush: bool
    log_level: str

    # Metrics
    metrics_endpoint: str
    metrics_token: str
    metrics_agent_name: str
    metrics_agent_owner: str
    metrics_website: str
    metrics_website_section: str
    metrics_enabled: bool
    INT_METRICS_WEBHOOK_URL: str
    INT_METRICS_TOKEN: str

    @property
    def any_api_key(self) -> Optional[str]:
        """Return whichever API key is available."""
        return self.PROFESSIONALIZE_API_KEY or self.llm_api_key


def load_settings() -> Settings:
    """Load Settings from environment (after loading .env files)."""
    _load_env_files()

    return Settings(
        PROFESSIONALIZE_API_KEY=_env("PROFESSIONALIZE_API_KEY"),
        llm_api_key=_env("LLM_API_KEY"),

        PROFESSIONALIZE_BASE_URL=_env("PROFESSIONALIZE_BASE_URL"),
        PROFESSIONALIZE_LLM_MODEL=_env("PROFESSIONALIZE_LLM_MODEL"),
        PROFESSIONALIZE_EMBEDDING_MODEL=_env("PROFESSIONALIZE_EMBEDDING_MODEL"),

        openai_api_style=_env("OPENAI_API_STYLE", "responses") or "responses",

        blog=_env("BLOG", "aspose") or "aspose",
        product=_env("PRODUCT", None),
        platform=_env("PLATFORM", None),

        config_dir=_env("CONFIG_DIR", "./config") or "./config",
        output_dir=_env("OUTPUT_DIR", "./output") or "./output",
        repo_cache_dir=_env("REPO_CACHE_DIR", "./repo_cache") or "./repo_cache",

        flush=_env_bool("FLUSH", False),
        log_level=_env("LOG_LEVEL", "INFO") or "INFO",

        # Metrics configuration
        metrics_endpoint=_env(
            "METRICS_ENDPOINT",
            "https://script.google.com/macros/s/AKfycbyCHwElrM6RcYLi0JNQAkJmzGrBjAhf28mKXVyub_6SdaZ2ITvzCwfM5xCLE7rmuxio/exec"
        ) or "",
        metrics_token=_env("METRICS_TOKEN", "lM6iU2mW0gV1eZ") or "lM6iU2mW0gV1eZ",
        metrics_agent_name=_env("METRICS_AGENT_NAME", "Content Gap Agent") or "Content Gap Agent",
        metrics_agent_owner=_env("METRICS_AGENT_OWNER", "Muzammil Khan") or "Muzammil Khan",
        metrics_website=_env("METRICS_WEBSITE", "aspose.com") or "aspose.com",
        metrics_website_section=_env("METRICS_WEBSITE_SECTION", "Blog") or "Blog",
        metrics_enabled=_env_bool("METRICS_ENABLED", True),

        # --- Internal Blog Teams Metrics / Google Apps Script webhook ---
        INT_METRICS_WEBHOOK_URL=_env(
            "INT_METRICS_WEBHOOK_URL",
            "https://script.google.com/macros/s/AKfycbwYyPBs3ox6xhYfznVpu4Gh8T4l7cXrAIj1m_y1g-vWn6tyP_LAkv3eo6W2EZYAeHgLag/exec"
        ) or "",

        INT_METRICS_TOKEN=_env("INT_METRICS_TOKEN", "blog_team_agent-2026") or "blog_team_agent-2026",
    )
