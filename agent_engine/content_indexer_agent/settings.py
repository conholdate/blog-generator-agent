from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    METRICS_ENABLED: bool = False
    METRICS_REQUIRED: bool = False
    METRICS_TIMEOUT_S: float = 10.0
    METRICS_WEBHOOK_URL: Optional[str] = None
    METRICS_TOKEN: Optional[str] = None
    METRICS_AGENT_NAME: str = "Content Indexer Agent"
    METRICS_AGENT_OWNER: str = "Muzammil Khan"

    INT_METRICS_WEBHOOK_URL: Optional[str] = None
    INT_METRICS_TOKEN: Optional[str] = None

    def resolved_openai_api_key(self) -> Optional[str]:
        return self.PROFESSIONALIZE_API_KEY or self.PROFESSIONALIZE_API_KEY_1 or self.OPENAI_API_KEY

    def resolved_openai_base_url(self) -> Optional[str]:
        return self.PROFESSIONALIZE_BASE_URL or self.OPENAI_BASE_URL


settings = Settings()
