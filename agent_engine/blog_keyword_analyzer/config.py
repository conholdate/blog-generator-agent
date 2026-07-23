from dotenv import load_dotenv
from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()  # loads .env from project root by default

# Sentinel default for PROFESSIONALIZE_API_KEY. Deliberately not a real-shaped
# credential: the OpenAI SDK client constructor requires a non-empty string at
# import time (empty string raises), so this must stay non-empty, but it must
# also never be mistakable for a live key. Real configuration must come from
# CUSTOM_LLM_API_KEY / PROFESSIONALIZE_API_KEY in the environment or .env.
UNCONFIGURED_API_KEY = "not-configured"


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
        populate_by_name=True,
    )
    PROFESSIONALIZE_BASE_URL: str = Field(
        default="https://llm.professionalize.com/v1",
        validation_alias=AliasChoices("PROFESSIONALIZE_BASE_URL", "CUSTOM_LLM_BASE_URL"),
    )
    # No secret ships as a source default. If neither PROFESSIONALIZE_API_KEY nor
    # CUSTOM_LLM_API_KEY is set in the environment/.env, this stays at the
    # UNCONFIGURED_API_KEY sentinel and the CLI fails closed with a clear error
    # (see runner.main()) instead of silently using a committed credential.
    PROFESSIONALIZE_API_KEY: str = Field(
        default=UNCONFIGURED_API_KEY,
        validation_alias=AliasChoices("PROFESSIONALIZE_API_KEY", "CUSTOM_LLM_API_KEY"),
    )

    # Standard OpenAI key (used when no custom base URL is set)
    OPENAI_API_KEY: str | None = None

    # --- Model defaults ---
    PROFESSIONALIZE_LLM_MODEL: str = Field(
        default="gpt-oss",
        validation_alias=AliasChoices("PROFESSIONALIZE_LLM_MODEL", "DEFAULT_LLM_MODEL"),
    )

    # --- SerpAPI integration ---
    # Empty by default; serp_import.py already treats a falsy SERPAPI_KEY as
    # "not configured" and degrades gracefully (returns no SERP keywords).
    SERPAPI_KEY: str = ""
    SERPAPI_ENGINE: str = "google"  # we’ll use standard Google search

    # --- KRA scoring / data dirs (unchanged) ---
    W_VOLUME: float = 0.35
    W_KD: float = 0.25
    W_CPC: float = 0.15
    W_BRAND: float = 0.15
    W_INTENT: float = 0.10
    TOP_CLUSTERS: int = 15
    MAX_ROWS: int = 50000    
    KRA_DATA_DIR: str = "./content"
    KRA_OUTPUT_DIR: str = "./content"
    BLOG_CONTENT_ROOT: str = ""
    KRA_METRICS_DB_PATH: str = "./src/data/kra_metrics_db.json"
    # Persisted, cross-run topic-title history (brand/product/platform ->
    # previously generated/rejected titles). Lets a later, separate run avoid
    # regenerating a title an earlier run already produced, even before that
    # title's post is published (content-index dedup only knows about already
    # published posts).
    KRA_RUN_HISTORY_PATH: str = "./content/kra_run_history.json"
    DEBUG: bool = False
    GOOGLE_SERVICE_ACCOUNT_FILE: str = ""

    # --- Metrics labels. Webhook URLs/tokens are loaded from configs/metrics.json. ---
    METRICS_AGENT_NAME: str = "Keyword Analyzer"
    METRICS_AGENT_OWNER: str = "Muzammil Khan"
    METRICS_KEYWORD_CLUSTERING_JOB: str = "Keyword Clustering"
    METRICS_TOPIC_GENERATION_JOB: str = "Topics Generation"

settings = Settings()
