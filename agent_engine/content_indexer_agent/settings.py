from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent_engine.config_loader import load_agent_metrics_config


class Settings(BaseSettings):
    """
    Settings are loaded from environment variables first, then `.env`, then
    non-secret defaults. Do not put webhook URLs, API keys, or tokens here.
    """

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROFESSIONALIZE_BASE_URL: Optional[str] = "https://llm.professionalize.com/v1"
    PROFESSIONALIZE_API_KEY: Optional[str] = None
    PROFESSIONALIZE_API_KEY_1: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    PROFESSIONALIZE_LLM_MODEL: str = "gpt-oss"
    PROFESSIONALIZE_EMBEDDING_MODEL: str = "qwen3-embedding-8b"

    OUTPUTS_DIR: Path = Path("outputs")

    METRICS_ENABLED: bool = True
    METRICS_REQUIRED: bool = False
    METRICS_TIMEOUT_S: float = 10.0
    METRICS_AGENT_KEY: str = "content_indexer_agent"
    METRICS_WEBHOOK_URL: Optional[str] = None
    METRICS_TOKEN: Optional[str] = None
    METRICS_AGENT_NAME: Optional[str] = None
    METRICS_AGENT_OWNER: Optional[str] = None
    METRICS_STAGES: list[str] = Field(default_factory=list)

    INT_METRICS_WEBHOOK_URL: Optional[str] = None
    INT_METRICS_TOKEN: Optional[str] = None
    METRICS_CONFIG_PATH: Path = Path("configs/metrics.json")

    def resolved_openai_api_key(self) -> Optional[str]:
        return self.PROFESSIONALIZE_API_KEY or self.PROFESSIONALIZE_API_KEY_1 or self.OPENAI_API_KEY

    def resolved_openai_base_url(self) -> Optional[str]:
        return self.PROFESSIONALIZE_BASE_URL or self.OPENAI_BASE_URL

    def model_post_init(self, __context: object) -> None:
        metrics_config_path = self.METRICS_CONFIG_PATH
        repo_root = Path.cwd().resolve()
        if not metrics_config_path.is_absolute():
            metrics_config_path = (repo_root / metrics_config_path).resolve()
        self.METRICS_CONFIG_PATH = metrics_config_path

        metrics_cfg = load_agent_metrics_config(self.METRICS_CONFIG_PATH, self.METRICS_AGENT_KEY)
        webhooks = metrics_cfg.get("webhooks") or {}
        primary_cfg = webhooks.get("primary") or {}
        internal_cfg = webhooks.get("internal") or {}
        self.METRICS_AGENT_NAME = str(
            self.METRICS_AGENT_NAME or metrics_cfg.get("agent_name") or "Content Indexer Agent"
        ).strip()
        self.METRICS_AGENT_OWNER = str(
            self.METRICS_AGENT_OWNER or metrics_cfg.get("agent_owner") or "Muzammil Khan"
        ).strip()
        if not self.METRICS_WEBHOOK_URL:
            self.METRICS_WEBHOOK_URL = str(primary_cfg.get("url") or "").strip() or None
        if not self.METRICS_TOKEN:
            self.METRICS_TOKEN = str(primary_cfg.get("token") or "").strip() or None
        if not self.INT_METRICS_WEBHOOK_URL:
            self.INT_METRICS_WEBHOOK_URL = str(internal_cfg.get("url") or "").strip() or None
        if not self.INT_METRICS_TOKEN:
            self.INT_METRICS_TOKEN = str(internal_cfg.get("token") or "").strip() or None
        self.METRICS_STAGES = [str(stage).strip() for stage in (metrics_cfg.get("stages") or []) if str(stage).strip()]


settings = Settings()
