# src/agents/kra/tools/llm_keyword_gen.py
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional

from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)

from agent_engine.blog_keyword_analyzer.config import settings
from agent_engine.blog_keyword_analyzer.schemas import KeywordRecord


# ----------------------------
# Request / config
# ----------------------------
@dataclass(frozen=True)
class LLMKeywordGenRequest:
    topic: str
    product: str
    platform: Optional[str] = None
    locale: str = "en-US"
    max_keywords: int = 50


# ----------------------------
# Sanitization utilities
# ----------------------------
_WHITESPACE = re.compile(r"\s+")
_BAD_CHARS = re.compile(r"[•·\u2026]")  # bullets, middle-dot, ellipsis char
_DISALLOWED_PUNCT = re.compile(r"[\"'`()\[\]{}<>|]")
_MULTI_PUNCT = re.compile(r"[,:;.!?]+$")

# Keep it tight; these can match your scoring expectations
_MIN_WORDS = 3
_MAX_WORDS = 12
_MAX_CHARS = 90

def _configure_agents_sdk() -> None:
    """
    Make the Agents SDK use our OpenAI-compatible backend instead of requiring OPENAI_API_KEY.
    """
    # Use your custom OpenAI-compatible endpoint
    client = AsyncOpenAI(
        base_url=settings.PROFESSIONALIZE_BASE_URL,
        api_key=settings.PROFESSIONALIZE_API_KEY,
    )
    set_default_openai_client(client)  # global default for Runner/Agents :contentReference[oaicite:1]{index=1}

    # Many non-OpenAI providers don't support the Responses API yet
    # Switch Agents SDK to Chat Completions if needed. :contentReference[oaicite:2]{index=2}
    set_default_openai_api("chat_completions")

    # If you don't have a real OpenAI key for tracing, disable tracing to avoid 401s. :contentReference[oaicite:3]{index=3}
    set_tracing_disabled(True)



def _clean_phrase(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""

    s = s.replace("&", " and ")
    s = _BAD_CHARS.sub(" ", s)
    s = _DISALLOWED_PUNCT.sub(" ", s)
    s = _WHITESPACE.sub(" ", s).strip()
    s = _MULTI_PUNCT.sub("", s).strip()
    return s


def _platform_contamination(phrase: str, platform: Optional[str]) -> bool:
    """
    If platform is specified, drop phrases that mention other platforms.
    Tune this list to match your taxonomy.
    """
    if not platform:
        return False

    p = platform.strip().lower()
    t = phrase.lower()

    other_tokens = [
        ".net", "dotnet", "c#", "csharp",
        "c++", "cpp",
        "python",
        "node", "node.js", "javascript", "typescript",
        "php",
        "ruby",
        "golang",
    ]

    # allow selected platform token(s)
    allow = set()
    if p == "java":
        allow.update(["java", "jvm"])
    elif p == "net":
        allow.update([".net", "dotnet", "c#", "csharp"])
    elif p in ("cpp", "c++"):
        allow.update(["c++", "cpp"])
    elif p == "python":
        allow.update(["python"])
    elif p == "node":
        allow.update(["node", "node.js", "javascript", "typescript"])
    else:
        allow.update([p])

    for tok in other_tokens:
        if tok in allow:
            continue
        if tok in t:
            return True

    return False


def _is_acceptable(phrase: str) -> bool:
    if not phrase:
        return False
    if len(phrase) > _MAX_CHARS:
        return False
    wc = len(phrase.split())
    if wc < _MIN_WORDS or wc > _MAX_WORDS:
        return False
    return True


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for s in items:
        k = s.lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


# ----------------------------
# Agent + generator
# ----------------------------

_configure_agents_sdk()
_KEYWORD_GEN_AGENT = Agent(
    name="kra-keyword-gen",
    instructions=(
        "You generate SEO keyword phrases for technical content.\n"
        "Return ONLY valid JSON.\n\n"
        "Rules:\n"
        "- Output MUST be a JSON array of strings.\n"
        "- Each string is a short keyword phrase (3–12 words, <= 90 chars).\n"
        "- No bullets, no ellipses, no step lists, no trailing punctuation.\n"
        "- Must be relevant to the given product + topic.\n"
        "- If a platform is provided, keywords must be platform-specific and must NOT mention other platforms.\n"
        "- Generate diverse variants: how-to, convert, render, export, save, example, tutorial.\n"
        "- Avoid duplicates.\n"
    ),
    model=settings.PROFESSIONALIZE_LLM_MODEL,  # your model name (e.g., "gpt-oss")
    # You can set model explicitly if you want; leaving default uses your SDK default config.
    # model="gpt-5.2",
)

def fetch_llm_keywords(req: LLMKeywordGenRequest) -> List[KeywordRecord]:
    """
    LLM fallback keyword generator using OpenAI Agents SDK.
    Returns KeywordRecord list with source='llm'.

    Improvements:
    - Robust JSON extraction (handles code fences / extra prose).
    - Logs raw output on parse failure (so you can see why you got []).
    - Optional one retry without platform if platform-filtering nukes everything.
    """
    import logging

    log = logging.getLogger("kra.llm_keyword_gen")

    def _run(prompt_obj: dict) -> str:
        res = Runner.run_sync(_KEYWORD_GEN_AGENT, json.dumps(prompt_obj, ensure_ascii=False))
        return ((res.final_output or "").strip())

    def _extract_json_list(raw_text: str) -> List[str]:
        """
        Accepts:
          - a real JSON array
          - ```json ... ``` fenced blocks
          - extra text around a JSON array (extract first [...] block)
        """
        txt = (raw_text or "").strip()
        if not txt:
            return []

        # Strip fenced code blocks if present
        if txt.startswith("```"):
            # remove leading/trailing fences; keep inner
            txt = re.sub(r"^```(?:json)?\s*", "", txt, flags=re.IGNORECASE)
            txt = re.sub(r"\s*```$", "", txt).strip()

        # First try: direct JSON parse
        try:
            data = json.loads(txt)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            pass

        # Second try: extract the first JSON-array-looking block
        m = re.search(r"\[[\s\S]*\]", txt)
        if not m:
            return []

        candidate = m.group(0).strip()
        try:
            data = json.loads(candidate)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            return []

        return []

    def _generate(prompt_obj: dict, platform_for_filter: Optional[str]) -> List[KeywordRecord]:
        raw = _run(prompt_obj)

        phrases = _extract_json_list(raw)
        if not phrases:
            # This is the key: you were seeing [] with no clue why.
            log.warning("LLM returned non-parseable or empty output. Raw output:\n%s", raw)

        cleaned: List[str] = []
        for s in phrases:
            s2 = _clean_phrase(s)
            if not _is_acceptable(s2):
                continue
            if _platform_contamination(s2, platform_for_filter):
                continue
            cleaned.append(s2)

        cleaned = _dedupe(cleaned)[: prompt_obj.get("max_keywords", req.max_keywords)]
        print(cleaned)

        return [
            KeywordRecord(
                keyword=kw,
                source="llm",
                locale=req.locale,
                volume=None,
                cpc=None,
                kd=None,
                clicks=None,
                url=None,
                competition=None,
                competition_label=None,
            )
            for kw in cleaned
        ]

    prompt = {
        "topic": req.topic,
        "product": req.product,
        "platform": req.platform,
        "locale": req.locale,
        "max_keywords": req.max_keywords,
        "output_format": "JSON array of strings only",
    }

    # Attempt 1: as requested
    records = _generate(prompt, platform_for_filter=req.platform)

    # Attempt 2 (optional): if platform filtering / constraints resulted in nothing, retry once without platform
    if not records and req.platform:
        log.info("Retrying LLM keyword gen without platform constraint (was: %s)", req.platform)
        prompt2 = dict(prompt)
        prompt2["platform"] = None
        records = _generate(prompt2, platform_for_filter=None)

    return records

# ----------------------------
# Example (manual run)
# ----------------------------
if __name__ == "__main__":
    req = LLMKeywordGenRequest(
        topic="LaTeX to PNG in Pytho",
        product="Aspose.Tex",
        platform="python",
        locale="en-US",
        max_keywords=20,
    )
    kws = fetch_llm_keywords(req)
    for k in kws[:10]:
        print("-", k.keyword)
