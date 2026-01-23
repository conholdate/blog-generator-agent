from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    # Read env at INSTANCE creation time (not import time)
    PROFESSIONALIZE_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("PROFESSIONALIZE_API_KEY"))
    PROFESSIONALIZE_BASE_URL: Optional[str] = field(default_factory=lambda: os.getenv("PROFESSIONALIZE_BASE_URL"))
    PROFESSIONALIZE_LLM_MODEL: str = field(default_factory=lambda: os.getenv("PROFESSIONALIZE_LLM_MODEL", "gpt-oss"))
    PROFESSIONALIZE_EMBEDDING_MODEL: str = field(
        default_factory=lambda: os.getenv("PROFESSIONALIZE_EMBEDDING_MODEL", "qwen3-embedding-8b")
    )

    # Local dev fallback
    OPENAI_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    OPENAI_BASE_URL: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))

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
