"""
GA4 Data API client (I/O layer) - dashboard insights snapshot.

Entry point: fetch_page_sessions(brand, property_id) -> per-URL sessions +
trend, for services/insights_collector.py. Mirrors services/gsc_selector.py's
shape (credentials loading, two-window trend comparison, paginated fetch)
but is a separate pipeline/kill-switch (INSIGHTS_ENABLED, GA4_GOOGLE_KEY) -
independent of GSC_ENABLED/autonomous topic selection.

Scoped to one brand's blog subdomain via a hostName filter: a GA4 property
covers the whole domain (products, docs, forum, blog, ...), and querying
without this filter returns whole-property traffic, not just the blog
(confirmed directly against a real property during the POC).
"""
from __future__ import annotations

import os
import re
from datetime import date, timedelta

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)
from google.oauth2.service_account import Credentials

from config import settings
from services.gsc_selector import LANG_CODES
from utils.gsc_opportunities import NON_PRODUCT_SLUGS

GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
ROW_LIMIT = 100000  # GA4 Data API max rowLimit per request; one brand's blog is nowhere close

# GA4 reports every distinct path as its own "page" - translated copies
# (/zh/..., /zh-hant/...), pagination (/page/39/), and tag/category listing
# pages all show up alongside real posts and vastly outnumber them (confirmed
# live: 33,681 GA4 paths for groupdocs.cloud against ~612 actual indexed
# posts). Reuses the same exclusion lists gsc_opportunities.py/gsc_selector.py
# already built for the identical problem on the GSC side, rather than
# inventing a second filter that could silently drift from it.
_LANG_PREFIX_RE = re.compile(r"^/(" + "|".join(LANG_CODES) + r")/")


def _is_real_post_path(path: str) -> bool:
    if not path or path == "/":
        return False
    if _LANG_PREFIX_RE.match(path):
        return False
    first_segment = path.strip("/").split("/", 1)[0].lower()
    return first_segment not in NON_PRODUCT_SLUGS


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _credentials() -> Credentials:
    key_path = os.path.join(_project_root(), "keys", settings.GA4_GOOGLE_KEY)
    return Credentials.from_service_account_file(key_path, scopes=GA4_SCOPES)


def _log(message: str) -> None:
    print(f"[GA4] {message}", flush=True)


def _fetch_window_sessions(
    client: BetaAnalyticsDataClient, property_id: str, hostname: str, start: date, end: date
) -> dict[str, int]:
    """{full_url: sessions} for one window, one brand's blog subdomain only."""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="hostName"), Dimension(name="pagePath")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimension_filter=FilterExpression(
            filter=Filter(field_name="hostName", string_filter=Filter.StringFilter(value=hostname))
        ),
        limit=ROW_LIMIT,
    )
    response = client.run_report(request)
    sessions_by_path: dict[str, int] = {}
    for row in response.rows:
        host, path = row.dimension_values[0].value, row.dimension_values[1].value
        if not _is_real_post_path(path):
            continue
        sessions = int(row.metric_values[0].value)
        url = f"https://{host}{path}"
        sessions_by_path[url] = sessions_by_path.get(url, 0) + sessions
    return sessions_by_path


def _fetch_window_channel_sessions(
    client: BetaAnalyticsDataClient, property_id: str, hostname: str, start: date, end: date
) -> dict[str, int]:
    """{channel_group: sessions} for one window, one brand's blog subdomain
    only - e.g. "Organic Search", "Referral", "Organic Social", "Direct".
    Uses GA4's own sessionDefaultChannelGroup dimension rather than
    classifying session source ourselves, so this stays consistent with
    whatever channel definitions/rules are configured on the property
    (including any custom channel group edits made directly in GA4, like
    the AI-referral channel added during this project)."""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimension_filter=FilterExpression(
            filter=Filter(field_name="hostName", string_filter=Filter.StringFilter(value=hostname))
        ),
        limit=ROW_LIMIT,
    )
    response = client.run_report(request)
    sessions_by_channel: dict[str, int] = {}
    for row in response.rows:
        channel = row.dimension_values[0].value
        sessions_by_channel[channel] = sessions_by_channel.get(channel, 0) + int(row.metric_values[0].value)
    return sessions_by_channel


def fetch_channel_sessions(brand: str, property_id: str) -> dict[str, dict]:
    """{channel_group: {"sessions": int, "priorSessions": int}} for one
    brand's blog subdomain - the Organic/Referral/Social/... breakdown for
    the Analytics dashboard widget. A separate, brand-level-only query
    (no pagePath dimension) from fetch_page_sessions above: channel
    breakdown is only needed as a brand-wide total, not per post, so this
    avoids a much larger per-page-per-channel result for no actual use.

    Uses GA4_CHANNEL_WINDOW_DAYS (a week), not GA4_WINDOW_DAYS (90 days,
    used by fetch_page_sessions for the per-bucket insights panel) -
    deliberately shorter so the Analytics widget reads as "this week's
    traffic" rather than a 90-day average that barely moves day to day."""
    hostname = f"blog.{brand}"
    client = BetaAnalyticsDataClient(credentials=_credentials())

    recent_end = date.today()
    recent_start = recent_end - timedelta(days=settings.GA4_CHANNEL_WINDOW_DAYS)
    prior_end = recent_start - timedelta(days=1)
    prior_start = prior_end - timedelta(days=settings.GA4_CHANNEL_WINDOW_DAYS)

    recent = _fetch_window_channel_sessions(client, property_id, hostname, recent_start, recent_end)
    prior = _fetch_window_channel_sessions(client, property_id, hostname, prior_start, prior_end)
    _log(f"{hostname}: {len(recent)} channels (recent) / {len(prior)} (prior)")

    channels = set(recent) | set(prior)
    return {
        channel: {"sessions": recent.get(channel, 0), "priorSessions": prior.get(channel, 0)}
        for channel in channels
    }


def fetch_page_sessions(brand: str, property_id: str) -> dict[str, dict]:
    """{full_url: {"sessions": int, "priorSessions": int, "trend": str}}
    for one brand's blog subdomain, current GA4_WINDOW_DAYS window vs. the
    prior one for trend - same windowing shape as gsc_selector.py's
    opportunity fetch, so both signals cover comparable timeframes.

    priorSessions is returned alongside the derived trend label (not just
    the label alone) so callers that aggregate many URLs together (e.g.
    insights_snapshot.py's bucket/brand rollups) can sum both periods and
    compute their own trend from the combined totals, rather than trying
    to meaningfully combine several different per-URL trend labels."""
    hostname = f"blog.{brand}"
    client = BetaAnalyticsDataClient(credentials=_credentials())

    recent_end = date.today()
    recent_start = recent_end - timedelta(days=settings.GA4_WINDOW_DAYS)
    prior_end = recent_start - timedelta(days=1)
    prior_start = prior_end - timedelta(days=settings.GA4_WINDOW_DAYS)

    recent = _fetch_window_sessions(client, property_id, hostname, recent_start, recent_end)
    prior = _fetch_window_sessions(client, property_id, hostname, prior_start, prior_end)
    _log(f"{hostname}: {len(recent)} pages with sessions (recent) / {len(prior)} (prior)")

    result: dict[str, dict] = {}
    for url, sessions in recent.items():
        prior_sessions = prior.get(url)
        if prior_sessions is None:
            trend = "new"
        else:
            delta = sessions - prior_sessions
            denominator = max(prior_sessions, 1)
            if delta / denominator > 0.1:
                trend = "improving"
            elif delta / denominator < -0.1:
                trend = "declining"
            else:
                trend = "flat"
        result[url] = {"sessions": sessions, "priorSessions": prior_sessions or 0, "trend": trend}
    return result
