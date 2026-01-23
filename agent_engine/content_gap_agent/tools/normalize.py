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


def canonical_topic_key(text: str) -> str:
    """
    Create a stable topic key for cross-platform matching.

    This removes language/platform qualifiers (e.g., "using C#", "in Java", "for .NET")
    before applying normalize_text(). This makes lexical matching robust when titles/topics
    differ only by language markers or slightly different phrasing.
    """
    if not text:
        return ""

    t = unicodedata.normalize("NFKC", text).strip()
    # Remove common "using/in/with/for <lang>" phrases
    t = _LANG_QUALIFIER_RE.sub(" ", t)
    # Remove trailing language token
    t = _TRAILING_LANG_TOKEN_RE.sub(" ", t)
    # Final canonical normalization
    return normalize_text(t)


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
