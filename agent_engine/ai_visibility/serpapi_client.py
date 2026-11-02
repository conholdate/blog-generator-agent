"""
Minimal client for SerpAPI's Google AI Overview lookup - uses a SEPARATE,
dedicated SerpAPI key (SERPAPI_KEY_AI_VISIBILITY) from the one
blog_keyword_analyzer uses (SERPAPI_KEY), so this never competes with
keyword research for the same free-tier quota.

Two-call sequence, confirmed live against real queries (2026-10-30): a
plain "google" search returns an ai_overview.page_token (no actual
content yet) when Google shows an AI Overview for that query; that token
must then be passed to a separate "google_ai_overview" engine call to get
the real text_blocks + references. There is no single-call way to get the
content - SerpAPI's two-step shape mirrors Google's own lazy-loaded AI
Overview UI.
"""
from dataclasses import dataclass, field

import requests

SERPAPI_BASE = "https://serpapi.com/search"
TIMEOUT = 30


@dataclass
class AiOverviewResult:
    has_overview: bool
    references: list[dict] = field(default_factory=list)  # [{"link": ..., "title": ...}, ...]


def fetch_ai_overview(query: str, api_key: str) -> AiOverviewResult | None:
    """Returns None on any failure (missing key, network error, malformed
    response) - callers must treat None as "couldn't check this one, skip
    it", never as "not cited". Those are different things, and conflating
    them would silently report false negatives.

    Returns AiOverviewResult(has_overview=False) when Google simply
    didn't show an AI Overview for this query - a real, valid outcome
    (not every query triggers one), distinct from a failed check.
    """
    if not api_key:
        return None

    try:
        first = requests.get(
            SERPAPI_BASE,
            params={"engine": "google", "q": query, "api_key": api_key},
            timeout=TIMEOUT,
        )
        first.raise_for_status()
        data = first.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  ⚠️  SerpAPI search failed for {query!r}: {e}")
        return None

    page_token = (data.get("ai_overview") or {}).get("page_token")
    if not page_token:
        return AiOverviewResult(has_overview=False)

    try:
        second = requests.get(
            SERPAPI_BASE,
            params={"engine": "google_ai_overview", "page_token": page_token, "api_key": api_key},
            timeout=TIMEOUT,
        )
        second.raise_for_status()
        data2 = second.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  ⚠️  SerpAPI AI Overview fetch failed for {query!r}: {e}")
        return None

    references = (data2.get("ai_overview") or {}).get("references", [])
    return AiOverviewResult(has_overview=True, references=references)
