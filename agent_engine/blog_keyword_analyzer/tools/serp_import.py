# src/agents/kra/tools/serp_import.py
from __future__ import annotations

import re
from typing import Iterable, List, Optional, Tuple

import requests

from ..config import settings
from agent_engine.blog_keyword_analyzer.tools.normalization import normalize_display_text, normalize_platform_mentions
from ..schemas import KeywordRecord


# ----------------------------
# Locale helpers
# ----------------------------
def _locale_to_hl_gl(locale: str) -> Tuple[str, str]:
    """
    Convert a BCP-47-ish locale like 'en-US' to SerpAPI's hl/gl.
    Fallbacks are reasonable defaults.
    """
    if not locale:
        return "en", "us"

    parts = re.split(r"[-_]", locale)
    if len(parts) == 1:
        return parts[0].lower(), "us"
    hl = parts[0].lower()
    gl = parts[1].lower()
    return hl, gl


# ----------------------------
# Keyword shaping & cleanup
# ----------------------------
_BULLET_SEPARATORS = re.compile(r"[\u00b7•|]+")  # · • |
_SENTENCE_SPLIT = re.compile(r"[.!?؛;:\n]+")
_WHITESPACE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9.+#]+")
# Common “noise” suffixes seen in SERP snippets/titles (tune over time)
_NOISE_SUFFIX = re.compile(
    r"""
    (?:
        high[-\s]?quality .* |
        simple code examples? .* |
        step[-\s]?by[-\s]?step .* |
        please follow the steps .* |
        call the .* method .* |
        load .* file .* |
        create an instance .* |
        iterate through .* |
        write .* to .* |
        via \w+ .* |
        \.\.\.+
    )$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Reject very short or very long phrases (tune thresholds to your scoring pipeline)
_MIN_WORDS = 3
_MAX_WORDS = 14
_MAX_CHARS = 120
_STOPWORDS = {
    "a", "an", "and", "api", "best", "by", "file", "files", "for", "from", "guide",
    "how", "in", "into", "of", "on", "or", "the", "to", "tutorial", "using", "with",
}
_BRAND_TOKENS = {"aspose", "groupdocs", "conholdate", "adobe", "acrobat"}
_ENDING_VERBS = {"add", "edit", "replace", "update", "convert", "render", "save", "merge", "split"}


def _clean_text(s: str) -> str:
    """
    Normalize common SERP text artifacts:
    - remove ellipsis
    - collapse whitespace
    - remove stray & (usually from "A & B" headings) by spacing it
    - strip quotes/brackets noise
    """
    if not s:
        return ""

    s = s.replace("\u2026", "...")  # unicode ellipsis -> "..."
    s = s.replace("...", " ")
    s = s.replace("&", " and ")
    s = s.replace("·", " ")
    s = s.replace("•", " ")
    s = re.sub(r"[\[\]\(\)\"“”‘’]+", " ", s)
    s = re.sub(r"\s*[-–—]\s*", " - ", s)  # normalize dashes
    s = _WHITESPACE.sub(" ", s).strip()
    return s


def _trim_noise_suffix(s: str) -> str:
    """
    Remove trailing marketing/step-list boilerplate when present.
    """
    s = s.strip()
    s = _NOISE_SUFFIX.sub("", s).strip()
    return s


def _extract_phrases(text: str) -> List[str]:
    """
    Turn long SERP snippets/questions into smaller keyword-like phrases.
    Heuristics:
      - split by bullets (· • |)
      - split by sentence punctuation
      - keep phrase length within configured bounds
    """
    if not text:
        return []

    text = _clean_text(text)

    # Split on bullet-like separators first
    parts: List[str] = []
    for chunk in _BULLET_SEPARATORS.split(text):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts.extend([p.strip() for p in _SENTENCE_SPLIT.split(chunk) if p.strip()])

    out: List[str] = []
    for p in parts:
        p = _trim_noise_suffix(p)
        p = _clean_text(p)

        if not p:
            continue

        # Drop if it's basically a “how-to step chain” with many "·" remnants, etc.
        # Also trim long fragments
        if len(p) > _MAX_CHARS:
            p = p[:_MAX_CHARS].rsplit(" ", 1)[0].strip()

        word_count = len(p.split())
        if word_count < _MIN_WORDS or word_count > _MAX_WORDS:
            continue

        out.append(p)

    return out


# ----------------------------
# Platform scoping
# ----------------------------
_PLATFORM_ALIASES = {
    "net": [r"\.net", r"dotnet", r"c#", r"csharp"],
    "java": [r"\bjava\b", r"\bjvm\b"],
    "cpp": [r"c\+\+", r"\bcpp\b"],
    "python": [r"\bpython\b"],
    "node": [r"\bnode\.?js\b", r"\bjavascript\b", r"\btypescript\b"],
    "php": [r"\bphp\b"],
    "ruby": [r"\bruby\b"],
    "go": [r"\bgolang\b", r"\bgo\b"],
}

# If platform is X, reject phrases mentioning ANY of these other-platform tokens.
# You can extend this list if you see frequent contamination.
_OTHER_PLATFORM_TOKENS = [
    r"\.net", r"dotnet", r"c#", r"csharp",
    r"c\+\+", r"\bcpp\b",
    r"\bpython\b",
    r"\bnode\.?js\b", r"\bjavascript\b", r"\btypescript\b",
    r"\bphp\b",
    r"\bruby\b",
    r"\bgolang\b",
]


def _platform_positive_term(platform: str) -> str:
    """
    What we add to the query to bias intent.
    """
    p = (platform or "").strip().lower()
    if not p:
        return ""

    # Use natural phrasing that tends to work well in Google queries.
    if p == "net":
        return "for .NET"
    if p == "cpp":
        return "for C++"
    if p == "node":
        return "for Node.js"
    return f"for {p.capitalize()}"


def _platform_negative_terms(platform: str) -> List[str]:
    """
    What we exclude from the query. Google supports '-' negation terms.
    """
    p = (platform or "").strip().lower()
    if not p:
        return []

    negatives = []
    for token in _OTHER_PLATFORM_TOKENS:
        # If the token matches the selected platform, skip it.
        # (e.g., platform=java should not exclude java)
        if p == "java" and re.search(r"\bjava\b", token, re.IGNORECASE):
            continue
        if p == "net" and (".net" in token or "dotnet" in token or "c#" in token or "csharp" in token):
            continue
        if p == "cpp" and ("c\\+\\+" in token or "cpp" in token):
            continue
        if p == "python" and "python" in token:
            continue
        if p == "node" and ("node" in token or "javascript" in token or "typescript" in token):
            continue
        if p == "php" and "php" in token:
            continue
        if p == "ruby" and "ruby" in token:
            continue
        if p == "go" and ("golang" in token or r"\bgo\b" in token):
            continue

        # Convert regex-ish tokens into reasonable query negatives
        # Keep it simple and pragmatic:
        negatives.append(token.replace(r"\b", "").replace("\\", ""))
    return negatives


def _phrase_mentions_other_platform(phrase: str, platform: str) -> bool:
    """
    Strict post-filter: if platform is specified, drop phrases that mention
    other platforms.
    """
    p = (platform or "").strip().lower()
    if not p:
        return False

    txt = phrase.lower()

    # Allow mentions of the selected platform; reject others.
    # We use simple substring/regex checks.
    # If platform is java, any mention of .net/c#/c++/python/node/php/etc => reject.
    if p == "java":
        return bool(re.search(r"(\.net|c#|csharp|c\+\+|\bpython\b|\bnode\b|\bnode\.js\b|\bphp\b|\bruby\b|\bgolang\b)", txt))
    if p == "net":
        return bool(re.search(r"(\bjava\b|c\+\+|\bcpp\b|\bpython\b|\bnode\b|\bnode\.js\b|\bphp\b|\bruby\b|\bgolang\b)", txt))
    if p == "cpp":
        return bool(re.search(r"(\bjava\b|\.net|c#|csharp|\bpython\b|\bnode\b|\bnode\.js\b|\bphp\b|\bruby\b|\bgolang\b)", txt))
    if p == "python":
        return bool(re.search(r"(\bjava\b|\.net|c#|csharp|c\+\+|\bcpp\b|\bnode\b|\bnode\.js\b|\bphp\b|\bruby\b|\bgolang\b)", txt))
    if p == "node":
        return bool(re.search(r"(\bjava\b|\.net|c#|csharp|c\+\+|\bcpp\b|\bpython\b|\bphp\b|\bruby\b|\bgolang\b)", txt))
    if p == "php":
        return bool(re.search(r"(\bjava\b|\.net|c#|csharp|c\+\+|\bcpp\b|\bpython\b|\bnode\b|\bnode\.js\b|\bruby\b|\bgolang\b)", txt))
    if p == "ruby":
        return bool(re.search(r"(\bjava\b|\.net|c#|csharp|c\+\+|\bcpp\b|\bpython\b|\bnode\b|\bnode\.js\b|\bphp\b|\bgolang\b)", txt))
    if p == "go":
        return bool(re.search(r"(\bjava\b|\.net|c#|csharp|c\+\+|\bcpp\b|\bpython\b|\bnode\b|\bnode\.js\b|\bphp\b|\bruby\b)", txt))

    return False


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for s in items:
        key = s.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(s.strip())
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

    return bool(phrase_tokens.intersection(anchors))


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
    out = _clean_text(phrase)
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


# ----------------------------
# Main fetch
# ----------------------------
def fetch_serp_keywords(
    topic: str,
    product: str,
    platform: Optional[str] = None,  # <-- add platform
    locale: str = "en-US",
    max_keywords: int = 50,
) -> List[KeywordRecord]:
    """
    Use SerpAPI to pull search-intent-enriched keyword phrases from Google SERPs.

    Improvements vs previous version:
      - Extract phrases (not entire snippets)
      - Clean artifacts like '&', '...', '·'
      - Platform scoping in query + strict post-filter
    """
    if not settings.SERPAPI_KEY:
        return []

    hl, gl = _locale_to_hl_gl(locale)

    platform_term = _platform_positive_term(platform or "")
    negatives = _platform_negative_terms(platform or "")

    base_query = f"{product} {topic}".strip()
    # Add a bias term like "for Java", and negative terms to reduce contamination.
    query_parts = [base_query]
    if platform_term:
        query_parts.append(platform_term)
    for neg in negatives:
        # Ensure it's prefixed with '-' in the Google query.
        neg = neg.strip()
        if not neg:
            continue
        if not neg.startswith("-"):
            neg = "-" + neg
        query_parts.append(neg)

    query = " ".join(query_parts).strip()

    params = {
        "engine": settings.SERPAPI_ENGINE or "google",
        "q": query,
        "hl": hl,
        "gl": gl,
        "api_key": settings.SERPAPI_KEY,
    }

    resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    candidates: List[str] = []

    # 1) Organic result titles/snippets -> phrase extraction
    for item in data.get("organic_results", []):
        title = item.get("title") or ""
        if title:
            candidates.extend(_extract_phrases(title) or [ _clean_text(title) ])

        snippet = item.get("snippet") or ""
        if snippet:
            candidates.extend(_extract_phrases(snippet))

    # 2) PAA / related questions -> phrase extraction
    for item in (data.get("related_questions", []) or data.get("people_also_ask", [])):
        question = item.get("question") or item.get("title") or ""
        if question:
            candidates.extend(_extract_phrases(question) or [_clean_text(question)])

    # 3) Related searches (already short, but still clean)
    for item in data.get("related_searches", []):
        rel = item.get("query") or item.get("title") or ""
        rel = _clean_text(rel)
        if rel:
            candidates.append(rel)

    # Cleanup + platform post-filter + dedupe
    cleaned: List[str] = []
    for c in candidates:
        c = _clean_text(c)
        c = _trim_noise_suffix(c)
        c = _sanitize_phrase(c, topic, product, platform)

        if not c:
            continue

        # Drop platform contamination
        if platform and _phrase_mentions_other_platform(c, platform):
            continue

        # Enforce reasonable size even after extraction
        if len(c) > _MAX_CHARS:
            continue
        wc = len(c.split())
        if wc < _MIN_WORDS or wc > _MAX_WORDS:
            continue

        cleaned.append(c)

    cleaned = _dedupe_preserve_order(cleaned)

    # Build KeywordRecord list
    out: List[KeywordRecord] = []
    for kw in cleaned[:max_keywords]:
        out.append(
            KeywordRecord(
                keyword=kw,
                source="serpapi",
                locale=locale,
                volume=None,
                cpc=None,
                kd=None,
                clicks=None,
                url=None,
                competition=None,
                competition_label=None,
            )
        )

    return out
