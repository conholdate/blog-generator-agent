from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
        Settings are loaded in this order (typical):
        1) Environment variables (CI/CD / repo secrets / container env)
        2) .env file (local dev)
        3) Defaults (non-secret safe defaults only)
        """

    # Tell pydantic-settings where to look for .env
    # Adjust Path(...) if your config.py is not in repo root.
    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    PROFESSIONALIZE_BASE_URL: str ="https://llm.professionalize.com/v1"
    PROFESSIONALIZE_API_KEY_1: SecretStr | None = None
    PROFESSIONALIZE_API_KEY: str = PROFESSIONALIZE_API_KEY_1

    # Standard OpenAI key (used when no custom base URL is set)
    OPENAI_API_KEY: str | None = None

    # --- Model defaults ---
    PROFESSIONALIZE_LLM_MODEL: str = "gpt-oss"

    PROFESSIONALIZE_EMBEDDING_MODEL: str = field(
        default_factory=lambda: os.getenv("PROFESSIONALIZE_EMBEDDING_MODEL", "qwen3-embedding-8b")
    )

    # Output root
    OUTPUTS_DIR: Path = field(default_factory=lambda: Path(os.getenv("CG_OUTPUTS_DIR", "outputs")))

    # Metrics
    METRICS_ENABLED: bool = True
    METRICS_TIMEOUT_S: float = 10.0

    # Required
    METRICS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyCHwElrM6RcYLi0JNQAkJmzGrBjAhf28mKXVyub_6SdaZ2ITvzCwfM5xCLE7rmuxio/exec"
    METRICS_TOKEN = "lM6iU2mW0gV1eZ"

    # Required metadata
    METRICS_AGENT_NAME = "Content Indexer Agent"   # or whatever run-level name you want
    METRICS_AGENT_OWNER = "Muzammil Khan"

    # Optional
    DEBUG = False
    INT_METRICS_WEBHOOK_URL: str = "https://script.google.com/macros/s/AKfycbwYyPBs3ox6xhYfznVpu4Gh8T4l7cXrAIj1m_y1g-vWn6tyP_LAkv3eo6W2EZYAeHgLag/exec"
    INT_METRICS_TOKEN: str = "blog_team_agent-2026"
