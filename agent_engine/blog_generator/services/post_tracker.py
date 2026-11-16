"""
Per-URL performance tracking for posts the dashboard asked us to follow
(today: posts Autopilot suggested and published, and existing posts
Autopilot sent for a refresh).

Contract with the dashboard (blog-command-center):
  - The dashboard writes one field per tracked URL to the Redis hash
    TRACKING_KEY: {url, brand, kind: "post" | "refresh", since: "YYYY-MM-DD",
    title, source}. `since` is the publish date (new post) or the date the
    refresh went live.
  - This module reads that hash once a day (from
    scripts/collect_dashboard_insights.py), fetches GA4 sessions + GSC
    clicks/impressions/position/top queries for each URL, and writes
    content/post_tracking.json, which the dashboard reads back.

Windows are counted from `since`: d7, d30, d90 (day 0 = `since`). A window
is "complete" once its last day is older than the GSC data lag; complete
windows are frozen and never re-fetched. Only the first incomplete window
is fetched (as "so far" numbers), so a young post shows live progress
without re-querying every window every day. Refreshes also get a one-off
`before28` window (the 28 days before `since`) to compare against.

Everything here is best-effort: one URL's failure is logged and its previous
numbers are kept; it never blocks the rest of the insights collection.
"""
from __future__ import annotations

import json
import os
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    FilterExpressionList,
    Metric,
    RunReportRequest,
)
from googleapiclient.discovery import build

from services import ga4_client, gsc_selector

TRACKING_KEY = "posttracking:urls:v1"
WINDOWS = (7, 30, 90)
BEFORE_DAYS = 28
TOP_QUERIES = 5
# Stop following a URL this long after `since` (every window is frozen by then).
MAX_AGE_DAYS = max(WINDOWS) + gsc_selector.GSC_DATA_LAG_DAYS + 7


def _log(message: str) -> None:
    print(f"[post_tracker] {message}", flush=True)


def _redis_creds() -> tuple[str, str] | None:
    url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return None
    return url.rstrip("/"), token


def load_tracked_urls() -> list[dict]:
    """The dashboard's tracking list. [] if Redis isn't configured/reachable."""
    creds = _redis_creds()
    if not creds:
        _log("Redis not configured (KV_REST_API_URL/TOKEN), nothing to track")
        return []
    base_url, token = creds
    resp = requests.get(
        f"{base_url}/hgetall/{TRACKING_KEY}", headers={"Authorization": f"Bearer {token}"}, timeout=15
    )
    resp.raise_for_status()
    flat = resp.json().get("result") or []
    entries = []
    for i in range(1, len(flat), 2):
        try:
            value = flat[i]
            entry = json.loads(value) if isinstance(value, str) else value
        except (TypeError, ValueError):
            continue
        if isinstance(entry, dict) and entry.get("url") and entry.get("brand") and entry.get("since"):
            entries.append(entry)
    return entries


def _ga4_sessions(client: BetaAnalyticsDataClient, property_id: str, url: str, start: date, end: date) -> int:
    parsed = urlparse(url)
    path = parsed.path or "/"
    variants = sorted({path, path.rstrip("/") or "/", path if path.endswith("/") else path + "/"})
    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimension_filter=FilterExpression(
            and_group=FilterExpressionList(
                expressions=[
                    FilterExpression(
                        filter=Filter(field_name="hostName", string_filter=Filter.StringFilter(value=parsed.netloc))
                    ),
                    FilterExpression(
                        filter=Filter(field_name="pagePath", in_list_filter=Filter.InListFilter(values=variants))
                    ),
                ]
            )
        ),
    )
    response = client.run_report(request)
    return sum(int(row.metric_values[0].value) for row in response.rows)


def _gsc_metrics(service, site_url: str, url: str, start: date, end: date) -> dict:
    page_filter = [{"filters": [{"dimension": "page", "operator": "equals", "expression": url}]}]
    base = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dimensionFilterGroups": page_filter}

    totals_rows = (
        service.searchanalytics()
        .query(siteUrl=site_url, body={**base, "dimensions": ["page"], "rowLimit": 10})
        .execute()
        .get("rows", [])
    )
    clicks = sum(r.get("clicks", 0) for r in totals_rows)
    impressions = sum(r.get("impressions", 0) for r in totals_rows)
    position = (
        sum(r.get("position", 0) * r.get("impressions", 0) for r in totals_rows) / impressions if impressions else None
    )

    query_rows = (
        service.searchanalytics()
        .query(siteUrl=site_url, body={**base, "dimensions": ["query"], "rowLimit": 50})
        .execute()
        .get("rows", [])
    )
    query_rows.sort(key=lambda r: r.get("impressions", 0), reverse=True)
    top_queries = [
        {
            "query": r["keys"][0],
            "impressions": int(r.get("impressions", 0)),
            "clicks": int(r.get("clicks", 0)),
            "position": round(r.get("position", 0), 1),
        }
        for r in query_rows[:TOP_QUERIES]
    ]
    return {
        "clicks": int(clicks),
        "impressions": int(impressions),
        "position": round(position, 1) if position is not None else None,
        "topQueries": top_queries,
    }


def _window(ga4, property_id, gsc, site_url, url, start: date, end: date, complete: bool) -> dict:
    metrics = _gsc_metrics(gsc, site_url, url, start, end)
    metrics["sessions"] = _ga4_sessions(ga4, property_id, url, start, end) if property_id else None
    metrics.update({"start": start.isoformat(), "end": end.isoformat(), "complete": complete})
    return metrics


def _track_one(entry: dict, previous: dict, ga4, property_id: str | None, gsc, today: date) -> dict:
    url = entry["url"]
    since = date.fromisoformat(str(entry["since"])[:10])
    last_data_day = today - timedelta(days=gsc_selector.GSC_DATA_LAG_DAYS)
    site_url = f"https://{urlparse(url).netloc}/"
    windows: dict = dict(previous.get("windows") or {})

    if entry.get("kind") == "refresh" and not (windows.get("before28") or {}).get("complete"):
        windows["before28"] = _window(
            ga4, property_id, gsc, site_url, url, since - timedelta(days=BEFORE_DAYS), since - timedelta(days=1), True
        )

    for days in WINDOWS:
        key = f"d{days}"
        if (windows.get(key) or {}).get("complete"):
            continue
        window_end = since + timedelta(days=days - 1)
        end = min(window_end, last_data_day)
        if end < since:
            break  # no data for this post yet
        windows[key] = _window(ga4, property_id, gsc, site_url, url, since, end, window_end <= last_data_day)
        if not windows[key]["complete"]:
            break  # only the current window is fetched as "so far"

    return {
        "url": url,
        "brand": entry["brand"],
        "kind": entry.get("kind", "post"),
        "title": entry.get("title", ""),
        "since": since.isoformat(),
        "windows": windows,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def collect_post_tracking(property_ids: dict[str, str | None], snapshot_path: Path) -> None:
    """Refreshes snapshot_path for every tracked URL. property_ids: brand -> GA4 property ID."""
    previous: dict = {}
    if snapshot_path.exists():
        try:
            previous = json.loads(snapshot_path.read_text(encoding="utf-8")).get("posts", {})
        except (ValueError, AttributeError):
            previous = {}

    entries = load_tracked_urls()
    _log(f"{len(entries)} tracked URL(s)")
    today = date.today()
    try:
        ga4 = BetaAnalyticsDataClient(credentials=ga4_client._credentials())
    except Exception as e:  # noqa: BLE001 - GSC numbers are still worth having
        _log(f"GA4 unavailable ({e}), sessions will be empty")
        ga4, property_ids = None, {}
    gsc = build("searchconsole", "v1", credentials=gsc_selector._credentials())

    posts: dict = {}
    for entry in entries:
        url = entry["url"]
        prev = previous.get(url, {})
        try:
            since = date.fromisoformat(str(entry["since"])[:10])
            if (today - since).days > MAX_AGE_DAYS and prev:
                posts[url] = prev  # fully frozen - nothing left to fetch
                continue
            posts[url] = _track_one(entry, prev, ga4, property_ids.get(entry["brand"]), gsc, today)
        except Exception as e:  # noqa: BLE001 - one URL must never block the rest
            _log(f"{url}: failed ({e}), keeping previous numbers")
            traceback.print_exc()
            if prev:
                posts[url] = prev

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(
            {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "posts": posts},
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _log(f"wrote {snapshot_path} ({len(posts)} URL(s))")
