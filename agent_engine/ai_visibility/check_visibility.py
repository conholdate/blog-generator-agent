"""
Checks whether a brand is cited in Google's AI Overview for a small, REAL
set of search queries - not invented topics, but the brand's own top GSC
opportunities/rising-demand queries already computed into
content/dashboard_insights.json for the dashboard. Each tracked query
already carries the existing post (`page`) that targets it, so a
citation gap becomes a direct candidate for the dashboard's Optimize
queue, not a guess at what to write.

Why this exists: AI answer engines increasingly answer questions
directly instead of showing blue links, and there was no visibility into
whether our own content gets cited in those answers, or who wins those
citations instead. This closes that gap for Google's AI Overview
specifically - the only answer engine with a usable, ToS-compliant API
for this (via SerpAPI), confirmed live (2026-10-30).

Results APPEND to content/aiVisibility/<brand>.json rather than
replacing it (unlike exampleRepos' snapshot-per-run), so a trend over
time can be reconstructed - e.g. did a page that was missing before
start getting cited after it was fixed.

Runs weekly (.github/workflows/ai_visibility_check.yml), one brand per
invocation via a matrix - same CLI convention as
code_retrieval/build_registry.py (`python check_visibility.py <brand>`).

Prefers SERPAPI_KEY_AI_VISIBILITY, a dedicated key with its own
free-tier quota so this never competes with keyword research. Falls
back to blog_keyword_analyzer's shared SERPAPI_KEY if the dedicated one
isn't set (see main()) - fine short-term, but that shared key is
already close to its free-plan monthly cap, so move to a dedicated key
before widening this beyond the current small per-brand query cap. No
key at all (neither var set) -> every brand checks 0 queries and the
workflow's "no changes" path takes over, same as any other transient
failure elsewhere in this repo - never a hard error that could break a
scheduled run.
"""
import json
import os
import sys
from datetime import date, datetime, timezone
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serpapi_client import fetch_ai_overview  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")
INSIGHTS_PATH = os.path.join(ROOT, "content/dashboard_insights.json")
OUT_DIR = os.path.join(ROOT, "content/aiVisibility")

# Capped deliberately - each query costs 2 SerpAPI calls, and this runs
# weekly against a dedicated free-tier key (250 searches/month). 4 active
# brands x 4 queries x 2 calls x ~4.3 weeks/month ~= 138/month, leaving
# real headroom for reruns/manual checks.
QUERIES_PER_BRAND = 4


def _select_queries(brand: str, insights: dict) -> list[dict]:
    """Top N queries for this brand, by impressions, deduped by keyword -
    pulled from REAL GSC demand the dashboard already computed
    (topOpportunities + risingQueries), not invented."""
    brand_data = insights.get(brand) or {}
    candidates = (brand_data.get("topOpportunities") or []) + (brand_data.get("risingQueries") or [])
    by_keyword: dict[str, dict] = {}
    for c in candidates:
        kw, page = c.get("keyword"), c.get("page")
        if not kw or not page:
            continue
        existing = by_keyword.get(kw)
        if not existing or c.get("impressions", 0) > existing.get("impressions", 0):
            by_keyword[kw] = c
    ranked = sorted(by_keyword.values(), key=lambda c: c.get("impressions", 0), reverse=True)
    return ranked[:QUERIES_PER_BRAND]


def _is_cited(references: list[dict], domain: str) -> tuple[bool, str | None, int | None]:
    """(cited, matched_url, 1-indexed position among references). Matches
    on the brand's bare apex domain (e.g. "aspose.com"), not a specific
    subdomain - confirmed live that an AI Overview can cite docs.aspose.com
    for an aspose.com query rather than the blog post itself, and that
    still counts as the brand being cited."""
    for i, ref in enumerate(references, start=1):
        if domain in urlparse(ref.get("link", "")).netloc:
            return True, ref.get("link"), i
    return False, None, None


def _other_domains(references: list[dict], own_domain: str) -> list[str]:
    seen: list[str] = []
    for ref in references:
        host = urlparse(ref.get("link", "")).netloc
        if host and own_domain not in host and host not in seen:
            seen.append(host)
    return seen


def check(brand: str, api_key: str) -> list[dict]:
    if not api_key:
        print("  SERPAPI_KEY_AI_VISIBILITY is not set - skipping (nothing checked, not an error).")
        return []

    try:
        with open(INSIGHTS_PATH, "r") as f:
            insights = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ⚠️  Could not read {INSIGHTS_PATH}: {e}")
        return []

    queries = _select_queries(brand, insights)
    if not queries:
        print(f"  No GSC opportunity/rising-query data for {brand} yet - nothing to check.")
        return []

    today = date.today().isoformat()
    checked_at = datetime.now(timezone.utc).isoformat()
    results: list[dict] = []

    for c in queries:
        query, page = c["keyword"], c["page"]
        result = fetch_ai_overview(query, api_key)
        if result is None:
            print(f"  ?  {query!r}: check failed, skipped")
            continue

        if not result.has_overview:
            print(f"  -  {query!r}: no AI Overview shown for this query")
            cited, cited_url, position, other = False, None, None, []
        else:
            cited, cited_url, position = _is_cited(result.references, brand)
            other = _other_domains(result.references, brand)
            status = f"cited at #{position}" if cited else "not cited"
            print(f"  {'✓' if cited else '✗'} {query!r}: {status}")

        results.append({
            "date": today,
            "checkedAt": checked_at,
            "query": query,
            "page": page,
            "hasOverview": result.has_overview,
            "cited": cited,
            "citedUrl": cited_url,
            "position": position,
            "otherDomains": other,
        })

    return results


def main():
    brand = sys.argv[1] if len(sys.argv) > 1 else "aspose.cloud"
    summary_file = None
    for arg in sys.argv[2:]:
        if arg.startswith("--summary-file="):
            summary_file = arg.split("=", 1)[1]

    # Prefers a dedicated key (its own free-tier quota, never competing
    # with keyword research) but falls back to the shared SERPAPI_KEY so
    # this works immediately without waiting on a new signup. That shared
    # key is on the free plan (250 searches/month, ~13 left as of
    # 2026-10-30) - fine to use now, but worth moving to a dedicated key
    # before running this on a wider query set.
    api_key = os.environ.get("SERPAPI_KEY_AI_VISIBILITY") or os.environ.get("SERPAPI_KEY", "")
    new_results = check(brand, api_key)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{brand}.json")
    prior: list[dict] = []
    if os.path.exists(out_path):
        try:
            with open(out_path, "r") as f:
                prior = json.load(f)
        except (json.JSONDecodeError, TypeError):
            prior = []

    combined = prior + new_results
    with open(out_path, "w") as f:
        json.dump(combined, f, indent=2)

    cited_count = sum(1 for r in new_results if r["cited"])
    print(f"\nWrote {out_path}: {len(new_results)} queries checked this run, {cited_count} cited.")

    if summary_file:
        with open(summary_file, "w") as f:
            if new_results:
                f.write(
                    f"AI visibility check for **{brand}** "
                    f"({cited_count}/{len(new_results)} tracked queries cited):\n\n"
                )
                for r in new_results:
                    if r["cited"]:
                        mark = "✓ cited"
                    elif not r["hasOverview"]:
                        mark = "no AI Overview"
                    else:
                        mark = "✗ not cited"
                    f.write(f"- {mark} — \"{r['query']}\" -> {r['page']}\n")
            else:
                f.write(f"No AI visibility results for **{brand}** this run (no key configured or no data).\n")


if __name__ == "__main__":
    main()
