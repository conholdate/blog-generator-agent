# content_gap_agent/agents/run.py

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI
from agents import Runner, set_default_openai_client, set_default_openai_api, set_tracing_disabled

from .settings import load_settings

from .tools import init_service


@dataclass(frozen=True)
class RunArgs:
    blog: str = "aspose"
    product: Optional[str] = None
    platform: Optional[str] = None
    config_dir: str = "./config"
    cache_dir: str = "./repo_cache"
    output_dir: str = "./output"
    flush: bool = False

def _configure_llm() -> str | None:
    s = load_settings()

    # Ensure default model is applied
    if s.PROFESSIONALIZE_LLM_MODEL:
        os.environ["PROFESSIONALIZE_LLM_MODEL"] = s.PROFESSIONALIZE_LLM_MODEL

    # If your provider doesn't support Responses API, force chat_completions
    # (safe to keep even if it does)
    set_default_openai_api("chat_completions")

    # Use your custom base URL explicitly
    base_url = s.PROFESSIONALIZE_BASE_URL
    api_key = s.PROFESSIONALIZE_API_KEY or s.llm_api_key or ""
    if not base_url:
        raise RuntimeError("PROFESSIONALIZE_BASE_URL is not set, but required for custom LLM.")

    client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    set_default_openai_client(client)

    return s.PROFESSIONALIZE_LLM_MODEL

def _configure_agents_llm() -> Optional[str]:
    s = load_settings()

    if not s.PROFESSIONALIZE_BASE_URL:
        raise RuntimeError("PROFESSIONALIZE_BASE_URL is required for LiteLLM.")

    # Many providers don't support Responses API; switch to Chat Completions. :contentReference[oaicite:5]{index=5}
    if s.openai_api_style.strip().lower() == "chat_completions":
        set_default_openai_api("chat_completions")

    # Ensure Agents SDK uses your base_url client (and optionally for tracing too). :contentReference[oaicite:6]{index=6}
    client = AsyncOpenAI(
        base_url=s.PROFESSIONALIZE_BASE_URL,
        api_key=s.any_api_key or "",
    )
    set_default_openai_client(client, use_for_tracing=True)

    # If you disable tracing in env, disable it in-process too (belt + suspenders). :contentReference[oaicite:7]{index=7}
    if (os.getenv("OPENAI_AGENTS_DISABLE_TRACING") or "").strip() == "1":
        set_tracing_disabled(True)

    # Let build_agents() set model explicitly for consistency
    return s.PROFESSIONALIZE_LLM_MODEL


def run_sync(args: RunArgs) -> str:
    init_service(config_dir=args.config_dir, cache_dir=args.cache_dir, output_dir=args.output_dir)

    model = _configure_agents_llm()
    orchestrator = build_agents(model=model)

    prompt = f"Run Content Gap Analyzer for blog={args.blog}"
    if args.product:
        prompt += f", product={args.product}"
    if args.platform:
        prompt += f", platform={args.platform}"
    if args.flush:
        prompt += ", flush=true"

    result = Runner.run_sync(orchestrator, prompt)
    return str(result.final_output)