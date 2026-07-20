"""
GSC opportunity ranking + topic matching (pure logic).

Turns raw Search Console rows into ranked "striking distance" opportunities
(decent impressions, position 8-20, ideally improving) and matches them
against keyword-sheet topic rows.

This module is intentionally stdlib-only so it can be imported and tested
without the blog generator's config/settings (mirrors layouts.py). All I/O
(GSC API, Google Sheets) lives in services/gsc_selector.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Function words only — format/product words ("pdf", "online", "file") must
# survive tokenization because they carry the matching signal.
STOPWORDS = {
    "a", "an", "and", "the", "in", "on", "of", "to", "for", "with", "using",
    "how", "is", "are", "what", "via", "from", "by", "or", "at", "do", "does",
}

# First URL path segments that are listing pages, not product categories.
NON_PRODUCT_SLUGS = {"tag", "tags", "category", "categories", "page", "author", "search"}

TREND_IMPROVING = "improving"
TREND_DECLINING = "declining"
TREND_FLAT = "flat"
TREND_NEW = "new"

# Declining keywords still qualify, but rank below improving/flat ones with
# similar impressions.
TREND_SCORE_MULTIPLIER = {
    TREND_IMPROVING: 1.2,
    TREND_NEW: 1.1,
    TREND_FLAT: 1.0,
    TREND_DECLINING: 0.7,
}

KEYWORD_ROW_TEXT_FIELDS = (
    "generated_title",
    "primary_keyword",
    "secondary_keywords",
    "long_tail_keywords",
    "semantic_keywords",
)


@dataclass
class Opportunity:
    keyword: str
    page: str            # top ranking URL for this query
    impressions: int
    clicks: int
    position: float      # impression-weighted average, recent window
    trend: str           # improving | declining | flat | new
    score: float = 0.0


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens minus function words, order preserved."""
    words = re.split(r"[^a-z0-9]+", str(text).lower())
    return [w for w in words if w and w not in STOPWORDS]


def aggregate_queries(rows: list[dict]) -> dict[str, dict]:
    """Collapse GSC API rows (dimensions: query, page) into per-query stats.

    Returns {query: {clicks, impressions, position, page}} where position is
    impression-weighted and page is the query's highest-impression URL.
    """
    stats: dict[str, dict] = {}
    for row in rows:
        keys = row.get("keys") or []
        if len(keys) < 2:
            continue
        query, page = keys[0].strip().lower(), keys[1]
        impressions = int(row.get("impressions", 0))
        clicks = int(row.get("clicks", 0))
        position = float(row.get("position", 0.0))
        entry = stats.setdefault(
            query,
            {"clicks": 0, "impressions": 0, "_pos_weighted": 0.0, "page": page, "_page_impr": -1},
        )
        entry["clicks"] += clicks
        entry["impressions"] += impressions
        entry["_pos_weighted"] += position * max(impressions, 1)
        if impressions > entry["_page_impr"]:
            entry["page"] = page
            entry["_page_impr"] = impressions
    for entry in stats.values():
        entry["position"] = entry["_pos_weighted"] / max(entry["impressions"], 1)
        del entry["_pos_weighted"], entry["_page_impr"]
    return stats


def build_opportunities(
    recent_rows: list[dict],
    prior_rows: list[dict],
    min_impressions: int,
    position_min: float,
    position_max: float,
    top_n: int,
) -> list[Opportunity]:
    """Rank striking-distance opportunities from two consecutive GSC windows.

    recent_rows drive eligibility (impressions floor + position band);
    prior_rows only supply the trend.
    """
    recent = aggregate_queries(recent_rows)
    prior = aggregate_queries(prior_rows)

    opportunities = []
    for query, stats in recent.items():
        # Non-English queries rank on English pages too, but can never match
        # English sheet topics — drop them so they don't waste opportunity
        # slots or clutter the suggestions tab.
        if not query.isascii():
            continue
        if stats["impressions"] < min_impressions:
            continue
        if not position_min <= stats["position"] <= position_max:
            continue
        prior_stats = prior.get(query)
        if prior_stats is None:
            trend = TREND_NEW
        else:
            delta = prior_stats["position"] - stats["position"]  # positive = moved up
            trend = TREND_IMPROVING if delta > 1 else TREND_DECLINING if delta < -1 else TREND_FLAT
        opp = Opportunity(
            keyword=query,
            page=stats["page"],
            impressions=stats["impressions"],
            clicks=stats["clicks"],
            position=round(stats["position"], 1),
            trend=trend,
            score=stats["impressions"] * TREND_SCORE_MULTIPLIER[trend],
        )
        opportunities.append(opp)

    opportunities.sort(key=lambda o: o.score, reverse=True)
    return opportunities[:top_n]


def product_slug_from_url(page_url: str) -> str:
    """First path segment of a blog URL ('https://blog.x.com/cells/foo/' -> 'cells').

    Returns '' for root/listing pages (tags, categories, ...).
    """
    match = re.match(r"^https?://[^/]+/([^/]+)/", str(page_url))
    if not match:
        return ""
    slug = match.group(1).lower()
    return "" if slug in NON_PRODUCT_SLUGS else slug


def match_product_tab(opportunity: Opportunity, tab_names: list[str]) -> str:
    """Pick the keyword-sheet tab an opportunity belongs to, or ''.

    Primary signal: the ranking URL's category slug (exact tab-name match).
    Fallback: first keyword token that equals a tab name (source format
    usually comes first in queries like 'pdf to word').
    """
    by_lower = {t.strip().lower(): t for t in tab_names}
    slug = product_slug_from_url(opportunity.page)
    if slug in by_lower:
        return by_lower[slug]
    for token in tokenize(opportunity.keyword):
        if token in by_lower:
            return by_lower[token]
    return ""


def topic_match_coverage(keyword: str, row: dict) -> float:
    """Fraction of the GSC keyword's tokens present in the row's title+keywords."""
    keyword_tokens = set(tokenize(keyword))
    if not keyword_tokens:
        return 0.0
    row_text = " ".join(str(row.get(f, "")) for f in KEYWORD_ROW_TEXT_FIELDS)
    row_tokens = set(tokenize(row_text))
    return len(keyword_tokens & row_tokens) / len(keyword_tokens)


def find_best_topic(
    keyword: str,
    rows: list[dict],
    min_coverage: float,
) -> Optional[tuple[int, dict, float]]:
    """Best approved row matching the keyword, as (sheet_row_number, row, coverage).

    Only rows with status 'approved' qualify — the human gate is never bypassed.
    Sheet row number accounts for the header row (index 0 -> row 2).
    """
    best = None
    for i, row in enumerate(rows):
        if str(row.get("status", "")).strip().lower() != "approved":
            continue
        coverage = topic_match_coverage(keyword, row)
        if coverage >= min_coverage and (best is None or coverage > best[2]):
            best = (i + 2, row, coverage)
    return best
