"""
Dashboard insights snapshot - orchestration (I/O layer).

Entry point: collect_brand_insights(brand, property_id, previous_entry) ->
one brand's entry for content/dashboard_insights.json. Combines GA4 page
sessions (services/ga4_client.py) and GSC striking-distance opportunities
(services/gsc_selector.py), grouped into brand|Product|Platform buckets via
the existing topic-duplicate index (utils/insights_snapshot.py), plus a
brand-wide channel (Organic Search/Referral/Social/...) breakdown for the
dashboard's Analytics widget.

Never raises: the caller (scripts/collect_dashboard_insights.py) loops
brands independently, and a single brand's failure must never blank out
its own last-good data, let alone block the other brands. See
collect_brand_insights's docstring for the exact contract.
"""
from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone

from config import settings
from services import ga4_client, gsc_selector
from utils.insights_snapshot import (
    build_url_bucket_map,
    build_url_title_map,
    group_ga4_sessions_by_bucket,
    group_gsc_opportunities_by_bucket,
    top_declining_posts,
)
from utils.topic_index import INDEX_PATH


def _log(message: str) -> None:
    print(f"[Insights] {message}", flush=True)


def _load_topic_index() -> dict:
    if not INDEX_PATH.exists():
        return {}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def collect_brand_insights(brand: str, property_id: str, previous_entry: dict | None) -> dict:
    """One brand's snapshot entry. On any failure, returns previous_entry
    unchanged (marked stale) rather than raising or returning empty data -
    a transient GA4/GSC error must never erase yesterday's real numbers."""
    try:
        topic_index = _load_topic_index()
        url_to_bucket = build_url_bucket_map(topic_index, brand)

        page_sessions = ga4_client.fetch_page_sessions(brand, property_id)
        ga4_by_bucket, ga4_unmatched = group_ga4_sessions_by_bucket(page_sessions, url_to_bucket)
        channels = ga4_client.fetch_channel_sessions(brand, property_id)
        declining_posts = top_declining_posts(
            page_sessions, build_url_title_map(topic_index, brand), settings.GA4_DECLINE_TOP_N
        )

        signals = gsc_selector.fetch_insights_signals(
            brand, top_n_opportunities=settings.GA4_MAX_OPPORTUNITIES_PER_BRAND
        )
        opportunities = signals["opportunities"]
        gsc_by_bucket, gsc_unmatched = group_gsc_opportunities_by_bucket(opportunities, url_to_bucket)
        # Flat, brand-wide, already-sorted-best-first slice of the SAME
        # opportunities (not re-filtered) for the Analytics page's signal
        # list - each row individually searchable in the GSC UI, unlike
        # the raw totals below which are a single aggregate number.
        top_opportunities = [
            {
                "keyword": o.keyword,
                "page": o.page,
                "impressions": o.impressions,
                "clicks": o.clicks,
                "position": o.position,
                "trend": o.trend,
            }
            for o in opportunities[: settings.GSC_TOP_OPPORTUNITIES_DISPLAY_N]
        ]

        # Zero-filter totals - see fetch_raw_totals' docstring for why this
        # (not the filtered `opportunities` sum) is the dashboard's
        # headline GSC stat: it's the only GSC number that's 1:1
        # verifiable against GSC's own Performance Overview with no
        # export/filtering steps.
        raw_totals = gsc_selector.fetch_raw_totals(brand)

        bucket_keys = set(ga4_by_bucket) | set(gsc_by_bucket)
        buckets = {
            key: {
                "ga4": ga4_by_bucket.get(key),
                "gscOpportunities": gsc_by_bucket.get(key, []),
            }
            for key in bucket_keys
        }

        _log(
            f"{brand}: {len(buckets)} buckets with data "
            f"({len(page_sessions)} GA4 pages, {ga4_unmatched} unmatched; "
            f"{len(opportunities)} GSC opportunities, {gsc_unmatched} unmatched; "
            f"{len(declining_posts)} declining posts, {len(signals['ctrAnomalies'])} CTR anomalies, "
            f"{len(signals['risingQueries'])} rising queries)"
        )

        return {
            "status": "ok",
            "refreshedAt": datetime.now(timezone.utc).isoformat(),
            "buckets": buckets,
            "channels": channels,
            "decliningPosts": declining_posts,
            "ctrAnomalies": signals["ctrAnomalies"],
            "risingQueries": signals["risingQueries"],
            "topOpportunities": top_opportunities,
            "gscRawImpressions": raw_totals["impressions"],
            "gscRawClicks": raw_totals["clicks"],
            "gscRawPriorImpressions": raw_totals["priorImpressions"],
            "gscRawPriorClicks": raw_totals["priorClicks"],
        }
    except Exception as exc:
        _log(f"{brand}: collection failed ({exc!r}), keeping previous snapshot if any")
        traceback.print_exc()
        if previous_entry is not None:
            return {**previous_entry, "status": "error", "error": str(exc)}
        return {
            "status": "error",
            "error": str(exc),
            "refreshedAt": None,
            "buckets": {},
            "channels": {},
            "decliningPosts": [],
            "ctrAnomalies": [],
            "risingQueries": [],
            "topOpportunities": [],
            "gscRawImpressions": 0,
            "gscRawClicks": 0,
            "gscRawPriorImpressions": 0,
            "gscRawPriorClicks": 0,
        }
