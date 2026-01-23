from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


# -----------------------------
# Exclusion: Release / Updates
# -----------------------------
_RELEASE_PATTERNS = [
    r"\brelease\s*notes?\b",
    r"\bproduct\s*updates?\b",
    r"\bproduct\s*release(s)?\b",
    r"\bversion\s*updates?\b",
    r"\bv?\d+(\.\d+){1,3}\b",  # versions like 23.5, v24.1.2
    r"\b(beta|rc|ga)\b",
    r"\bwhat'?s\s*new\b",
    r"\bnew\s*release\b",
]
_RELEASE_RE = re.compile("|".join(_RELEASE_PATTERNS), re.IGNORECASE)


def _text_blob_for_row(row: Dict[str, Any]) -> str:
    """
    coverage.json row shape:
      {category, sub_category, topic, coverage{platform{title,url,topic,...}}}
    """
    parts = [
        str(row.get("topic", "") or ""),
        str(row.get("category", "") or ""),
        str(row.get("sub_category", "") or ""),
    ]
    cov = row.get("coverage", {}) or {}
    for _, cell in cov.items():
        if isinstance(cell, dict):
            parts.append(str(cell.get("title", "") or ""))
            parts.append(str(cell.get("topic", "") or ""))
            parts.append(str(cell.get("url", "") or ""))
    return " ".join(parts)


def _is_release_update_row(row: Dict[str, Any]) -> bool:
    return bool(_RELEASE_RE.search(_text_blob_for_row(row)))


# -----------------------------
# Core datamodel
# -----------------------------
@dataclass(frozen=True)
class GapRow:
    category: str
    sub_category: str
    topic: str
    missing_platforms: Tuple[str, ...]
    present_platforms: Tuple[str, ...]


# -----------------------------
# Helpers
# -----------------------------
def _as_bool(v: Any) -> bool:
    return bool(v) is True


def _coverage_bool(cell: Dict[str, Any]) -> bool:
    return _as_bool(cell.get("matched", False))


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    out: List[str] = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def _status_for_pct(pct: float) -> str:
    """
    Simple, deterministic status mapping for dashboard visuals.
    """
    if pct >= 80:
        return "🟢 Strong"
    if pct >= 60:
        return "🟡 Moderate"
    return "🔴 Weak"


def _extract_filtered_rows(coverage_json: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Returns (filtered_rows, excluded_count).
    Filtering is applied consistently across *all* analytics and gaps.
    """
    rows = coverage_json.get("rows", []) or []
    excluded = 0
    kept: List[Dict[str, Any]] = []
    for r in rows:
        if _is_release_update_row(r):
            excluded += 1
            continue
        kept.append(r)
    return kept, excluded


def _extract_gap_rows(filtered_rows: List[Dict[str, Any]], platforms: List[str]) -> List[GapRow]:
    gap_rows: List[GapRow] = []
    for r in filtered_rows:
        category = r.get("category", "") or ""
        sub_category = r.get("sub_category", "") or ""
        topic = r.get("topic", "") or ""
        cov = r.get("coverage", {}) or {}

        present = [p for p in platforms if _coverage_bool(cov.get(p, {}))]
        missing = [p for p in platforms if p not in present]

        if missing:
            gap_rows.append(
                GapRow(
                    category=category,
                    sub_category=sub_category,
                    topic=topic,
                    missing_platforms=tuple(missing),
                    present_platforms=tuple(present),
                )
            )
    return gap_rows


# -----------------------------
# Main renderer
# -----------------------------
def render_gaps_md(title: str, coverage_json: Dict[str, Any]) -> str:
    """
    Generate a structured gap analysis report from coverage.json only.
    Adds a dashboard-style Executive Summary and excludes release/update rows.
    """
    case = coverage_json.get("case", "") or ""
    platforms: List[str] = coverage_json.get("platforms", []) or []
    baseline: str = coverage_json.get("baseline_platform", "") or ""

    # Apply exclusions once, use consistently everywhere
    filtered_rows, excluded = _extract_filtered_rows(coverage_json)

    total_rows = len(filtered_rows)
    gap_rows = _extract_gap_rows(filtered_rows, platforms)

    gap_count = len(gap_rows)
    fully_covered = total_rows - gap_count
    gap_pct = (gap_count / total_rows * 100.0) if total_rows else 0.0

    # Per-platform coverage counts (on FILTERED rows only)
    platform_covered_counts = Counter()
    for r in filtered_rows:
        cov = r.get("coverage", {}) or {}
        for p in platforms:
            if _coverage_bool(cov.get(p, {})):
                platform_covered_counts[p] += 1

    # Gap frequency per platform (how often each platform is missing across gap rows)
    platform_missing_counts = Counter()
    for gr in gap_rows:
        for p in gr.missing_platforms:
            platform_missing_counts[p] += 1

    # Cluster gaps by (category, sub_category)
    cluster_to_topics: Dict[Tuple[str, str], List[GapRow]] = defaultdict(list)
    for gr in gap_rows:
        cluster_to_topics[(gr.category, gr.sub_category)].append(gr)

    def cluster_score(items: List[GapRow]) -> int:
        return sum(len(x.missing_platforms) for x in items)

    ranked_clusters = sorted(
        cluster_to_topics.items(),
        key=lambda kv: (cluster_score(kv[1]), len(kv[1])),
        reverse=True,
    )

    # High priority topics: top clusters → top topics missing on most platforms
    high_priority: List[Tuple[str, str, GapRow]] = []
    for (cat, sub), items in ranked_clusters[:8]:
        items_sorted = sorted(items, key=lambda x: len(x.missing_platforms), reverse=True)
        for gr in items_sorted[:2]:
            high_priority.append((cat, sub, gr))
    high_priority = high_priority[:15]

    # Quick wins: missing on many platforms but present on baseline (if baseline is a platform key)
    baseline_key = baseline if baseline in platforms else None
    quick_wins: List[GapRow] = []
    for gr in gap_rows:
        if baseline_key and (baseline_key in gr.present_platforms) and len(gr.missing_platforms) >= max(
            2, (len(platforms) // 2)
        ):
            quick_wins.append(gr)
    quick_wins = sorted(quick_wins, key=lambda x: len(x.missing_platforms), reverse=True)[:12]

    # Cross-link placeholders (will become URL-based once you use URLs from coverage.json cells)
    cross_links: List[List[str]] = []
    for gr in quick_wins[:8]:
        src = f"{baseline} coverage: {gr.topic}" if baseline else f"Well-covered topic: {gr.topic}"
        tgt = f"New guides for: {', '.join(gr.missing_platforms[:4])}" + ("..." if len(gr.missing_platforms) > 4 else "")
        anchor = f"{gr.topic} in {', '.join(gr.missing_platforms[:2])}" if gr.missing_platforms else gr.topic
        cross_links.append([src, tgt, anchor])

    # -----------------------------
    # Render
    # -----------------------------
    out: List[str] = []
    out.append(f"# {title}")
    out.append("")
    out.append("---")
    out.append("")

    # Dashboard-style Executive Summary
    out.append("## 📊 Coverage Performance Overview")
    out.append("")
    out.append(
        _md_table(
            ["🧩 Metric", "Value", "Status"],
            [
                ["**Total Canonical Topics**", f"**{total_rows}**", "—"],
                ["**Topics with Gaps**", f"**{gap_count}**", "⚠️" if gap_count else "✅"],
                ["**Fully Covered Topics**", str(fully_covered), "✅" if fully_covered else "—"],
                ["**Excluded (Release / Updates)**", str(excluded), "ℹ️"],
                ["**Baseline Scope**", baseline or "all", "—"],
                ["**Case**", case, "—"],
            ],
        )
    )
    out.append("")
    out.append("---")
    out.append("")

    out.append("### 🟢 Coverage Health")
    out.append("")
    parity_status = _status_for_pct(100.0 - gap_pct)  # parity improves as gaps decrease
    porting_status = "🔥 Very High" if gap_pct >= 40 else ("✅ High" if gap_pct >= 20 else "🟢 Low")
    out.append(
        _md_table(
            ["Indicator", "Score", "Interpretation"],
            [
                ["Cross-Platform Parity", f"{100.0 - gap_pct:.1f}%", parity_status],
                ["Content Reusability", "High", "✅ Strong"],
                ["Porting Opportunity", f"{gap_pct:.1f}% gaps", porting_status],
                ["Excluded Noise (Releases)", str(excluded), "✅ Controlled"],
            ],
        )
    )
    out.append("")
    out.append("---")
    out.append("")

    out.append("### 🧩 Platform Coverage Snapshot")
    out.append("")
    plat_snapshot_rows: List[List[str]] = []
    for p in platforms:
        covered = platform_covered_counts.get(p, 0)
        missing = platform_missing_counts.get(p, 0)
        pct = (covered / total_rows * 100.0) if total_rows else 0.0
        plat_snapshot_rows.append([f"**{p}**", str(covered), str(missing), f"{_status_for_pct(pct)} ({pct:.1f}%)"])
    out.append(_md_table(["Platform", "# Covered", "# Missing", "Coverage"], plat_snapshot_rows))
    out.append("")
    out.append("---")
    out.append("")

    out.append("### 🔎 Executive Insights")
    out.append("")
    out.append(f"- **{gap_pct:.1f}%** of canonical topics are missing on at least one platform (after exclusions).")
    if platform_missing_counts:
        worst = platform_missing_counts.most_common(3)
        out.append(f"- Highest gap density: {', '.join(f'**{p}** ({c} missing)' for p, c in worst)}.")
    out.append(f"- Gaps are concentrated in **{min(8, len(ranked_clusters))}** major category/subcategory clusters (see Section 4).")
    out.append("- Release notes, product updates, and version announcements are intentionally excluded from this report.")
    out.append("")

    out.append("---")
    out.append("")
    out.append("## 2. High-Priority Topics to Port / Adapt (Top recommendations)")
    out.append("")
    if not high_priority:
        out.append("No high-priority gaps were identified from the current coverage map.")
        out.append("")
    else:
        hp_rows: List[List[str]] = []
        for i, (cat, sub, gr) in enumerate(high_priority, start=1):
            missing = ", ".join(gr.missing_platforms[:6]) + ("..." if len(gr.missing_platforms) > 6 else "")
            suggested_titles = "; ".join([f"{gr.topic} — {p}" for p in gr.missing_platforms[:3]])
            hp_rows.append([str(i), f"**{cat} / {sub}**", gr.topic, missing, suggested_titles])

        out.append(
            _md_table(
                ["#", "Cluster", "Representative topic", "Missing platforms (high-impact)", "Suggested new titles (examples)"],
                hp_rows,
            )
        )
        out.append("")
        out.append(
            "*These recommendations are derived from topics missing across the largest number of platforms and clustered by category/subcategory.*"
        )
        out.append("")

    out.append("---")
    out.append("")
    out.append("## 3. Platform Gap Analysis")
    out.append("")
    plat_rows: List[List[str]] = []
    for p in platforms:
        covered = platform_covered_counts.get(p, 0)
        missing = platform_missing_counts.get(p, 0)
        pct = (covered / total_rows * 100.0) if total_rows else 0.0
        plat_rows.append([f"**{p}**", str(covered), f"{pct:.1f}%", str(missing)])
    out.append(_md_table(["Platform", "# topics covered", "% of baseline rows", "# topics missing"], plat_rows))
    out.append("")
    out.append(
        "**Takeaway:** Focus first on platforms with the highest missing counts and lowest coverage percentage; port high-impact topics from the best-covered platform first."
    )
    out.append("")

    out.append("---")
    out.append("")
    out.append("## 4. Content Clusters (grouped gaps)")
    out.append("")
    cluster_rows: List[List[str]] = []
    for (cat, sub), items in ranked_clusters[:12]:
        missing_signals = sum(len(x.missing_platforms) for x in items)
        miss_counter = Counter()
        for it in items:
            miss_counter.update(it.missing_platforms)
        top_missing = ", ".join([p for p, _ in miss_counter.most_common(4)])
        cluster_rows.append([f"**{cat} / {sub}**", str(len(items)), str(missing_signals), top_missing])
    if cluster_rows:
        out.append(_md_table(["Cluster", "# gap topics", "Missing signals", "Most-missed platforms"], cluster_rows))
        out.append("")
    else:
        out.append("No clusters found (no gaps).")
        out.append("")

    out.append("---")
    out.append("")
    out.append("## 5. Quick Wins (low-effort expansions)")
    out.append("")
    if not quick_wins:
        out.append(
            "No quick wins detected with the current heuristic. "
            "Quick wins are defined as topics present on the baseline but missing on many other platforms."
        )
        out.append("")
    else:
        qw_rows: List[List[str]] = []
        for gr in quick_wins:
            missing = ", ".join(gr.missing_platforms[:6]) + ("..." if len(gr.missing_platforms) > 6 else "")
            effort = "1–2 days per platform" if len(gr.missing_platforms) >= 4 else "1 day per platform"
            qw_rows.append([gr.topic, missing, effort])
        out.append(_md_table(["Quick-win topic", "Missing platforms", "Estimated effort"], qw_rows))
        out.append("")
        out.append(
            "*Heuristic: topics missing across many platforms but already present on baseline are prime candidates for rapid porting/adaptation.*"
        )
        out.append("")

    out.append("---")
    out.append("")
    out.append("## 6. Cross-Linking Opportunities")
    out.append("")
    if not cross_links:
        out.append("No cross-link suggestions generated (insufficient quick wins).")
        out.append("")
    else:
        out.append(_md_table(["Source (well-covered)", "Target (gap)", "Suggested anchor text"], cross_links))
        out.append("")
        out.append(
            "*Once coverage cells include canonical URLs per platform, this section can generate concrete link pairs (source URL → target URL).*"
        )
        out.append("")

    out.append("---")
    out.append("")
    out.append("### Bottom Line")
    out.append("")
    out.append(
        "Prioritize porting/adapting high-impact baseline topics to the most under-covered platforms. "
        "Use the cluster table to organize work into repeatable series and publish platform-specific guides with consistent cross-linking."
    )
    out.append("")

    return "\n".join(out)
