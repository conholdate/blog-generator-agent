#!/usr/bin/env python3
"""
One-off backfill of the dashboard's Analytics "Trend over time" history.

The daily collector (collect_dashboard_insights.py) only records today's
figures, so history only exists from the day it started saving them
(organic sessions: 2026-10-25). This script recomputes, for every past day
D in a range, exactly the numbers the collector would have saved if it had
run on D - using the SAME queries with D as the end date:

  GA4 organic sessions   (D-90 .. D)  vs (D-181 .. D-91)
                         Organic Search channel, hostName = blog.<brand>
  GSC raw totals         (E-90 .. E)  vs (E-181 .. E-91), E = D - 3 days lag
                         zero dimensions/filters (GSC Performance totals)

Output: content/insights_history_backfill.json
  { brand: { "YYYY-MM-DD": { organicSessions, organicPriorSessions,
             gscRawImpressions, gscRawClicks, gscRawPriorImpressions,
             gscRawPriorClicks } } }

Resumable: days already in the file are skipped, so a re-run only fills
gaps (e.g. after a quota error). The dashboard prefers a real daily
snapshot over a backfilled value for the same day.

Usage:
  python scripts/backfill_insights_history.py --start 2026-01-01 --end 2026-10-24 [--brands aspose.cloud,...]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "agent_engine" / "blog_generator"))

from googleapiclient.discovery import build  # noqa: E402
from google.analytics.data_v1beta import BetaAnalyticsDataClient  # noqa: E402

from config import settings  # noqa: E402
from services import ga4_client, gsc_selector  # noqa: E402

OUT_PATH = REPO_ROOT / "content" / "insights_history_backfill.json"
GA4_WINDOW = settings.GA4_WINDOW_DAYS  # 90, same as the collector's organic_90d call
GSC_WINDOW = gsc_selector.WINDOW_DAYS  # 90
GSC_LAG = gsc_selector.GSC_DATA_LAG_DAYS  # 3

BRANDS = {
    "groupdocs.cloud": settings.GA4_PROPERTY_ID_GROUPDOCS_CLOUD,
    "aspose.cloud": settings.GA4_PROPERTY_ID_ASPOSE_CLOUD,
    "aspose.com": settings.GA4_PROPERTY_ID_ASPOSE_COM,
    "conholdate.cloud": settings.GA4_PROPERTY_ID_CONHOLDATE_CLOUD,
    "conholdate.com": settings.GA4_PROPERTY_ID_CONHOLDATE_COM,
}


def _log(msg: str) -> None:
    print(f"[backfill_insights_history] {msg}", flush=True)


def _windows(end: date, days: int) -> tuple[date, date, date, date]:
    """Same arithmetic as ga4_client.fetch_channel_sessions / gsc_selector.fetch_raw_totals."""
    recent_start = end - timedelta(days=days)
    prior_end = recent_start - timedelta(days=1)
    prior_start = prior_end - timedelta(days=days)
    return recent_start, end, prior_start, prior_end


def _retry(fn, attempts: int = 5):
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - quota/transient errors: back off and retry
            if i == attempts - 1:
                raise
            wait = 2 ** i * 3
            _log(f"  retry in {wait}s after: {exc!r}"[:300])
            time.sleep(wait)


def _day(brand: str, property_id: str, d: date, ga4, gsc_service) -> dict:
    hostname = f"blog.{brand}"
    rs, re_, ps, pe = _windows(d, GA4_WINDOW)
    recent = _retry(lambda: ga4_client._fetch_window_channel_sessions(ga4, property_id, hostname, rs, re_))
    prior = _retry(lambda: ga4_client._fetch_window_channel_sessions(ga4, property_id, hostname, ps, pe))

    site_url = gsc_selector._property_url(brand)

    def totals(start: date, end: date) -> dict:
        body = {"startDate": start.isoformat(), "endDate": end.isoformat()}
        rows = _retry(lambda: gsc_service.searchanalytics().query(siteUrl=site_url, body=body).execute()).get("rows", [])
        row = rows[0] if rows else {}
        return {"impressions": int(row.get("impressions", 0)), "clicks": int(row.get("clicks", 0))}

    grs, gre, gps, gpe = _windows(d - timedelta(days=GSC_LAG), GSC_WINDOW)
    g_recent = totals(grs, gre)
    g_prior = totals(gps, gpe)
    return {
        "organicSessions": recent.get("Organic Search", 0),
        "organicPriorSessions": prior.get("Organic Search", 0),
        "gscRawImpressions": g_recent["impressions"],
        "gscRawClicks": g_recent["clicks"],
        "gscRawPriorImpressions": g_prior["impressions"],
        "gscRawPriorClicks": g_prior["clicks"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-01-01")
    ap.add_argument("--end", default="2026-10-24")
    ap.add_argument("--brands", default="", help="comma-separated; default = all onboarded")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    wanted = [b.strip() for b in args.brands.split(",") if b.strip()] or list(BRANDS)

    data: dict = json.loads(OUT_PATH.read_text(encoding="utf-8")) if OUT_PATH.exists() else {}

    ga4 = BetaAnalyticsDataClient(credentials=ga4_client._credentials())

    for brand in wanted:
        property_id = BRANDS.get(brand)
        if not property_id:
            _log(f"{brand}: no GA4 property ID configured, skipping")
            continue
        done = data.setdefault(brand, {})
        days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        todo = [d for d in days if d.isoformat() not in done]
        _log(f"{brand}: {len(todo)} day(s) to fill ({len(days) - len(todo)} already done)")
        failed = 0

        def work(d: date):
            # googleapiclient services aren't thread-safe - one per call.
            gsc_service = build("searchconsole", "v1", credentials=gsc_selector._credentials(), cache_discovery=False)
            return d, _day(brand, property_id, d, ga4, gsc_service)

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(work, d) for d in todo]
            for n, fut in enumerate(as_completed(futures), 1):
                try:
                    d, values = fut.result()
                    done[d.isoformat()] = values
                except Exception as exc:  # noqa: BLE001 - leave the day out; a re-run fills it
                    failed += 1
                    _log(f"{brand}: a day failed ({exc!r})"[:300])
                if n % 25 == 0:
                    _log(f"{brand}: {n}/{len(todo)}")
                    OUT_PATH.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")

        data[brand] = dict(sorted(done.items()))
        OUT_PATH.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
        _log(f"{brand}: done, {failed} failed")

    _log(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
