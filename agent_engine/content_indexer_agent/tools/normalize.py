from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

import unicodedata

from agent_engine.content_indexer_agent.tools.specs import ProductSpec

_PUNCT_RE = re.compile(r"[^\w\s]+", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)


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
    Coverage uses baseline platform. Map common keys to display names (same convention as indexer).
    """
    pk = (platform_key or "").strip().lower()
    if not pk:
        return "All"
    fallback = {
        "net": ".NET",
        "java": "Java",
        "python_net": "Python via .NET",
        "cpp": "C++",
        "android": "Android via Java",
        "nodejs": "Node.js via Java",
        "python": "Python",
        "php": "PHP",
        "ruby": "Ruby",
    }
    return fallback.get(pk, platform_key or "All")
