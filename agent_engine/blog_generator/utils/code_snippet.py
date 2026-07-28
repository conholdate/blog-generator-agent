"""
Standalone code-snippet generation step.

Generates the ONE piece of code the rest of the post is built around,
before the main writer prompt runs. Kept separate from the writer so the
source of code can later be swapped (e.g. for a verified/sandboxed
snippet) without touching the writer prompt or layouts.
"""
from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Optional

from services.LLMservice import llm_service
from utils.prompts import get_code_snippet_prompt

_CODE_BLOCK_RE = re.compile(r"```(\w+)?\s*\n(.*?)```", re.DOTALL)


def _parse_snippet(text: str) -> Optional[Dict[str, str]]:
    match = _CODE_BLOCK_RE.search(text or "")
    if not match:
        return None
    code = match.group(2).strip()
    if not code:
        return None
    language = (match.group(1) or "").strip()
    return {"language": language or "text", "code": code}


async def generate_code_snippet(
    topic: str,
    primary_keyword: str,
    platform: str,
    context: str,
    outline: Optional[List[str]] = None,
    is_cloud: bool = False,
    max_retries: int = 3,
    metrics=None,
) -> Optional[Dict[str, str]]:
    """
    Generate the single source-of-truth code snippet for a post.

    Retries up to `max_retries` times on API failure OR on a response that
    doesn't contain a parseable fenced code block. Returns None only after
    every attempt is exhausted - callers must abort on None, not fall back
    to inventing code elsewhere in the pipeline.
    """
    prompt = get_code_snippet_prompt(
        topic=topic,
        primary_keyword=primary_keyword,
        platform=platform,
        context=context,
        outline=outline or [],
        is_cloud=is_cloud,
    )

    total_input_tokens = 0
    total_output_tokens = 0
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            text, token_usage = await llm_service.complete(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000,
            )
            total_input_tokens += token_usage.get("input_tokens", 0)
            total_output_tokens += token_usage.get("output_tokens", 0)

            snippet = _parse_snippet(text)
            if snippet:
                if metrics:
                    metrics.record_llm_usage(
                        input_tokens=total_input_tokens,
                        output_tokens=total_output_tokens,
                        caller="code-snippet-agent",
                    )
                print(
                    f"✅ Code snippet generated on attempt {attempt}/{max_retries} "
                    f"({snippet['language']}, {len(snippet['code'].splitlines())} lines)",
                    flush=True,
                )
                return snippet

            last_error = "response did not contain a parseable code block"

        except Exception as e:
            last_error = str(e)

        print(f"⚠️ Code snippet attempt {attempt}/{max_retries} failed: {last_error}", flush=True)
        if attempt < max_retries:
            await asyncio.sleep(2 ** attempt)

    if metrics and (total_input_tokens or total_output_tokens):
        metrics.record_llm_usage(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            caller="code-snippet-agent",
        )

    print(f"❌ Code snippet generation failed after {max_retries} attempts. Last error: {last_error}", flush=True)
    return None
