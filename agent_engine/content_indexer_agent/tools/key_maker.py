from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional
from urllib.parse import urlparse

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_MULTI_DASH_RE = re.compile(r"-+")

_SEO_TITLE_KEYS = (
    "seo_title",
    "seo-title",
    "seoTitle",
    "seotitle",
    "meta_title",
    "meta-title",
    "title_seo",
)

_PLATFORM_VALUE_RE = r"(c\#|csharp|vb\.net|vbnet|vb|\.net|dotnet|java|python|node\.js|nodejs|javascript|js|c\+\+|cpp|cplusplus|android|php|ruby|go|golang|swift|kotlin|online)"
_PLATFORM_PHRASE_RE = re.compile(
    rf"(?:^|[\s\-_]+)(?:using|in|with|for|via|on)[\s\-_]+{_PLATFORM_VALUE_RE}(?:$|[\s\-_]+)",
    re.IGNORECASE,
)
_TRAILING_PLATFORM_RE = re.compile(rf"(?:[\s\-_]+|^){_PLATFORM_VALUE_RE}$", re.IGNORECASE)
_CONVERSION_PREFIX_RE = re.compile(r"^(?:convert|export|save|transform|change)-(.+?-to-.+)$")
_LEADING_NOISE_RE = re.compile(r"^(how-to|how-do-i|tutorial|guide)-")
_LEADING_PHRASE_RE = re.compile(r"^(let-s|lets|let-us)-")
_FORMAT_FILLER_RE = re.compile(r"\b(file|files|format|formats)\b", re.IGNORECASE)
_TRAILING_NOISE_RE = re.compile(r"-(programmatically|converter|converters)$")
_CONVERSION_CORE_RE = re.compile(r"([a-z0-9]+)-to-([a-z0-9]+)")
_GENERIC_TRAILING_RE = re.compile(r"-(online|free|software|application|app|tool|tools)$")
_ACTION_ARTICLE_RE = re.compile(r"^(create|read|build|repair|merge|split|convert|export|import)-(?:a|an|the)-")
_ACTION_START_RE = re.compile(r"(create|read|build|repair|merge|split|convert|export|import)-")
_MODEL_SCENE_RE = re.compile(r"-model-scenes?$")

_UPPERCASE_FORMATS = {
    "pdf",
    "xlsx",
    "xls",
    "xlsm",
    "xltx",
    "xltm",
    "csv",
    "tsv",
    "ods",
    "doc",
    "docx",
    "dotx",
    "rtf",
    "txt",
    "html",
    "htm",
    "xml",
    "json",
    "yaml",
    "yml",
    "ppt",
    "pptx",
    "ppsx",
    "odp",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "tiff",
    "svg",
    "emf",
    "wmf",
    "epub",
    "md",
    "mhtml",
    "xps",
    "ps",
    "slsx",
    "obj",
    "stl",
    "fbx",
    "glb",
    "gltf",
    "3ds",
    "dae",
    "ply",
    "usd",
    "usdz",
}


def extract_seo_title(frontmatter: Dict[str, Any]) -> Optional[str]:
    for key in _SEO_TITLE_KEYS:
        value = frontmatter.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _slugify(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("&", " and ")
    normalized = normalized.replace("/", " ")
    normalized = _NON_ALNUM_RE.sub("-", normalized)
    normalized = _MULTI_DASH_RE.sub("-", normalized).strip("-")
    return normalized


def _strip_platform_qualifiers(text: str) -> str:
    if not text:
        return ""

    out = text
    while True:
        next_out = _PLATFORM_PHRASE_RE.sub(" ", out)
        next_out = _TRAILING_PLATFORM_RE.sub("", next_out)
        next_out = re.sub(r"\s+", " ", next_out).strip(" -_")
        if next_out == out:
            break
        out = next_out
    return out


def _normalize_candidate(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).strip()
    text = _strip_platform_qualifiers(text)
    text = _FORMAT_FILLER_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    slug = _slugify(text)
    slug = _LEADING_NOISE_RE.sub("", slug)
    slug = _LEADING_PHRASE_RE.sub("", slug)
    slug = _ACTION_ARTICLE_RE.sub(r"\1-", slug)

    action_match = _ACTION_START_RE.search(slug)
    if action_match and action_match.start() > 0:
        prefix = slug[:action_match.start()].strip("-")
        if prefix in {"3d", "model", "models", "3d-model", "3d-models"}:
            slug = slug[action_match.start():]

    match = _CONVERSION_PREFIX_RE.match(slug)
    if match:
        slug = match.group(1)

    core_match = _CONVERSION_CORE_RE.search(slug)
    if core_match:
        slug = f"{core_match.group(1)}-to-{core_match.group(2)}"

    slug = _TRAILING_NOISE_RE.sub("", slug)
    while True:
        next_slug = _GENERIC_TRAILING_RE.sub("", slug)
        if next_slug == slug:
            break
        slug = next_slug
    slug = _MODEL_SCENE_RE.sub("-model", slug)
    slug = _MULTI_DASH_RE.sub("-", slug).strip("-")
    return slug


def _extract_preserved_uppercase_terms(*values: Optional[str]) -> set[str]:
    """
    Capture likely file-format tokens already written in uppercase in the source text.
    This lets titles like "Convert OBJ to STL in Java" render as "OBJ to STL".
    """
    out: set[str] = set()
    for value in values:
        if not value:
            continue
        for token in re.findall(r"\b[A-Z0-9]{2,8}\b", value):
            lowered = token.lower()
            if lowered in {"in", "on", "to", "for", "with", "and", "or"}:
                continue
            out.add(lowered)
    return out


def _to_sentence_case(slug: str, preserve_upper: set[str]) -> str:
    words = [w for w in (slug or "").split("-") if w]
    if not words:
        return ""

    rendered = []
    for i, word in enumerate(words):
        if word in _UPPERCASE_FORMATS or word in preserve_upper:
            rendered.append(word.upper())
            continue
        if i == 0:
            rendered.append(word.capitalize())
        else:
            rendered.append(word.lower())

    return " ".join(rendered)


def _looks_too_generic(slug: str) -> bool:
    words = [w for w in (slug or "").split("-") if w]
    if not words:
        return True
    if len(words) == 1 and words[0] in {"3d", "model", "models", "scene", "file", "files"}:
        return True
    return False


def _key_from_url(url: Optional[str]) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    parts = [p for p in (parsed.path or "").split("/") if p]
    if not parts:
        return ""

    # Prefer the last slug-like path segment, but skip common archive buckets.
    for part in reversed(parts):
        token = _normalize_candidate(part)
        if token and token not in {"blog", "blogs", "article", "articles"}:
            return token
    return ""


def build_content_topic(
    *,
    title: str,
    url: Optional[str] = None,
    seo_title: Optional[str] = None,
    llm_topic: Optional[str] = None,
) -> str:
    """
    Build a short, stable topic summary for indexed content.

    Rules:
      1) Prefer deterministic sources (URL, SEO title, title) before LLM wording.
      2) Strip platform qualifiers like "in Java", "using C#", "for .NET".
      3) For conversions, drop leading verbs like "Convert" and keep only "X to Y".
      4) Render in simple sentence case with spaces.
      5) Keep detected file formats uppercase (for example "OBJ to STL", "XLSX to PDF").

    Priority:
      1) URL slug
      2) SEO title
      3) Page title
      4) LLM-proposed topic
    """
    preserve_upper = _extract_preserved_uppercase_terms(title, seo_title, url, llm_topic)

    candidates = [_key_from_url(url), seo_title, title, llm_topic]
    normalized_candidates = [_normalize_candidate(candidate or "") for candidate in candidates]

    # If the URL slug collapses to something too generic, prefer richer title-derived text.
    if normalized_candidates and _looks_too_generic(normalized_candidates[0]):
        normalized_candidates = normalized_candidates[1:] + normalized_candidates[:1]

    for normalized in normalized_candidates:
        if normalized:
            return _to_sentence_case(normalized, preserve_upper)
    return ""
