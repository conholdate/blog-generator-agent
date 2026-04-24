from __future__ import annotations

from openai import AsyncOpenAI, OpenAI
from agents import set_default_openai_client

from ..settings import Settings


def build_openai_clients(s: Settings) -> tuple[OpenAI, AsyncOpenAI]:
    api_key = s.PROFESSIONALIZE_API_KEY or s.OPENAI_API_KEY
    if not api_key:
        raise EnvironmentError(
            "Missing API key. Set PROFESSIONALIZE_API_KEY (preferred) or OPENAI_API_KEY."
        )
    base_url = s.PROFESSIONALIZE_BASE_URL or s.OPENAI_BASE_URL

    sync_client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    async_client = (
        AsyncOpenAI(api_key=api_key, base_url=base_url) if base_url else AsyncOpenAI(api_key=api_key)
    )

    # Agents SDK uses the default async client for tool execution.
    set_default_openai_client(async_client)
    return sync_client, async_client
