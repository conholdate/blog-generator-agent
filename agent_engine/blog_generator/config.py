"""
Configuration for Blog Agent
"""
import os, sys
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8"
    )

    PROFESSIONALIZE_BASE_URL: str = "http://your-llm-server.com/v1"
    PROFESSIONALIZE_API_KEY_2: str = "your-api-key"
    PROFESSIONALIZE_LLM_MODEL: str = "gpt-oss"
    GIST_NAME: str = "mustafabutt"
    REPO_PAT: str = ""
    # Paths
    PRODUCTS_JSON_PATH: str = "../data/products.json"
    OUTPUT_DIR: str = "../output/blogs"
    
    SERPAPI_KEY: str = ""  
    GOOGLE_SCRIPT_URL_FOR_TEAM: str= ""
    TOKEN_FOR_TEAM: str = ""
    METRICS_API_KEY:str=""
    METRICS_API_URL:str=""


    CONSOLIDATED_SHEET_NAME_FOR_BLOGPOST_METADATA:str=""
    GOOGLE_KEY:str=""
    SPREADSHEET_ID_FOR_KEYWORDS:str=""
    SPREADSHEET_ID_FOR_BLOGPOST_METADATA:str=""
    ASPOSE_COM_AUTHOR:str=""
    ASPOSE_CLOUD_AUTHOR:str=""
    GROUPDOCS_CLOUD_AUTHOR:str=""

    # GSC-driven topic selection (fail-safe: any error falls back to round-robin)
    GSC_ENABLED: bool = True                       # kill-switch
    GSC_PROPERTY_URL: str = ""                     # default: https://blog.<brand>/
    GSC_TOP_N: int = 5                             # opportunities tried per run
    GSC_MIN_IMPRESSIONS: int = 30                  # floor over the recent 90-day window
    GSC_POSITION_MIN: float = 8.0                  # striking-distance band
    GSC_POSITION_MAX: float = 20.0
    GSC_MATCH_MIN_COVERAGE: float = 0.7            # keyword-token overlap to accept a topic
    GSC_SUGGESTIONS_SHEET_NAME: str = "GSC Suggestions"

    # Agent Settings
    NUMBER_OF_BLOG_WORDS: int = 0  
    ENVIRONMENT: str = ""
    KRA_DATA_DIR: str = "./src/data/samples"
    KRA_OUTPUT_DIR: str = "./src/data/outputs"
    TOP_CLUSTERS: int = 10
    MAX_ROWS: int = 50000
    DEBUG: bool = False
    # Optional value which your helper method uses
    ALLOWED_ORIGINS: str = "*"

    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()