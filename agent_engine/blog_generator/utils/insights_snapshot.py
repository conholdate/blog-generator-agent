"""
Dashboard insights snapshot - pure logic (URL normalization, bucket matching).

Turns raw GA4 page-level sessions and GSC opportunities into per-bucket
("brand|Product|Platform", same key shape as dashboard_topic_index.json)
groups, by matching against the existing topic-duplicate index's known post
URLs rather than re-deriving product/platform from scratch.

Stdlib-only, mirrors utils/gsc_opportunities.py's split: all I/O (GA4 API,
GSC API, reading the topic index) lives in services/insights_collector.py.
"""
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def normalize_url(url: str) -> str:
    """Strip trailing slash, query string, and fragment; lowercase scheme
    and host. Needed because GA4 page paths, GSC ranking URLs, and the
    topic index's stored URLs don't reliably agree on trailing-slash or
    query-string formatting even for the same real post."""
    if not url:
        return ""
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def build_url_bucket_map(topic_index: dict, brand: str) -> dict[str, str]:
    """Reverse index: normalized post URL -> its 'brand|Product|Platform'
    bucket key, for one brand only. Reuses the topic-duplicate index as the
    single source of truth for which URL belongs to which product/platform,
    instead of re-deriving that from the URL shape (which gsc_opportunities.py's
    product_slug_from_url only does at the product level, not platform)."""
    url_to_bucket: dict[str, str] = {}
    prefix = f"{brand}|"
    for bucket_key, posts in topic_index.items():
        if not bucket_key.startswith(prefix):
            continue
        for post in posts:
            url = normalize_url(post.get("url", ""))
            if url:
                url_to_bucket[url] = bucket_key
    return url_to_bucket


def group_ga4_sessions_by_bucket(
    page_sessions: dict[str, dict], url_to_bucket: dict[str, str]
) -> tuple[dict[str, dict], int]:
    """page_sessions: {raw_url: {"sessions": int, "trend": str}} as returned by
    ga4_client.fetch_page_sessions (not pre-normalized - normalized here).

    Returns ({bucket_key: {"sessions": int, "postCount": int}}, unmatched_count).
    Sessions are summed across every known post in a bucket; postCount is how
    many of those posts actually had GA4 data (not just how many exist).
    """
    grouped: dict[str, dict] = {}
    unmatched = 0
    for url, stats in page_sessions.items():
        bucket_key = url_to_bucket.get(normalize_url(url))
        if bucket_key is None:
            unmatched += 1
            continue
        entry = grouped.setdefault(bucket_key, {"sessions": 0, "postCount": 0})
        entry["sessions"] += stats.get("sessions", 0)
        entry["postCount"] += 1
    return grouped, unmatched


def group_gsc_opportunities_by_bucket(
    opportunities: list, url_to_bucket: dict[str, str]
) -> tuple[dict[str, list], int]:
    """opportunities: list of gsc_opportunities.Opportunity.

    Matches each opportunity's ranking page against the same URL->bucket map
    GA4 uses, so both signals are attributed consistently. An opportunity
    whose page isn't a known indexed post (plausible - GSC can surface a
    non-blog page, or a post missing from the index) is dropped rather than
    guessed at from the URL shape alone.
    """
    grouped: dict[str, list] = {}
    unmatched = 0
    for opp in opportunities:
        bucket_key = url_to_bucket.get(normalize_url(opp.page))
        if bucket_key is None:
            unmatched += 1
            continue
        grouped.setdefault(bucket_key, []).append({
            "keyword": opp.keyword,
            "page": opp.page,
            "impressions": opp.impressions,
            "clicks": opp.clicks,
            "position": opp.position,
            "trend": opp.trend,
        })
    return grouped, unmatched
