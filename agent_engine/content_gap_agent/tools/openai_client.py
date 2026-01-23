from __future__ import annotations

from typing import Optional

from openai import OpenAI

from ..settings import CoverageSettings


def get_openai_client(settings: CoverageSettings) -> OpenAI:
    """
    Single source of truth for OpenAI client initialization.
    Uses your env-backed settings resolution.
    """
    api_key = settings.resolved_openai_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenAI API key is missing. Set PROFESSIONALIZE_API_KEY (preferred) or OPENAI_API_KEY in .env/env."
        )

    base_url: Optional[str] = settings.resolved_openai_base_url()

    # OpenAI client accepts base_url=None safely (uses default).
    return OpenAI(api_key=api_key, base_url=base_url)
