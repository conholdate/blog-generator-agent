from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def _load_env_once() -> None:
    """
    Loads .env exactly once, early, so all modules see env vars.
    """
    # Safe to call multiple times; dotenv internally handles idempotency.
    load_dotenv(override=False)


_load_env_once()


@dataclass(frozen=True)
class CoverageSettings:
    # Paths
    repo_root: Path = field(default_factory=lambda: Path(os.getenv("CG_REPO_ROOT", Path.cwd())).resolve())
    outputs_root: Path = field(default_factory=lambda: Path(os.getenv("CG_OUTPUTS_ROOT", (Path.cwd() / "outputs"))).resolve())


    # Matching
    threshold_strict: float = 0.86
    threshold_loose: float = 0.80
    top_k: int = 5

    # Existing standardized env vars (your convention)
    PROFESSIONALIZE_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("PROFESSIONALIZE_API_KEY"))
    PROFESSIONALIZE_BASE_URL: Optional[str] = field(default_factory=lambda: os.getenv("PROFESSIONALIZE_BASE_URL"))
    PROFESSIONALIZE_LLM_MODEL: str = field(default_factory=lambda: os.getenv("PROFESSIONALIZE_LLM_MODEL", "gpt-5.2"))
    PROFESSIONALIZE_EMBEDDING_MODEL: str = field(
        default_factory=lambda: os.getenv("PROFESSIONALIZE_EMBEDDING_MODEL", "text-embedding-3-large")
    )

    # Canonical resolved OpenAI settings (what the SDK/client should use)
    OPENAI_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    OPENAI_BASE_URL: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))

    # Metrics
    METRICS_ENABLED: bool = True
    METRICS_TIMEOUT_S: float = 12.0

    # Required
    METRICS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyCHwElrM6RcYLi0JNQAkJmzGrBjAhf28mKXVyub_6SdaZ2ITvzCwfM5xCLE7rmuxio/exec"
    METRICS_TOKEN = "lM6iU2mW0gV1eZ"

    # Required metadata
    METRICS_AGENT_NAME = "Content Gap Agent"  # or whatever run-level name you want
    METRICS_AGENT_OWNER = "Muzammil Khan"

    # Optional
    DEBUG = False
    INT_METRICS_WEBHOOK_URL: str = "https://script.google.com/macros/s/AKfycbwYyPBs3ox6xhYfznVpu4Gh8T4l7cXrAIj1m_y1g-vWn6tyP_LAkv3eo6W2EZYAeHgLag/exec"
    INT_METRICS_TOKEN: str = "blog_team_agent-2026"

    @staticmethod
    def from_env() -> "CoverageSettings":
        # Dataclass reads env via default_factory; .env already loaded above.
        return CoverageSettings()

    def resolved_openai_api_key(self) -> Optional[str]:
        return self.PROFESSIONALIZE_API_KEY or self.OPENAI_API_KEY

    def resolved_openai_base_url(self) -> Optional[str]:
        return self.PROFESSIONALIZE_BASE_URL or self.OPENAI_BASE_URL
