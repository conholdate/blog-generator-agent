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
    build_ctr_anomalies,
    build_opportunities,
    build_rising_queries,
    find_best_topic,
    match_product_tab,
    tokenize,
)
from utils.topic_embeddings import cosine_similarity, embed_text

GSC_SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Same exclusions as helpers.get_next_tab so both selectors see the same tabs.
EXCLUDED_KEYWORD_TABS = {"tracker", "sheet1", "template", "all missing topics"}

# Translated posts live under a language prefix; generation is English-only,
# so those pages are filtered out of the GSC query server-side (and, via
# ga4_client.py's reuse of this list, out of the GA4 insights pipeline too).
#
# zh-tw/ka/hu/da/ro/bg/sk/bs/lt added 2026-10-13 after onboarding
# aspose.cloud's GA4 property surfaced a real gap: these locale prefixes
# were missing entirely, so blog.aspose.cloud/ka/tags/,
# blog.aspose.cloud/da/cells/..., etc. were counted as real post pages -
# confirmed live, they accounted for ~7,800 of 12,326 "pages with
# sessions" for that one brand (63%). zh-cn/ua added same day after
# onboarding aspose.com surfaced two more (confirmed via samples -
# /zh-cn/cad/..., /ua/slides/... are translated posts). Checked samples
# under each new code before adding it, and separately confirmed
# /total/..., /zip/... (a real Aspose.Zip product), /2014.../...,
# /2021/.../... etc. are genuine content, not noise - left those alone.
LANG_CODES = (
    "ar cs de el es fa fr he hi id it ja ko nl pl pt ru sv th tr uk vi "
    "zh zh-hans zh-hant zh-tw zh-cn ka hu da ro bg sk bs lt ua"
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


def _fetch_recent_and_prior_rows(brand: str) -> tuple[str, list[dict], list[dict]]:
    """Shared by fetch_opportunities and fetch_all_opportunities - same two
    windows, same site, same pagination. Returns (site_url, recent_rows, prior_rows)."""
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
    return site_url, recent_rows, prior_rows


def fetch_opportunities(brand: str) -> list[Opportunity]:
    """Top striking-distance opportunities for a brand's blog property -
    capped at GSC_TOP_N, the handful the autonomous topic-selector tries
    per run."""
    _, recent_rows, prior_rows = _fetch_recent_and_prior_rows(brand)
    return build_opportunities(
        recent_rows,
        prior_rows,
        min_impressions=settings.GSC_MIN_IMPRESSIONS,
        position_min=settings.GSC_POSITION_MIN,
        position_max=settings.GSC_POSITION_MAX,
        top_n=settings.GSC_TOP_N,
    )


def fetch_all_opportunities(brand: str, top_n: int) -> list[Opportunity]:
    """Same windowing/ranking as fetch_opportunities, but with a
    caller-supplied cap - for services/insights_collector.py, which wants
    far more than the 5 the autonomous selector tries per run (every
    striking-distance opportunity worth showing in the dashboard panel,
    not just the ones generation will act on)."""
    _, recent_rows, prior_rows = _fetch_recent_and_prior_rows(brand)
    return build_opportunities(
        recent_rows,
        prior_rows,
        min_impressions=settings.GSC_MIN_IMPRESSIONS,
        position_min=settings.GSC_POSITION_MIN,
        position_max=settings.GSC_POSITION_MAX,
        top_n=top_n,
    )


def fetch_insights_signals(brand: str, top_n_opportunities: int) -> dict:
    """Striking-distance opportunities + CTR anomalies + rising queries for
    the dashboard Analytics page, all derived from ONE shared GSC fetch
    (the same two windows fetch_all_opportunities alone used to pull) -
    see services/insights_collector.py. Three deterministic, independent
    signals: opportunities are about RANKING higher, CTR anomalies are
    about getting clicked more at the rank already held, rising queries
    are about growing DEMAND for something already ranked for."""
    _, recent_rows, prior_rows = _fetch_recent_and_prior_rows(brand)
    opportunities = build_opportunities(
        recent_rows,
        prior_rows,
        min_impressions=settings.GSC_MIN_IMPRESSIONS,
        position_min=settings.GSC_POSITION_MIN,
        position_max=settings.GSC_POSITION_MAX,
        top_n=top_n_opportunities,
    )
    ctr_anomalies = build_ctr_anomalies(
        recent_rows,
        min_impressions=settings.GSC_CTR_ANOMALY_MIN_IMPRESSIONS,
        top_n=settings.GSC_CTR_ANOMALY_TOP_N,
    )
    rising_queries = build_rising_queries(
        recent_rows,
        prior_rows,
        min_impressions=settings.GSC_RISING_MIN_IMPRESSIONS,
        max_position=settings.GSC_RISING_MAX_POSITION,
        top_n=settings.GSC_RISING_TOP_N,
    )
    return {
        "opportunities": opportunities,
        "ctrAnomalies": ctr_anomalies,
        "risingQueries": rising_queries,
    }


# Below this, a lexically-overlapping query (2+ shared tokens) still isn't
# necessarily ABOUT the same thing - calibrated live against real data for
# two brands: genuine matches scored 0.84-0.92 against the post title
# (e.g. "dwg to png" vs "DWG to PNG Conversion Tutorial in Python" ->
# 0.911), while confirmed noise that passed the lexical filter topped out
# at 0.74 (e.g. "convert pdf to png java" -> 0.643, "word to png docx to
# png in python sdk" -> 0.738). Clean gap either side of 0.80.
FAQ_QUERY_RELEVANCE_THRESHOLD = 0.80


def fetch_related_queries(brand: str, title: str, keywords: list[str], top_n: int = 5) -> list[str]:
    """Real GSC queries related to a new post's topic, for grounding its
    FAQ section in genuine search demand instead of LLM-invented questions -
    see prompts.get_blog_writer_prompt's faq_queries param. A lightweight,
    query-only fetch (no page dimension, no trend) since this only needs
    "what do people actually search for near this topic," not
    striking-distance ranking analysis.

    Two filters, both required: lexical (2+ shared tokens with `keywords`)
    narrows the GSC result set down cheaply, then embedding similarity
    against `title` (>= FAQ_QUERY_RELEVANCE_THRESHOLD) confirms the
    surviving candidates are actually ABOUT the same topic, not just
    sharing a couple of generic words - see that constant's comment for
    the real-data calibration behind the threshold.

    Best-effort: [] on any failure, missing config, or no match surviving
    both filters - the caller falls back to letting the LLM invent its own
    FAQ questions, same as it always has."""
    if not settings.GSC_ENABLED:
        return []
    try:
        creds = _credentials()
        service = build("searchconsole", "v1", credentials=creds)
        site_url = _property_url(brand)

        end = date.today() - timedelta(days=GSC_DATA_LAG_DAYS)
        start = end - timedelta(days=WINDOW_DAYS)
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["query"],
            "rowLimit": 25000,
        }
        rows = service.searchanalytics().query(siteUrl=site_url, body=body).execute().get("rows", [])

        keyword_tokens = {t for kw in keywords for t in tokenize(kw)}
        if not keyword_tokens:
            return []
        # Requiring just ONE shared token is too loose - a single generic
        # token like "png" or "conversion" matched completely unrelated
        # queries (confirmed live for aspose.cloud: keywords
        # ['dwg','png','python','conversion'] matched "jpg to png .net sdk"
        # and ".net power point to pdf conversion sdk" - neither about DWG
        # at all, sharing only "png" or "conversion"). Requiring 2+ shared
        # tokens means the SPECIFIC format/topic pairing has to match, not
        # just one generic word either side happens to use.
        min_overlap = min(2, len(keyword_tokens))

        lexical_hits = []
        for row in rows:
            query = (row.get("keys") or [""])[0].strip().lower()
            # isascii() only catches non-Latin scripts, not non-English
            # Latin-script queries (confirmed live: "zip ke jpg", "ubah zip
            # ke jpg" - Indonesian - both passed this check for
            # groupdocs.cloud). Same accepted limitation as
            # build_opportunities' identical check; not worth a heavier
            # language-detection pass for a handful of FAQ seed phrases
            # the LLM is already told to rephrase naturally.
            if not query or not query.isascii():
                continue
            if len(set(tokenize(query)) & keyword_tokens) < min_overlap:
                continue
            lexical_hits.append((int(row.get("impressions", 0)), query))

        if not lexical_hits:
            return []

        # Embedding pass over lexical survivors, highest-impression first,
        # stopping once top_n relevant matches are found - confirmed live
        # that embedding every survivor sequentially can blow well past a
        # couple of minutes when many queries pass the lexical filter (one
        # network round-trip each). Capping the embedding calls instead of
        # the lexical set keeps this bounded regardless of how many
        # queries matched, and checking highest-impression-first means the
        # ones most worth showing get checked before the ones least likely
        # to matter anyway.
        lexical_hits.sort(key=lambda pair: pair[0], reverse=True)
        title_vector = embed_text(title)
        matches = []
        for impressions, query in lexical_hits:
            if len(matches) >= top_n:
                break
            if cosine_similarity(title_vector, embed_text(query)) >= FAQ_QUERY_RELEVANCE_THRESHOLD:
                matches.append(query)

        return matches
    except Exception as exc:
        print(f"⚠️ Could not fetch related GSC queries for FAQ grounding (non-fatal): {exc}", flush=True)
        return []


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
