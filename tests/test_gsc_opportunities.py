from agent_engine.blog_generator.utils.gsc_opportunities import (
    Opportunity,
    TREND_DECLINING,
    TREND_FLAT,
    TREND_IMPROVING,
    TREND_NEW,
    aggregate_queries,
    build_opportunities,
    find_best_topic,
    match_product_tab,
    product_slug_from_url,
    tokenize,
    topic_match_coverage,
)


def gsc_row(query: str, page: str, clicks: int, impressions: int, position: float) -> dict:
    return {"keys": [query, page], "clicks": clicks, "impressions": impressions, "position": position}


def sheet_row(status: str = "approved", **overrides) -> dict:
    row = {
        "status": status,
        "generated_title": "Convert PDF to Word in Python",
        "primary_keyword": "convert pdf to word python",
        "secondary_keywords": "pdf to docx python|python pdf converter",
        "long_tail_keywords": "how to convert pdf to word in python",
        "semantic_keywords": "pdf conversion|docx export",
    }
    row.update(overrides)
    return row


# ── tokenize ──────────────────────────────────────────────────────────────────

def test_tokenize_drops_function_words_but_keeps_formats() -> None:
    assert tokenize("How to Convert PDF to Word in Python") == ["convert", "pdf", "word", "python"]


def test_tokenize_keeps_meaningful_short_words() -> None:
    assert "online" in tokenize("excel online viewer")


# ── aggregate_queries ─────────────────────────────────────────────────────────

def test_aggregate_merges_pages_and_weights_position_by_impressions() -> None:
    stats = aggregate_queries([
        gsc_row("pdf to word", "https://b/x/", 1, 100, 10.0),
        gsc_row("pdf to word", "https://b/y/", 1, 300, 20.0),
    ])
    entry = stats["pdf to word"]
    assert entry["impressions"] == 400
    assert entry["position"] == (10.0 * 100 + 20.0 * 300) / 400
    assert entry["page"] == "https://b/y/"  # higher-impression page wins


# ── build_opportunities ───────────────────────────────────────────────────────

def test_position_band_and_impressions_floor_filter() -> None:
    recent = [
        gsc_row("too high", "https://b/a/", 5, 500, 3.0),     # already ranks well
        gsc_row("too low", "https://b/b/", 5, 500, 45.0),     # too far away
        gsc_row("too few", "https://b/c/", 1, 5, 12.0),       # below impressions floor
        gsc_row("just right", "https://b/d/", 5, 500, 12.0),
    ]
    opps = build_opportunities(recent, [], min_impressions=30, position_min=8, position_max=20, top_n=5)
    assert [o.keyword for o in opps] == ["just right"]
    assert opps[0].trend == TREND_NEW


def test_trend_computed_from_prior_window() -> None:
    recent = [
        gsc_row("improving kw", "https://b/a/", 5, 100, 10.0),
        gsc_row("declining kw", "https://b/b/", 5, 100, 15.0),
        gsc_row("flat kw", "https://b/c/", 5, 100, 12.0),
    ]
    prior = [
        gsc_row("improving kw", "https://b/a/", 5, 100, 15.0),
        gsc_row("declining kw", "https://b/b/", 5, 100, 10.0),
        gsc_row("flat kw", "https://b/c/", 5, 100, 12.5),
    ]
    by_kw = {o.keyword: o for o in build_opportunities(recent, prior, 30, 8, 20, 5)}
    assert by_kw["improving kw"].trend == TREND_IMPROVING
    assert by_kw["declining kw"].trend == TREND_DECLINING
    assert by_kw["flat kw"].trend == TREND_FLAT


def test_ranking_prefers_improving_over_declining_on_equal_impressions() -> None:
    recent = [
        gsc_row("up", "https://b/a/", 5, 100, 10.0),
        gsc_row("down", "https://b/b/", 5, 100, 15.0),
    ]
    prior = [
        gsc_row("up", "https://b/a/", 5, 100, 15.0),
        gsc_row("down", "https://b/b/", 5, 100, 10.0),
    ]
    opps = build_opportunities(recent, prior, 30, 8, 20, 5)
    assert [o.keyword for o in opps] == ["up", "down"]


def test_non_ascii_queries_are_dropped() -> None:
    recent = [
        gsc_row("psd轉jpg", "https://b/psd/x/", 5, 500, 12.0),
        gsc_row("psd to jpg", "https://b/psd/x/", 5, 500, 12.0),
    ]
    opps = build_opportunities(recent, [], 30, 8, 20, 5)
    assert [o.keyword for o in opps] == ["psd to jpg"]


def test_top_n_limits_results() -> None:
    recent = [gsc_row(f"kw {i}", "https://b/a/", 1, 100 + i, 12.0) for i in range(10)]
    assert len(build_opportunities(recent, [], 30, 8, 20, 5)) == 5


# ── product tab matching ──────────────────────────────────────────────────────

def test_product_slug_from_url() -> None:
    assert product_slug_from_url("https://blog.aspose.cloud/cells/compress-excel/") == "cells"
    assert product_slug_from_url("https://blog.aspose.cloud/tag/scan-pdf/") == ""
    assert product_slug_from_url("https://blog.aspose.cloud/") == ""


def test_match_product_tab_prefers_url_slug() -> None:
    opp = Opportunity("compress excel file", "https://b/cells/compress-excel/", 100, 5, 12.0, TREND_FLAT)
    assert match_product_tab(opp, ["PDF", "Cells", "HTML"]) == "Cells"


def test_match_product_tab_falls_back_to_keyword_token() -> None:
    opp = Opportunity("html to pdf converter", "https://b/tag/foo/", 100, 5, 12.0, TREND_FLAT)
    assert match_product_tab(opp, ["PDF", "Cells", "HTML"]) == "HTML"  # first token match wins


def test_match_product_tab_returns_empty_when_unknown() -> None:
    opp = Opportunity("compress video", "https://b/tag/foo/", 100, 5, 12.0, TREND_FLAT)
    assert match_product_tab(opp, ["PDF", "Cells"]) == ""


# ── topic matching ────────────────────────────────────────────────────────────

def test_coverage_full_match() -> None:
    assert topic_match_coverage("convert pdf to word python", sheet_row()) == 1.0


def test_find_best_topic_skips_unapproved_rows() -> None:
    rows = [sheet_row(status="Generated"), sheet_row(status="pending")]
    assert find_best_topic("convert pdf to word python", rows, 0.7) is None


def test_find_best_topic_returns_sheet_row_number() -> None:
    rows = [sheet_row(status="Generated"), sheet_row(status="Approved")]
    best = find_best_topic("convert pdf to word python", rows, 0.7)
    assert best is not None
    row_number, row, coverage = best
    assert row_number == 3  # second data row, after header
    assert coverage == 1.0


def test_find_best_topic_rejects_below_threshold() -> None:
    rows = [sheet_row(generated_title="Merge Excel Sheets in Java",
                      primary_keyword="merge excel java",
                      secondary_keywords="", long_tail_keywords="", semantic_keywords="")]
    assert find_best_topic("convert pdf to word python", rows, 0.7) is None


def test_find_best_topic_picks_highest_coverage() -> None:
    weak = sheet_row(primary_keyword="pdf converter python",
                     generated_title="PDF Converter in Python",
                     secondary_keywords="", long_tail_keywords="", semantic_keywords="")
    strong = sheet_row()
    best = find_best_topic("convert pdf to word python", [weak, strong], 0.5)
    assert best is not None
    assert best[0] == 3  # the strong row
