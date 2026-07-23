from __future__ import annotations

from ..config import Settings
from .base import LLMClient
from .professionalize_client import ProfessionalizeClient


def get_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "professionalize":
        if not settings.professionalize_base_url:
            raise RuntimeError("PROFESSIONALIZE_BASE_URL is not set")
        if not settings.professionalize_api_key:
            raise RuntimeError("PROFESSIONALIZE_API_KEY is not set")
        return ProfessionalizeClient(
            base_url=settings.professionalize_base_url,
            api_key=settings.professionalize_api_key,
            model=settings.professionalize_llm_model,
        )
    raise ValueError(f"Unknown llm_provider: {settings.llm_provider!r}")
