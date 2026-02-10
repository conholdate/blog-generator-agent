from pydantic_settings import BaseSettings
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()  # loads .env from project root by default


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

    # --- SerpAPI integration ---
    SERPAPI_KEY: str = "66c1df1bd9d524fc1f5864c6070b9a73666994b392127d642839817119d7992d"
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
    DEBUG: bool = False

    # --- NEW: Metrics / Google Apps Script webhook ---
    METRICS_WEBHOOK_URL: str = "https://script.google.com/macros/s/AKfycbyCHwElrM6RcYLi0JNQAkJmzGrBjAhf28mKXVyub_6SdaZ2ITvzCwfM5xCLE7rmuxio/exec"
    METRICS_TOKEN: str = ""
    METRICS_AGENT_NAME: str = "Keyword Analyzer"
    METRICS_AGENT_OWNER: str = "Muzammil Khan"
    METRICS_KEYWORD_CLUSTERING_JOB: str = "Keyword Clustering"
    METRICS_TOPIC_GENERATION_JOB: str = "Topics Generation"

    # --- Internal Blog Teams Metrics / Google Apps Script webhook ---
    INT_METRICS_WEBHOOK_URL: str = "https://script.google.com/macros/s/AKfycbwYyPBs3ox6xhYfznVpu4Gh8T4l7cXrAIj1m_y1g-vWn6tyP_LAkv3eo6W2EZYAeHgLag/exec"
    INT_METRICS_TOKEN: str = "-2026"

settings = Settings()

BRAND_METRICS: dict[str, Tuple[str, str]] = {
    # key: normalized brand (lowercase)
    "aspose": ("aspose.com", "Blog"),
    "groupdocs": ("groupdocs.com", "Blog"),
    "asposecloud": ("aspose.cloud", "Blog"),
    "groupdocscloud": ("groupdocs.cloud", "Blog"),
    "conholdate": ("conholdate.com", "Blog"),
    "familiarize": ("familiarize.com", "Blog"),
    # add more brands here...
}
platform_LABELS: Dict[str, str] = {
    "python": "Python",
    "java": "Java",
    "c#": "C#",
    "c++": "C++",
    "php": "PHP",
    "javascript": "JavaScript",
    "nodejs": "Node.js",
}

# Canonical platform -> list of patterns to search for
platform_PATTERNS: Dict[str, List[str]] = {
    "python": ["python"],
    "java": ["java"],
    "c#": ["c#", "csharp", "c-sharp", "dotnet", ".net", "asp.net", "vb.net"],
    "c++": ["c++", "cpp"],
    "php": ["php"],
    "javascript": ["javascript", "js"],
    "nodejs": ["node.js", "nodejs", "node js"],
    # you can add more later: "go": ["golang", "go "], etc.
}