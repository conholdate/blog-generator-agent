from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

import unicodedata

from agent_engine.content_indexer_agent.tools.specs import ProductSpec

_PUNCT_RE = re.compile(r"[^\w\s]+", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)

# Remove common language/platform qualifiers so cross-platform posts match
# Examples:
#  - "using C#" / "in Java" / "with Python"
#  - "for .NET" / "for Java"
#  - "(C#)" / "[Java]"
_LANG_QUALIFIER_RE = re.compile(
    r"""
    (\(|\[)?\b
    (using|in|with|for)\s+
    (c\#|csharp|vb\.net|vbnet|vb|\.net|dotnet|java|python|node\.js|nodejs|javascript|js|c\+\+|cpp|cplusplus|android)
    \b(\)|\])?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Remove trailing standalone language tokens that often appear at end
# e.g. "... Pivot Tables C#" or "... Pivot Tables Java"
_TRAILING_LANG_TOKEN_RE = re.compile(
    r"""
    \b
    (c\#|csharp|vb\.net|vbnet|vb|\.net|dotnet|java|python|node\.js|nodejs|javascript|js|c\+\+|cpp|cplusplus|android)
    \b\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Remove platform/language tokens even when not introduced by using/in/with/for.
_LANG_TOKEN_ANYWHERE_RE = re.compile(
    r"""
    \b
    (c\#|csharp|vb\.net|vbnet|vb|\.net|dotnet|java|python|node\.js|nodejs|javascript|js|c\+\+|cpp|cplusplus|android)
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Remove generic filler words that make conversion keys noisy.
_TOPIC_NOISE_WORDS_RE = re.compile(r"\b(file|files|format|formats)\b", re.IGNORECASE)
_TRAILING_PREPOSITION_RE = re.compile(r"\b(in|with|using|for)\b\s*$", re.IGNORECASE)
_C_NET_NOISE_RE = re.compile(r"\bc\s+net\b", re.IGNORECASE)
_FROM_TO_NOISE_RE = re.compile(r"\bfrom\s+to\b", re.IGNORECASE)
_FORMAT_TOKENS = {
    "3ds",
    "3mf",
    "dae",
    "drc",
    "dxf",
    "fbx",
    "glb",
    "gltf",
    "igs",
    "iges",
    "json",
    "ma",
    "obj",
    "pdf",
    "ply",
    "stl",
    "u3d",
    "usd",
    "usdz",
    "x",
    "xml",
}

def normalize_text(text: str) -> str:
    """
    Canonical topic normalization:
    - Unicode normalize
    - lowercase
    - strip punctuation
    - collapse whitespace
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t

# "OBJ to STL", "OBJ into STL", "OBJ -> STL", "OBJ2STL" (optional), etc.
_CONVERSION_PAIR_RE = re.compile(
    r"\b([a-z0-9]{2,8})\s*(?:to|into|in2|->|→)\s*([a-z0-9]{2,8})\b",
    re.IGNORECASE,
)

# Optional: catch "Convert OBJ to STL" where "convert" might be earlier in the string anyway.
# The pair regex above already matches the "OBJ to STL" part, so this is often enough.

def _final_topic_cleanup(normalized: str) -> str:
    if not normalized:
        return ""
    t = re.sub(r"\busing\s+c\s+net\b", " ", normalized, flags=re.IGNORECASE)
    t = re.sub(r"\bc\s+net\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\busing\b\s*$", " ", t, flags=re.IGNORECASE)
    t = _WS_RE.sub(" ", t).strip()
    return t


def canonical_topic_key(text: str) -> str:
    """
    Stable topic key for cross-platform matching.

    Primary rule (critical):
      If the title contains a conversion pair like "OBJ to STL",
      collapse everything to: "<src> to <dst>"

    This forces:
      - "Convert OBJ to STL in Python - 3D Modeling Software"
      - "OBJ to STL conversion"
      - "OBJ to STL file conversion guide"
    to map to the SAME key.
    """
    if not text:
        return ""

    t = unicodedata.normalize("NFKC", text).strip()
    t = re.sub(r"[-_/]+", " ", t)
    t = _LANG_QUALIFIER_RE.sub(" ", t)
    t = _TRAILING_LANG_TOKEN_RE.sub(" ", t)
    t = _LANG_TOKEN_ANYWHERE_RE.sub(" ", t)
    t = _TOPIC_NOISE_WORDS_RE.sub(" ", t)
    t = _C_NET_NOISE_RE.sub(" ", t)
    t = _FROM_TO_NOISE_RE.sub(" ", t)
    t = _TRAILING_PREPOSITION_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()

    # 1) Try to extract conversion pair and canonicalize to a single key.
    m = _CONVERSION_PAIR_RE.search(t)
    if m:
        src = m.group(1).lower()
        dst = m.group(2).lower()
        # Build canonical conversion key only for known file-format pairs.
        # This avoids false positives like "scene to real".
        if src in _FORMAT_TOKENS and dst in _FORMAT_TOKENS:
            return _final_topic_cleanup(normalize_text(f"{src} to {dst}"))

    # 2) Fallback to your old logic (language qualifier stripping + normalize)
    return _final_topic_cleanup(normalize_text(t))

def nor_platform_key(platform_key: Optional[str]) -> str:
    """
    Canonicalize platform keys, collapsing python variants to 'python'.
    """
    pk = normalize_text(platform_key or "")
    if pk in {"python_net", "python-java", "python_cpp", "python"}:
        return "python"
    return pk


def nor_website_domain(site: str) -> str:
    """
    Normalize site URL to a base domain.
    Examples:
      "https://blog.aspose.com" -> "aspose.com"
      "blog.aspose.com" -> "aspose.com"
      "https://aspose.com" -> "aspose.com"

    Note: This uses a simple 'last two labels' rule which is correct for aspose.com.
    For domains like *.co.uk you would need a public suffix list.
    """
    site = (site or "").strip()
    if not site:
        return ""

    if "://" in site:
        netloc = (urlparse(site).netloc or "").lower()
    else:
        netloc = site.lower()

    netloc = netloc.strip("/")

    parts = [p for p in netloc.split(".") if p]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return netloc


def nor_section_label(step: str) -> str:
    step = (step or "").strip().lower()
    mapping = {"blog": "blog", "docs": "Docs", "tutorials": "Tutorials", "api": "API", "kb": "KB"}
    return mapping.get(step, step.capitalize() if step else "")


def nor_platform_display_name(platform_key: Optional[str]) -> str:
    """
    Coverage uses baseline platform. Map common keys to display names.
    NOTE: python_net is now treated as Python per policy.
    """
    pk = nor_platform_key(platform_key)
    if not pk:
        return "All"
    fallback = {
        "net": ".NET",
        "java": "Java",
        "python_net": "Python",  # kept for backward compatibility
        "python": "Python",
        "cpp": "C++",
        "android": "Android via Java",
        "nodejs": "Node.js via Java",
        "php": "PHP",
        "ruby": "Ruby",
    }
    return fallback.get(pk, platform_key or "All")

def nor_website_section_from_case(case: str) -> str:
    mapping = {
        "blogs_to_blogs": "Blog",
        "docs_to_blogs": "Docs",
        "docs_to_tutorials": "Tutorials",
        "api_coverage": "API",
    }
    return mapping.get(case, case)
