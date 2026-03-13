from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, List, Optional

from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)

from agent_engine.blog_keyword_analyzer.config import settings
from agent_engine.blog_keyword_analyzer.tools.normalization import (
    normalize_display_text,
    normalize_platform_mentions,
)
from agent_engine.blog_keyword_analyzer.schemas import KeywordRecord


@dataclass(frozen=True)
class LLMKeywordGenRequest:
    topic: str
    product: str
    platform: Optional[str] = None
    locale: str = "en-US"
    max_keywords: int = 50


_WHITESPACE = re.compile(r"\s+")
_BAD_CHARS = re.compile(r"[\u2022\u00b7\u2026]")
_DISALLOWED_PUNCT = re.compile(r"[\"'`()\[\]{}<>|]")
_MULTI_PUNCT = re.compile(r"[,:;.!?]+$")
_TOKEN_RE = re.compile(r"[a-z0-9.+#]+")

_MIN_WORDS = 3
_MAX_WORDS = 12
_MAX_CHARS = 90
_STOPWORDS = {
    "a", "an", "and", "api", "best", "by", "file", "files", "for", "from", "guide",
    "how", "in", "into", "of", "on", "or", "the", "to", "tutorial", "using", "with",
}
_BRAND_TOKENS = {"aspose", "groupdocs", "conholdate", "adobe", "acrobat"}
_ENDING_VERBS = {"add", "edit", "replace", "update", "convert", "render", "save", "merge", "split"}


def _configure_agents_sdk() -> None:
    client = AsyncOpenAI(
        base_url=settings.PROFESSIONALIZE_BASE_URL,
        api_key=settings.PROFESSIONALIZE_API_KEY,
    )
    set_default_openai_client(client)
    set_default_openai_api("chat_completions")
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
        allow.add(p)

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


def _product_brand_tokens(product: str) -> set[str]:
    return set(_TOKEN_RE.findall((product or "").lower()))


def _topic_anchor_tokens(topic: str) -> set[str]:
    tokens = set()
    for token in _TOKEN_RE.findall((topic or "").lower()):
        if len(token) <= 1 or token in _STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _mentions_unrelated_brand(phrase: str, product: str) -> bool:
    phrase_tokens = set(_TOKEN_RE.findall((phrase or "").lower()))
    allowed = _product_brand_tokens(product)
    for brand in _BRAND_TOKENS:
        if brand in phrase_tokens and brand not in allowed:
            return True
    return False


def _is_relevant_phrase(phrase: str, topic: str, product: str) -> bool:
    phrase_tokens = set(_TOKEN_RE.findall((phrase or "").lower()))
    if not phrase_tokens:
        return False
    if _mentions_unrelated_brand(phrase, product):
        return False

    anchors = _topic_anchor_tokens(topic)
    if not anchors:
        return True

    # Require direct overlap with the topic feature/action/format terms.
    if phrase_tokens.intersection(anchors):
        return True

    return False


def _strip_product_noise(phrase: str, product: str) -> str:
    out = phrase
    variants = {product, product.replace(".", " "), product.replace(" ", ".")}
    for v in variants:
        v = (v or "").strip()
        if not v:
            continue
        out = re.sub(rf"(?i)(?<!\w){re.escape(v)}(?!\w)", " ", out)
    out = re.sub(r"(?i)\bcloud\s+sdk\b", " ", out)
    out = re.sub(r"(?i)\bsdk\b", " ", out)
    out = re.sub(r"(?i)\bcloud\b", " ", out)
    out = re.sub(r"(?i)\bapi\b", " ", out)
    return re.sub(r"\s{2,}", " ", out).strip()

def _normalize_action_phrases(phrase: str) -> str:
    out = phrase
    replacements = [
        (r"(?i)\btext replace\b", "replace text"),
        (r"(?i)\bslide add\b", "add slide"),
        (r"(?i)\bslides add\b", "add slides"),
        (r"(?i)\bfile update\b", "update file"),
        (r"(?i)\bpptx update\b", "update PPTX"),
        (r"(?i)\bpptx edit\b", "edit PPTX"),
        (r"(?i)\bpptx convert\b", "convert PPTX"),
    ]
    for pattern, repl in replacements:
        out = re.sub(pattern, repl, out)
    return re.sub(r"\s{2,}", " ", out).strip()


def _collapse_duplicate_words(phrase: str) -> str:
    words = phrase.split()
    if not words:
        return ""
    collapsed = [words[0]]
    for word in words[1:]:
        if word.lower() == collapsed[-1].lower():
            continue
        collapsed.append(word)
    out = " ".join(collapsed)
    out = re.sub(r"(?i)\b(\.net)\s+in\s+\1\b", r"\1", out)
    out = re.sub(r"(?i)\bin\s+(\.net)\s+in\s+\1\b", r"in \1", out)
    return out.strip()


def _looks_malformed(phrase: str) -> bool:
    low = phrase.lower()
    if re.search(r"(?i)\bwith in\b|\bin in\b", low):
        return True
    if low.count(".net") > 1 or low.count("node.js") > 1 or low.count("c++") > 1:
        return True
    tokens = _TOKEN_RE.findall(low)
    if tokens and tokens[-1] in _ENDING_VERBS:
        return True
    if re.search(r"(?i)\b(powerpoint|pptx|text|slide|file)\s+(add|edit|replace|update|convert)\b", low):
        return True
    return False


def _sanitize_phrase(phrase: str, topic: str, product: str, platform: Optional[str]) -> str:
    out = _clean_phrase(phrase)
    out = _strip_product_noise(out, product)
    out = _normalize_action_phrases(out)
    out = normalize_platform_mentions(out, platform)
    out = _collapse_duplicate_words(out)
    out = re.sub(r"\s{2,}", " ", out).strip(" -,:;")
    if _looks_malformed(out):
        return ""
    if not _is_relevant_phrase(out, topic, product):
        return ""
    return normalize_display_text(out)


def _extract_json_payload(raw_text: str) -> Any:
    txt = (raw_text or "").strip()
    if not txt:
        return None

    if txt.startswith("```"):
        txt = re.sub(r"^```(?:json)?\s*", "", txt, flags=re.IGNORECASE)
        txt = re.sub(r"\s*```$", "", txt).strip()

    try:
        return json.loads(txt)
    except Exception:
        pass

    obj_match = re.search(r"\{[\s\S]*\}", txt)
    if obj_match:
        try:
            return json.loads(obj_match.group(0).strip())
        except Exception:
            pass

    list_match = re.search(r"\[[\s\S]*\]", txt)
    if list_match:
        try:
            return json.loads(list_match.group(0).strip())
        except Exception:
            pass

    return None


def _collect_phrases_from_payload(payload: Any) -> List[str]:
    if isinstance(payload, list):
        return [str(x) for x in payload]

    if not isinstance(payload, dict):
        return []

    phrases: List[str] = []

    primary = payload.get("primary_keyword")
    if isinstance(primary, str) and primary.strip():
        phrases.append(primary)

    keyword_groups = payload.get("keyword_groups")
    if isinstance(keyword_groups, dict):
        for key in ("core_seo_keywords", "long_tail_keywords", "context_keywords"):
            values = keyword_groups.get(key) or []
            if isinstance(values, list):
                phrases.extend(str(v) for v in values if isinstance(v, str))

    supporting = payload.get("supporting_keywords")
    if isinstance(supporting, list):
        phrases.extend(str(v) for v in supporting if isinstance(v, str))

    return phrases


_configure_agents_sdk()
_KEYWORD_GEN_AGENT = Agent(
    name="kra-keyword-gen",
    instructions=(
        "You generate only the best possible relevant SEO keyword phrases for technical content.\n"
        "Return ONLY valid JSON.\n\n"
        "Primary objective:\n"
        "- Highlight the feature/topic first so it attracts broad relevant visitors, especially platform developers and AI agents that collect and rank content.\n"
        "Secondary objective:\n"
        "- Show that the given product provides that feature.\n\n"
        "Return a JSON array of keyword strings only.\n\n"
        "Rules:\n"
        "- Output MUST be a JSON array of strings.\n"
        "- Generate only concise keyword phrases, not personas, angles, outlines, or notes.\n"
        "- Every keyword must be directly relevant to the given topic.\n"
        "- Every keyword must stay feature-first and topic-first, not product-first.\n"
        "- Include the product only when it helps clarify the feature, not as filler.\n"
        "- Avoid competitor names, unrelated brands, subscriptions, pricing terms, and irrelevant software.\n"
        "- If a platform is provided, keywords must be platform-specific and must NOT mention other platforms.\n"
        "- Prefer phrases that include the action, file format, or core feature from the topic.\n"
        "- Generate only the strongest relevant SEO phrases a technical writer would actually target.\n"
        "- Avoid vague phrases, generic brand terms, and off-topic software queries.\n"
        "- No markdown fences. No commentary outside JSON.\n"
    ),
    model=settings.PROFESSIONALIZE_LLM_MODEL,
)


def fetch_llm_keywords(req: LLMKeywordGenRequest) -> List[KeywordRecord]:
    import logging

    log = logging.getLogger("kra.llm_keyword_gen")

    def _run(prompt_obj: dict) -> str:
        res = Runner.run_sync(_KEYWORD_GEN_AGENT, json.dumps(prompt_obj, ensure_ascii=False))
        return (res.final_output or "").strip()

    def _generate(prompt_obj: dict, platform_for_filter: Optional[str]) -> List[KeywordRecord]:
        raw = _run(prompt_obj)
        payload = _extract_json_payload(raw)
        phrases = _collect_phrases_from_payload(payload)

        if not phrases:
            log.warning("LLM returned non-parseable or empty output. Raw output:\n%s", raw)

        cleaned: List[str] = []
        for s in phrases:
            s2 = _sanitize_phrase(s, req.topic, req.product, platform_for_filter)
            if not _is_acceptable(s2):
                continue
            if _platform_contamination(s2, platform_for_filter):
                continue
            cleaned.append(s2)

        cleaned = _dedupe(cleaned)[: prompt_obj.get("max_keywords", req.max_keywords)]

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
        "output_format": "JSON array of keyword strings only",
    }

    records = _generate(prompt, platform_for_filter=req.platform)

    if not records and req.platform:
        log.info("Retrying LLM keyword gen without platform constraint (was: %s)", req.platform)
        prompt2 = dict(prompt)
        prompt2["platform"] = None
        records = _generate(prompt2, platform_for_filter=None)

    return records


if __name__ == "__main__":
    req = LLMKeywordGenRequest(
        topic="LaTeX to PNG in Python",
        product="Aspose.Tex",
        platform="python",
        locale="en-US",
        max_keywords=20,
    )
    kws = fetch_llm_keywords(req)
    for k in kws[:10]:
        print("-", k.keyword)
