"""
GSC-driven topic selection (I/O layer).

Entry point: select_topic_via_gsc(brand) — returns the matched approved topic
or None. The orchestrator treats None (or any raised exception) as "use the
existing round-robin selection", so this layer can never break generation:
the worst outcome is a logged warning and the current behavior.

Pure ranking/matching logic lives in utils/gsc_opportunities.py.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import settings
from utils.gsc_opportunities import (
    Opportunity,
    build_opportunities,
    find_best_topic,
    match_product_tab,
)

GSC_SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Same exclusions as helpers.get_next_tab so both selectors see the same tabs.
EXCLUDED_KEYWORD_TABS = {"tracker", "sheet1", "template", "all missing topics"}

# Translated posts live under a language prefix; generation is English-only,
# so those pages are filtered out of the GSC query server-side.
LANG_CODES = (
    "ar cs de el es fa fr he hi id it ja ko nl pl pt ru sv th tr uk vi "
    "zh zh-hans zh-hant"
).split()
PAGE_LANG_FILTER_REGEX = r"^https?://[^/]+/(" + "|".join(LANG_CODES) + r")/"

SUGGESTION_HEADERS = [
    "Date Added", "Product", "Keyword", "Impressions", "Clicks",
    "Avg Position", "Trend", "Ranking URL", "Status",
]

GSC_DATA_LAG_DAYS = 3
WINDOW_DAYS = 90  # two consecutive windows = the agreed 6-month split


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def _credentials() -> Credentials:
    key_path = os.path.join(_project_root(), "keys", settings.GOOGLE_KEY)
    return Credentials.from_service_account_file(key_path, scopes=GSC_SCOPES)


def _log(message: str) -> None:
    print(f"[GSC] {message}", flush=True)


def _property_url(brand: str) -> str:
    return settings.GSC_PROPERTY_URL or f"https://blog.{brand}/"


def _fetch_window_rows(service, site_url: str, start: date, end: date) -> list[dict]:
    """All (query, page) rows for one window, English pages only, paginated."""
    rows, start_row = [], 0
    while True:
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["query", "page"],
            "dimensionFilterGroups": [{
                "filters": [{
                    "dimension": "page",
                    "operator": "excludingRegex",
                    "expression": PAGE_LANG_FILTER_REGEX,
                }],
            }],
            "rowLimit": 25000,
            "startRow": start_row,
        }
        batch = (
            service.searchanalytics()
            .query(siteUrl=site_url, body=body)
            .execute()
            .get("rows", [])
        )
        rows.extend(batch)
        if len(batch) < 25000:
            return rows
        start_row += len(batch)


def fetch_opportunities(brand: str) -> list[Opportunity]:
    """Top striking-distance opportunities for a brand's blog property."""
    creds = _credentials()
    service = build("searchconsole", "v1", credentials=creds)
    site_url = _property_url(brand)

    recent_end = date.today() - timedelta(days=GSC_DATA_LAG_DAYS)
    recent_start = recent_end - timedelta(days=WINDOW_DAYS)
    prior_end = recent_start - timedelta(days=1)
    prior_start = prior_end - timedelta(days=WINDOW_DAYS)

    recent_rows = _fetch_window_rows(service, site_url, recent_start, recent_end)
    prior_rows = _fetch_window_rows(service, site_url, prior_start, prior_end)
    _log(f"{site_url}: {len(recent_rows)} recent / {len(prior_rows)} prior rows")

    return build_opportunities(
        recent_rows,
        prior_rows,
        min_impressions=settings.GSC_MIN_IMPRESSIONS,
        position_min=settings.GSC_POSITION_MIN,
        position_max=settings.GSC_POSITION_MAX,
        top_n=settings.GSC_TOP_N,
    )


def _write_suggestions(client: gspread.Client, unmatched: list[tuple[Opportunity, str]]) -> None:
    """Append unmatched opportunities to the brand's GSC Suggestions tab.

    Best-effort: failures are logged and swallowed so they cannot affect
    topic selection or generation.
    """
    if not unmatched or not settings.SPREADSHEET_ID_FOR_BLOGPOST_METADATA:
        return
    try:
        spreadsheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_BLOGPOST_METADATA)
        try:
            worksheet = spreadsheet.worksheet(settings.GSC_SUGGESTIONS_SHEET_NAME)
        except gspread.WorksheetNotFound:
            # Place right after the consolidated tab so it's visible without
            # scrolling past the weekly tabs.
            try:
                index = spreadsheet.worksheet(
                    settings.CONSOLIDATED_SHEET_NAME_FOR_BLOGPOST_METADATA
                ).index + 1
            except gspread.WorksheetNotFound:
                index = 1
            worksheet = spreadsheet.add_worksheet(
                title=settings.GSC_SUGGESTIONS_SHEET_NAME,
                rows=200,
                cols=len(SUGGESTION_HEADERS),
                index=index,
            )
            worksheet.append_row(SUGGESTION_HEADERS)

        existing = {
            str(row.get("Keyword", "")).strip().lower()
            for row in worksheet.get_all_records()
        }
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        added = 0
        for opp, product in unmatched:
            if opp.keyword in existing:
                continue
            worksheet.append_row([
                today, product, opp.keyword, opp.impressions, opp.clicks,
                opp.position, opp.trend, opp.page, "New",
            ])
            existing.add(opp.keyword)
            added += 1
        _log(f"suggestions: {added} new, {len(unmatched) - added} already listed")
    except Exception as e:
        _log(f"⚠️ could not write suggestions tab (non-fatal): {e}")


def select_topic_via_gsc(brand: str) -> Optional[dict]:
    """GSC-first selection: match top opportunities against approved topics.

    Returns {"tab", "row", "row_number", "keyword", "coverage"} for the first
    opportunity with a matching approved topic, else None. Unmatched
    opportunities are logged to the GSC Suggestions tab either way.
    """
    if not settings.GSC_ENABLED:
        _log("disabled via GSC_ENABLED, using round-robin")
        return None
    if not settings.SPREADSHEET_ID_FOR_KEYWORDS:
        _log("no keywords spreadsheet configured, using round-robin")
        return None

    opportunities = fetch_opportunities(brand)
    if not opportunities:
        _log("no striking-distance opportunities found, using round-robin")
        return None
    for opp in opportunities:
        _log(
            f"opportunity: '{opp.keyword}' pos {opp.position} "
            f"({opp.impressions} impr, {opp.trend})"
        )

    client = gspread.authorize(_credentials())
    spreadsheet = client.open_by_key(settings.SPREADSHEET_ID_FOR_KEYWORDS)
    worksheets = {
        ws.title: ws
        for ws in spreadsheet.worksheets()
        if ws.title.lower() not in EXCLUDED_KEYWORD_TABS
    }

    chosen = None
    unmatched: list[tuple[Opportunity, str]] = []
    rows_cache: dict[str, list[dict]] = {}
    for opp in opportunities:
        tab = match_product_tab(opp, list(worksheets.keys()))
        if not tab:
            unmatched.append((opp, ""))
            continue
        if tab not in rows_cache:
            rows_cache[tab] = worksheets[tab].get_all_records()
        best = find_best_topic(opp.keyword, rows_cache[tab], settings.GSC_MATCH_MIN_COVERAGE)
        if best and chosen is None:
            row_number, row, coverage = best
            chosen = {
                "tab": tab,
                "row": row,
                "row_number": row_number,
                "keyword": opp.keyword,
                "coverage": round(coverage, 2),
            }
            _log(
                f"✅ matched '{opp.keyword}' -> tab '{tab}' row {row_number} "
                f"(coverage {coverage:.0%})"
            )
        elif not best:
            unmatched.append((opp, tab))

    _write_suggestions(client, unmatched)
    if chosen is None:
        _log("no opportunity matched an approved topic, using round-robin")
    return chosen
