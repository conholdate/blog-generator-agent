# src/agents/kra/tools/seo_title_polisher.py
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_default_openai_api, set_tracing_disabled

from agent_engine.blog_keyword_analyzer.config import settings
from agent_engine.blog_keyword_analyzer.prompt_loader import load_prompt
from agent_engine.blog_keyword_analyzer.tools.normalization import contains_platform_variant, platform_variant_pattern

log = logging.getLogger("kra.seo_title_polisher")

# ----------------------------
# Request / config
# ----------------------------
@dataclass(frozen=True)
class SeoTitlePolishRequest:
    raw_title: str
    primary_keyword: str
    supporting_keywords: List[str]
    platform_label: Optional[str]
    product: str
    include_product_in_title: bool
    min_len: int = 40
    max_len: int = 60


# ----------------------------
# Agents SDK bootstrap
# ----------------------------
def _configure_agents_sdk() -> None:
    """
    Make Agents SDK use the same OpenAI-compatible backend you already use.
    Mirrors the existing LLM keyword generator agent bootstrap.
    """
    client = AsyncOpenAI(
        base_url=settings.PROFESSIONALIZE_BASE_URL,
        api_key=settings.PROFESSIONALIZE_API_KEY,
    )
    set_default_openai_client(client)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)


_configure_agents_sdk()

# ----------------------------
# Agent definition
# ----------------------------
_TITLE_POLISHER_AGENT = Agent(
    name="kra-title-polisher",
    instructions=load_prompt("seo_title_polisher_instructions.txt"),
    model=settings.PROFESSIONALIZE_LLM_MODEL,
)

# ----------------------------
# Utilities
# ----------------------------
_WS = re.compile(r"\s+")
_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")

def _clean(s: str) -> str:
    return _WS.sub(" ", (s or "").strip())

def _extract_json_obj(text: str) -> Optional[Dict[str, Any]]:
    """
    Robust JSON object extraction:
    - accepts plain JSON
    - accepts fenced ```json
    - extracts first {...} block if extra text exists
    """
    t = (text or "").strip()
    if not t:
        return None

    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```$", "", t).strip()

    # Try direct parse
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    m = _JSON_OBJ_RE.search(t)
    if not m:
        return None

    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None

def _platform_suffix_ok(title: str, platform_label: Optional[str]) -> bool:
    if not platform_label:
        return True
    return contains_platform_variant(title, platform_label)

def _contains_verbatim(haystack: str, needle: str) -> bool:
    return bool(needle) and (needle in (haystack or ""))

def _too_many_platform_mentions(title: str, platform_label: Optional[str]) -> bool:
    if not platform_label:
        return False
    pattern = platform_variant_pattern(platform_label)
    if not pattern:
        return False
    return len(re.findall(rf"(?i){pattern}", title)) > 1

def _has_duplicate_verb(title: str) -> bool:
    # catches "Convert Convert", "Generate Generate", etc.
    return bool(re.search(r"(?i)\b(convert|generate|create|build|export|render|merge|split)\s+\1\b", title))

# ----------------------------
# Public API
# ----------------------------
def polish_title(req: SeoTitlePolishRequest) -> Optional[str]:
    """
    Returns a polished title if it passes HARD validation; otherwise None.
    Caller should fallback to deterministic title.
    """
    raw_title = _clean(req.raw_title)
    pk = _clean(req.primary_keyword)
    if not raw_title or not pk:
        return None

    payload = {
        "raw_title": raw_title,
        "primary_keyword": pk,
        "supporting_keywords": [k for k in (req.supporting_keywords or []) if isinstance(k, str) and k.strip()][:8],
        "platform_label": req.platform_label,
        "product": (req.product or "").strip(),
        "include_product_in_title": bool(req.include_product_in_title),
        "min_len": int(req.min_len),
        "max_len": int(req.max_len),
        "output_format": "JSON object with title/confidence/notes only",
    }

    res = Runner.run_sync(_TITLE_POLISHER_AGENT, json.dumps(payload, ensure_ascii=False))
    raw_out = (res.final_output or "").strip()

    obj = _extract_json_obj(raw_out)
    if not obj:
        log.warning("Title polisher returned non-JSON. Raw:\n%s", raw_out)
        return None

    title = _clean(str(obj.get("title", "") or ""))
    if not title:
        return None

    # ----------------------------
    # HARD VALIDATION
    # ----------------------------
    if _has_duplicate_verb(title):
        return None

    if not _contains_verbatim(title, pk):
        return None

    if req.platform_label:
        if not _platform_suffix_ok(title, req.platform_label):
            return None
        if _too_many_platform_mentions(title, req.platform_label):
            return None

    prod = (req.product or "").strip()
    if prod:
        if req.include_product_in_title and not _contains_verbatim(title, prod):
            return None
        if (not req.include_product_in_title) and _contains_verbatim(title, prod):
            return None

    # Length preference (not hard fail; caller can clamp/normalize again)
    # But reject extreme outputs.
    if len(title) < 15 or len(title) > 120:
        return None

    return title
