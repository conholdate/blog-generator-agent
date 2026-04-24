from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoverageSettings(BaseSettings):
    """
    Environment-backed coverage settings. Secrets and webhook URLs must come
    from environment variables, `.env`, or CI secrets; source defaults stay
    non-sensitive.
    """

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    repo_root: Path = Field(default_factory=lambda: Path.cwd().resolve(), alias="CG_REPO_ROOT")
    outputs_root: Path = Field(default_factory=lambda: (Path.cwd() / "outputs").resolve(), alias="CG_OUTPUTS_ROOT")

    threshold_strict: float = 0.86
    threshold_loose: float = 0.80
    top_k: int = 5

    PROFESSIONALIZE_BASE_URL: Optional[str] = "https://llm.professionalize.com/v1"
    PROFESSIONALIZE_API_KEY: Optional[str] = None
    PROFESSIONALIZE_API_KEY_1: Optional[str] = None
    PROFESSIONALIZE_LLM_MODEL: str = "gpt-oss"
    PROFESSIONALIZE_EMBEDDING_MODEL: str = "qwen3-embedding-8b"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    METRICS_ENABLED: bool = False
    METRICS_REQUIRED: bool = False
    METRICS_TIMEOUT_S: float = 12.0
    METRICS_WEBHOOK_URL: Optional[str] = None
    METRICS_TOKEN: Optional[str] = None
    METRICS_AGENT_NAME: str = "Content Gap Agent"
    METRICS_AGENT_OWNER: str = "Muzammil Khan"

    DEBUG: bool = False
    INT_METRICS_WEBHOOK_URL: Optional[str] = None
    INT_METRICS_TOKEN: Optional[str] = None

    # Legacy single-brand env vars retained for compatibility.
    TOPICS_ASPOSE_COM_WEBHOOK_URL: Optional[str] = None
    TOPICS_ASPOSE_COM_TOKEN: Optional[str] = None
    TOPICS_ASPOSE_COM_COVERAGE_JSON: Optional[str] = None

    TOPICS_GROUPDOCS_COM_WEBHOOK_URL: Optional[str] = None
    TOPICS_GROUPDOCS_COM_TOKEN: Optional[str] = None
    TOPICS_GROUPDOCS_COM_COVERAGE_JSON: Optional[str] = None

    TOPICS_CONHOLDATE_COM_WEBHOOK_URL: Optional[str] = None
    TOPICS_CONHOLDATE_COM_TOKEN: Optional[str] = None
    TOPICS_CONHOLDATE_COM_COVERAGE_JSON: Optional[str] = None

    TOPICS_ASPOSE_CLOUD_WEBHOOK_URL: Optional[str] = None
    TOPICS_ASPOSE_CLOUD_TOKEN: Optional[str] = None
    TOPICS_ASPOSE_CLOUD_COVERAGE_JSON: Optional[str] = None

    TOPICS_GROUPDOCS_CLOUD_WEBHOOK_URL: Optional[str] = None
    TOPICS_GROUPDOCS_CLOUD_TOKEN: Optional[str] = None
    TOPICS_GROUPDOCS_CLOUD_COVERAGE_JSON: Optional[str] = None

    TOPICS_CONHOLDATE_CLOUD_WEBHOOK_URL: Optional[str] = None
    TOPICS_CONHOLDATE_CLOUD_TOKEN: Optional[str] = None
    TOPICS_CONHOLDATE_CLOUD_COVERAGE_JSON: Optional[str] = None

    # Preferred per-brand config. In env/.env, provide JSON such as:
    # {"aspose":{"webhook_url":"...","token":"...","sheet_name":"All Missing Topics"}}
    TOPICS_SHEETS: dict[str, dict[str, str]] = Field(default_factory=dict)

    @staticmethod
    def from_env() -> "CoverageSettings":
        return CoverageSettings()

    def resolved_openai_api_key(self) -> Optional[str]:
        return self.PROFESSIONALIZE_API_KEY or self.PROFESSIONALIZE_API_KEY_1 or self.OPENAI_API_KEY

    def resolved_openai_base_url(self) -> Optional[str]:
        return self.PROFESSIONALIZE_BASE_URL or self.OPENAI_BASE_URL

    def model_post_init(self, __context: object) -> None:
        if not self.repo_root.is_absolute():
            self.repo_root = self.repo_root.resolve()
        if not self.outputs_root.is_absolute():
            self.outputs_root = (self.repo_root / self.outputs_root).resolve()
