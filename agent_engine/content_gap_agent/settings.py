from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent_engine.config_sources import load_agent_metrics_config, load_json_object, resolve_config_env_value


def _config_value(raw_cfg: dict[str, Any], key: str, *, env_file: Path) -> str | None:
    from_env = resolve_config_env_value(raw_cfg, key, env_file=env_file)
    if from_env:
        return from_env
    value = str(raw_cfg.get(key) or "").strip()
    return value or None


def _load_topics_sheets_config(repo_root: Path, config_path: Path) -> dict[str, dict[str, str]]:
    resolved_path = config_path if config_path.is_absolute() else (repo_root / config_path)
    if not resolved_path.exists():
        legacy_parts = resolved_path.parts
        if "config" in legacy_parts:
            replaced_parts = tuple("configs" if part == "config" else part for part in legacy_parts)
            candidate = Path(*replaced_parts)
            if candidate.exists():
                resolved_path = candidate
    data = load_json_object(resolved_path)

    loaded: dict[str, dict[str, str]] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        cfg = {
            str(inner_key): str(inner_value)
            for inner_key, inner_value in value.items()
            if inner_value is not None
        }
        webhook_url = _config_value(value, "webhook_url", env_file=repo_root / ".env")
        token = _config_value(value, "token", env_file=repo_root / ".env")
        if webhook_url:
            cfg["webhook_url"] = webhook_url
        if token:
            cfg["token"] = token
        loaded[str(key)] = cfg
    return loaded


def _merge_topics_sheets(
    base: dict[str, dict[str, str]],
    override: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {str(key): dict(value) for key, value in (base or {}).items()}
    for key, value in (override or {}).items():
        normalized_key = str(key)
        current = dict(merged.get(normalized_key, {}))
        current.update({str(inner_key): str(inner_value) for inner_key, inner_value in value.items()})
        merged[normalized_key] = current
    return merged


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

    METRICS_ENABLED: bool = True
    METRICS_REQUIRED: bool = False
    METRICS_TIMEOUT_S: float = 10.0
    METRICS_AGENT_KEY: str = "content_gap_agent"
    METRICS_WEBHOOK_URL: Optional[str] = None
    METRICS_TOKEN: Optional[str] = None
    METRICS_AGENT_NAME: Optional[str] = None
    METRICS_AGENT_OWNER: Optional[str] = None
    METRICS_STAGES: list[str] = Field(default_factory=list)

    DEBUG: bool = False
    INT_METRICS_WEBHOOK_URL: Optional[str] = None
    INT_METRICS_TOKEN: Optional[str] = None
    METRICS_CONFIG_PATH: Path = Path("configs/metrics.json")
    TOPICS_SHEETS_CONFIG_PATH: Path = Path("configs/topics_sheets.json")
    TOPICS_SHEETS_TOKEN: Optional[str] = None

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
        metrics_config_path = self.METRICS_CONFIG_PATH
        if not metrics_config_path.is_absolute():
            metrics_config_path = (self.repo_root / metrics_config_path).resolve()
        self.METRICS_CONFIG_PATH = metrics_config_path

        metrics_cfg = load_agent_metrics_config(self.METRICS_CONFIG_PATH, self.METRICS_AGENT_KEY)
        webhooks = metrics_cfg.get("webhooks") or {}
        primary_cfg = webhooks.get("primary") or {}
        internal_cfg = webhooks.get("internal") or {}
        self.METRICS_AGENT_NAME = str(
            self.METRICS_AGENT_NAME or metrics_cfg.get("agent_name") or "Content Gap Agent"
        ).strip()
        self.METRICS_AGENT_OWNER = str(
            self.METRICS_AGENT_OWNER or metrics_cfg.get("agent_owner") or "Muzammil Khan"
        ).strip()
        if not self.METRICS_WEBHOOK_URL:
            self.METRICS_WEBHOOK_URL = _config_value(primary_cfg, "url", env_file=self.repo_root / ".env")
        if not self.METRICS_TOKEN:
            self.METRICS_TOKEN = _config_value(primary_cfg, "token", env_file=self.repo_root / ".env")
        if not self.INT_METRICS_WEBHOOK_URL:
            self.INT_METRICS_WEBHOOK_URL = _config_value(internal_cfg, "url", env_file=self.repo_root / ".env")
        if not self.INT_METRICS_TOKEN:
            self.INT_METRICS_TOKEN = _config_value(internal_cfg, "token", env_file=self.repo_root / ".env")
        self.METRICS_STAGES = [str(stage).strip() for stage in (metrics_cfg.get("stages") or []) if str(stage).strip()]

        config_path = self.TOPICS_SHEETS_CONFIG_PATH
        if not config_path.is_absolute():
            config_path = (self.repo_root / config_path).resolve()
        if not config_path.exists():
            candidate = (self.repo_root / "configs" / "topics_sheets.json").resolve()
            if candidate.exists():
                config_path = candidate
        self.TOPICS_SHEETS_CONFIG_PATH = config_path

        file_topics_sheets = _load_topics_sheets_config(self.repo_root, self.TOPICS_SHEETS_CONFIG_PATH)
        self.TOPICS_SHEETS = _merge_topics_sheets(file_topics_sheets, self.TOPICS_SHEETS)
