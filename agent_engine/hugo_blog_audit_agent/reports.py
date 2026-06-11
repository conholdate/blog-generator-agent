from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
import re

from .models import AuditResult, Issue, Post


def write_reports(
    result: AuditResult,
    output_dir: Path,
    include_suggestions: bool,
    draft_fixes: bool,
    max_draft_fixes: int | None,
    priority_only: bool,
    detailed_outputs: bool = False,
    run_context: dict[str, object] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_action_items(result, output_dir / "audit-action-items.md", detailed_outputs, run_context)
    if detailed_outputs:
        write_complete_seo_audit(result, output_dir / "complete-seo-audit.md")
        write_summary(result, output_dir / "audit-summary.md")
        write_code_audit(result, output_dir / "code-audit.md")
        write_post_csv(result.posts, output_dir / "post-audit.csv")
        (output_dir / "post-audit.json").write_text(json.dumps([post_to_dict(p) for p in result.posts], indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        write_issue_report(output_dir / "technical-seo-audit.md", "Technical SEO Audit", result.technical_issues)
        write_issue_report(output_dir / "internal-linking-audit.md", "Internal Linking Audit", result.internal_link_issues)
        write_content_plan(result, output_dir / "content-improvement-plan.md", include_suggestions)
        write_quick_wins(result, output_dir / "quick-wins.md")
    if draft_fixes:
        write_draft_fixes(result, output_dir / "draft-fixes", max_draft_fixes, priority_only)


def post_to_dict(post: Post) -> dict:
    data = asdict(post)
    data["path"] = str(post.path)
    return data


def write_complete_seo_audit(result: AuditResult, path: Path) -> None:
    posts = result.posts
    english_posts = [p for p in posts if p.language == "en"]
    primary_posts = english_posts or posts
    all_issues = [i for p in posts for i in p.issues] + result.technical_issues + result.internal_link_issues
    severity_counts = Counter(i.severity for i in all_issues)
    issue_counts = Counter(i.issue_type for i in all_issues)
    top_posts = sorted(posts, key=lambda p: p.scores.get("priority", 0), reverse=True)[:25]
    score_rows = seo_scorecard_rows(result)
    overall_score = next((row[1] for row in score_rows if row[0] == "Overall SEO Health"), "0")
    lines = [
        "# Complete SEO Audit Report",
        "",
        "## Executive Summary",
        f"This local audit scanned {len(posts)} Markdown files for {result.config.blog_name}. It found {len(all_issues)} total issues across content quality, on-page SEO, technical Hugo SEO, internal linking, multilingual SEO, and audience fit.",
        f"The estimated overall SEO health score is {overall_score}/100. The highest-leverage work is to fix high-severity content gaps, improve developer-intent completeness, repair internal linking weaknesses, and tighten translation metadata.",
        "",
        f"- Repository: `{result.repo_root}`",
        f"- Audience profile: {result.config.audience_profile or 'General blog audience'}",
        f"- Markdown files scanned: {len(posts)}",
        f"- Languages detected: {len(sorted({p.language for p in posts}))}",
        f"- Translation groups: {len(result.groups)}",
        f"- Total issues: {len(all_issues)}",
        "",
        "## SEO Scorecard",
        *markdown_table(["Area", "Score", "Interpretation"], score_rows),
        "",
        "## Issue Summary",
        "",
        "### Issues By Severity",
        *markdown_table(["Severity", "Count"], [[sev, str(severity_counts.get(sev, 0))] for sev in ["Critical", "High", "Medium", "Low", "Opportunity"]]),
        "",
        "### Top Issue Types",
        *markdown_table(["Issue Type", "Count"], [[issue_type, str(count)] for issue_type, count in issue_counts.most_common(20)]),
        "",
        "### Top Priority Posts",
        *markdown_table(
            ["File", "Language", "Priority", "Issues", "Top Issue", "Recommended Action"],
            [
                [
                    f"`{p.relative_path}`",
                    p.language,
                    str(p.scores.get("priority", 0)),
                    str(len(p.issues)),
                    p.issues[0].issue_type if p.issues else "",
                    p.issues[0].recommended_fix if p.issues else "Monitor and refresh as needed.",
                ]
                for p in top_posts
            ],
        ),
        "",
        "## Per-Post SEO Segment Score Table",
        "All scanned posts are listed below, sorted by priority score. Each SEO audit segment is shown as a column for direct post-by-post comparison.",
        "",
        *markdown_table(
            [
                "Blog Post",
                "Title",
                "Language",
                "Content Quality",
                "On-Page SEO",
                "Technical SEO",
                "Internal Linking",
                "Translation SEO",
                "Developer Audience Fit",
                "Growth Opportunity",
                "Priority",
                "Issues",
                "Top Issues",
            ],
            post_score_rows(posts),
        ),
        "",
        "## Content Quality Audit",
        "Developer and file-format processing content should satisfy a concrete task, show working code, explain setup, clarify input/output formats, and provide troubleshooting or limitations.",
        "",
        *markdown_table(["Signal", "Count", "Share"], content_signal_rows(primary_posts)),
        "",
        "### Content Quality Recommendations",
        "- Expand posts under 800 words with complete steps, screenshots, examples, edge cases, and conclusions.",
        "- Add runnable examples to developer-intent pages that currently have no fenced code block.",
        "- Add FAQ sections where query intent includes setup, supported formats, licensing, errors, or output expectations.",
        "- Remove placeholder/template wording and review possible encoding artifacts before publication.",
        "",
        "## Developer Audience Fit",
        "The target reader is a developer or technical evaluator using Aspose APIs for document and file-format processing. Posts should make the SDK, language, input/output format, and integration path obvious.",
        "",
        *markdown_table(["Signal", "Count", "Share"], developer_audience_rows(primary_posts)),
        "",
        "### Audience-Fit Recommendations",
        "- Include install/setup commands for the relevant package manager: NuGet, Maven, pip, npm, Composer, Gradle, or Android setup as applicable.",
        "- Include a complete code path: load input, call API, save output, and mention expected output.",
        "- Link to API reference, product page, release package, docs, and sample repository when relevant.",
        "- Add troubleshooting notes for licensing, large files, unsupported formats, exceptions, and performance.",
        "",
        "## On-Page SEO Audit",
        *markdown_table(["Signal", "Count"], metadata_signal_rows(primary_posts)),
        "",
        "### On-Page Recommendations",
        "- Rewrite duplicate or weak descriptions so each URL has a distinct search promise.",
        "- Keep titles concise while preserving language/platform, file format, and task intent.",
        "- Add descriptive image alt text and align headings with task-based search subtopics.",
        "- Add FAQPage or HowTo schema only where page content actually supports it.",
        "",
        "## Technical Hugo SEO",
        *issue_table(result.technical_issues),
        "",
        "### Technical Recommendations",
        "- Validate rendered canonical, hreflang, Open Graph, Twitter card, schema, sitemap, and robots behavior with a local Hugo build.",
        "- Review taxonomy, pagination, and translation pages for duplicate-content and index-bloat risks.",
        "",
        "## Internal Linking Audit",
        *markdown_table(
            ["Signal", "Count"],
            [
                ["Internal linking issues", str(len(result.internal_link_issues))],
                ["Orphan posts", str(sum(1 for i in result.internal_link_issues if i.issue_type == "orphan_post"))],
                ["Too few outgoing internal links", str(sum(1 for i in result.internal_link_issues if i.issue_type == "too_few_outgoing_internal_links"))],
                ["Broken internal links", str(sum(1 for i in result.internal_link_issues if i.issue_type == "broken_internal_link"))],
                ["Weak anchor text", str(sum(1 for i in result.internal_link_issues if i.issue_type == "weak_anchor_text"))],
            ],
        ),
        "",
        "### Internal Linking Recommendations",
        "- Add contextual links from older release posts to current evergreen tutorials.",
        "- Link every tutorial to related conversion, creation, editing, and API reference pages.",
        "- Use descriptive anchors that include the file format, language, or developer task.",
        "",
        "## Multilingual SEO",
        *markdown_table(
            ["Signal", "Count"],
            [
                ["Translation groups", str(len(result.groups))],
                ["Groups missing configured languages", str(sum(1 for g in result.groups if g.missing_languages))],
                ["Groups with translation issues", str(sum(1 for g in result.groups if g.issues))],
                ["Detected languages", str(len(sorted({p.language for p in posts})))],
            ],
        ),
        "",
        "### Multilingual Recommendations",
        "- Prioritize missing translations for high-value product families and languages with proven demand.",
        "- Localize titles and descriptions instead of copying English metadata.",
        "- Validate hreflang/canonical templates in rendered HTML before expanding translation scale.",
        "",
        "## Content Inventory Trends",
        "",
        "### Posts By Year",
        *markdown_table(["Year", "Posts"], year_rows(primary_posts)),
        "",
        "### Product-Family Distribution",
        *markdown_table(["Product", "Posts"], product_rows(primary_posts)),
        "",
        "## Priority Roadmap",
        *markdown_table(
            ["Priority", "Action", "Reason"],
            [
                ["P0", "Fix broken internal links and high-severity metadata/content issues.", "These issues directly affect crawl quality, user trust, and search relevance."],
                ["P0", "Validate rendered canonical, hreflang, sitemap, and robots output.", "Local Markdown checks cannot fully confirm rendered Hugo SEO behavior."],
                ["P1", "Refresh high-priority developer tutorials with code, setup, output examples, and troubleshooting.", "This best matches the target developer audience and likely search intent."],
                ["P1", "Repair duplicate descriptions, weak titles, and missing API/reference links.", "Improves CTR, page differentiation, and technical evaluator confidence."],
                ["P2", "Consolidate or redirect thin legacy release posts into evergreen guides where appropriate.", "Reduces low-value archive weight and cannibalization risk."],
                ["P2", "Improve translation coverage and localized metadata for priority languages.", "Expands international search reach without scaling low-quality translations."],
            ],
        ),
        "",
        "## Appendix",
        "- Detailed row-level data: `post-audit.csv` and `post-audit.json`.",
        "- Consolidated action backlog: `audit-action-items.md`.",
        "- Technical details: `technical-seo-audit.md`.",
        "- Multilingual SEO details are included in this report and `post-audit.json`.",
        "- Internal linking details: `internal-linking-audit.md`.",
        "- Quick fixes: `quick-wins.md`.",
        "- Run logs and metrics: `audit-run.log` and `audit-metrics.json`.",
        "",
        "## Known Limitations",
        "- This report is generated from local repository files and does not crawl the live website.",
        "- Rendered Hugo output should be validated separately for final canonical, hreflang, sitemap, robots, schema, and social metadata behavior.",
        "- Traffic impact estimates are heuristic unless Search Console, analytics, or rank-tracking exports are integrated.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(result: AuditResult, path: Path) -> None:
    posts = result.posts
    langs = sorted({p.language for p in posts})
    all_issues = [i for p in posts for i in p.issues] + result.technical_issues + result.internal_link_issues
    top_posts = sorted(posts, key=lambda p: p.scores.get("priority", 0), reverse=True)[:10]
    english_posts = [p for p in posts if p.language == "en"]
    lines = [
        "# Audit Summary",
        "",
        "## Executive Summary",
        f"Scanned {len(posts)} Markdown files across {len(langs)} detected languages. The strongest opportunities are metadata cleanup, internal linking, translation coverage validation, and content expansion for thin or weakly structured posts.",
        "",
        f"- Total Markdown files scanned: {len(posts)}",
        f"- Total blog posts detected: {len(posts)}",
        f"- Total languages detected: {len(langs)} ({', '.join(langs)})",
        f"- Translation groups: {len(result.groups)}",
        f"- Total issues: {len(all_issues)}",
        f"- Audience profile: {result.config.audience_profile or 'General blog audience'}",
        "",
        "## Audit Segment Summary",
        *markdown_table(
            ["Segment", "Scope", "Key Metric", "Issues", "Status", "Detailed Report"],
            audit_segment_summary_rows(result),
        ),
        "",
        "## Repository Signal Tables",
        "",
        "### Developer Audience Fit Signals",
        *markdown_table(["Signal", "Count", "Share"], developer_audience_rows(english_posts or posts)),
        "",
        "### Content Depth Signals",
        *markdown_table(["Signal", "Count", "Share"], content_signal_rows(english_posts or posts)),
        "",
        "### Metadata CTR Signals",
        *markdown_table(["Signal", "Count"], metadata_signal_rows(english_posts or posts)),
        "",
        "### Posts By Year",
        *markdown_table(["Year", "Posts"], year_rows(english_posts or posts)),
        "",
        "### Product-Family Distribution",
        *markdown_table(["Product", "Posts"], product_rows(english_posts or posts)),
        "",
        "## Highest-Priority Posts",
        *markdown_table(
            ["File", "Priority", "Issues", "Top Issue", "Recommended Action"],
            [
                [
                    f"`{p.relative_path}`",
                    str(p.scores.get("priority", 0)),
                    str(len(p.issues)),
                    p.issues[0].issue_type if p.issues else "",
                    p.issues[0].recommended_fix if p.issues else "Monitor and refresh as needed.",
                ]
                for p in top_posts
            ],
        ),
        "",
        "## Severity Summary",
        *markdown_table(
            ["Severity", "Issue Count"],
            [[severity, str(sum(1 for item in all_issues if item.severity == severity))] for severity in ["Critical", "High", "Medium", "Low", "Opportunity"]],
        ),
        "",
        "## Recommended 30-Day Action Plan",
        "1. Fix broken internal links, missing descriptions, duplicate metadata, and missing alt text.",
        "2. Improve the top 10 priority posts with stronger intros, examples, FAQs, conclusions, and CTAs.",
        "3. Add internal links from related posts to orphan content and key conversion pages.",
        "4. Review translation groups for missing languages and unlocalized titles/descriptions.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_post_csv(posts: list[Post], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "file_path", "detected_language", "translation_group", "title", "description", "word_count",
            "content_score", "seo_score", "technical_score", "internal_linking_score", "translation_score",
            "priority_score", "issue_count", "top_issues", "recommended_action",
        ])
        writer.writeheader()
        for post in posts:
            writer.writerow({
                "file_path": post.relative_path,
                "detected_language": post.language,
                "translation_group": post.translation_group,
                "title": post.title,
                "description": post.description,
                "word_count": post.word_count,
                "content_score": post.scores.get("content_quality", 0),
                "seo_score": post.scores.get("on_page_seo", 0),
                "technical_score": post.scores.get("technical_seo", 0),
                "internal_linking_score": post.scores.get("internal_linking", 0),
                "translation_score": post.scores.get("translation_seo", 0),
                "priority_score": post.scores.get("priority", 0),
                "issue_count": len(post.issues),
                "top_issues": "; ".join(i.issue_type for i in post.issues[:5]),
                "recommended_action": post.issues[0].recommended_fix if post.issues else "Monitor and refresh as needed.",
            })


def write_issue_report(path: Path, title: str, issues: list[Issue]) -> None:
    lines = [f"# {title}", ""]
    if not issues:
        lines.append("No issues detected in this area.")
    else:
        lines += issue_table(issues)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_code_audit(result: AuditResult, path: Path) -> None:
    code_issues = [issue for post in result.posts for issue in post.issues if issue.issue_type in code_issue_types()]
    posts_with_code = [post for post in result.posts if post.code_samples]
    api_sources = sdk_reference_rows(result)
    class_resolution_rows = code_class_resolution_rows(code_issues)
    lines = [
        "# Code Audit",
        "",
        "## Summary",
        f"- Posts scanned: {len(result.posts)}",
        f"- Posts with fenced code blocks: {len(posts_with_code)}",
        f"- Code blocks found: {sum(len(post.code_samples) for post in result.posts)}",
        f"- Code/API issues found: {len(code_issues)}",
        f"- SDK validation enabled: {bool(result.config.sdk_validation.get('enabled'))}",
        "",
        "## API Reference Sources",
        "The agent validates SDK classes by indexing configured product API reference repositories. For product-scoped audits, these references are derived from the selected product config where available.",
        "",
        *markdown_table(["Source", "Product", "Path", "Namespaces", "Symbols Indexed"], api_sources),
        "",
        "## Per-Post Code Coverage",
        *markdown_table(
            ["Blog Post", "Title", "Language", "Code Blocks", "Code Issues", "Top Code Issues"],
            [
                [
                    f"`{post.relative_path}`",
                    post.title,
                    post.language,
                    str(len(post.code_samples)),
                    str(sum(1 for issue in post.issues if issue.issue_type in code_issue_types())),
                    "; ".join(issue.issue_type for issue in post.issues if issue.issue_type in code_issue_types())[:240],
                ]
                for post in sorted(result.posts, key=lambda item: sum(1 for issue in item.issues if issue.issue_type in code_issue_types()), reverse=True)
            ],
        ),
        "",
        "## Class/Member Resolution Details",
        "Missing or deprecated SDK classes, properties, and members are listed here with the closest existing indexed-symbol suggestions when the API reference data can support them.",
        "",
        *markdown_table(["File", "Code Line", "Referenced Class/Member", "Status", "Suggested Existing Symbol/Fix"], class_resolution_rows),
        "",
        "## Code/API Issues",
        *issue_table(code_issues),
        "",
        "## Checks Applied",
        "- Validates Aspose import/module names against configured SDK namespaces.",
        "- Validates imported or fully qualified classes against symbols indexed from API reference repositories.",
        "- Flags configured deprecated or renamed SDK symbols.",
        "- Optionally validates Python imports at runtime when `runtime_import_check` is enabled and target SDKs are installed.",
        "",
        "## Known Limits",
        "- Static validation focuses on explicit imports and fully qualified symbols; it does not execute snippets.",
        "- Method-level validation depends on how completely the API reference repository exposes method names.",
        "- If an API reference repository cannot be cloned or opened, the audit logs the skip and continues.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_action_items(result: AuditResult, path: Path, detailed_outputs: bool = False, run_context: dict[str, object] | None = None) -> None:
    items = audit_action_items(result)
    severity_counts = Counter(item["severity"] for item in items)
    priority_counts = Counter(item["priority"] for item in items)
    area_counts = Counter(item["area"] for item in items)
    quick_wins = [item for item in items if item["effort"] == "Low"]
    llm_rows = llm_suggestion_rows(result)
    lines = [
        "# Audit Action Items",
        "",
        f"Consolidated actionable backlog for {result.config.blog_name}. This combines post-level, technical SEO, internal linking, multilingual, content, on-page SEO, and code/API findings from the audit output.",
        "",
        "## Audit Run",
        *markdown_table(["Field", "Value"], audit_run_rows(result, run_context, detailed_outputs)),
        "",
        "## Summary",
        *markdown_table(
            ["Metric", "Count"],
            [
                ["Total scanned blog posts", str(len(result.posts))],
                ["Total action items", str(len(items))],
                ["P0 action items", str(priority_counts.get("P0", 0))],
                ["P1 action items", str(priority_counts.get("P1", 0))],
                ["Low-effort quick wins", str(len(quick_wins))],
                ["Critical issues", str(severity_counts.get("Critical", 0))],
                ["High issues", str(severity_counts.get("High", 0))],
                ["Medium issues", str(severity_counts.get("Medium", 0))],
                ["Low issues", str(severity_counts.get("Low", 0))],
                ["Opportunity issues", str(severity_counts.get("Opportunity", 0))],
            ],
        ),
        "",
        "## Items By Area",
        *markdown_table(["Area", "Action Items"], [[area, str(count)] for area, count in area_counts.most_common()]),
        "",
        "## All Action Items",
        "Action items are grouped by affected post. The post heading carries the file path, so the tables omit the repeated file column.",
        "",
        *grouped_action_item_sections(items, result),
        "",
    ]
    if llm_rows:
        lines += [
            "## LLM Suggestions",
            *markdown_table(
                ["File", "Model", "Cached", "Summary", "Suggested Title", "Suggested Description", "Content Actions", "FAQ Questions", "Risk Notes"],
                llm_rows,
            ),
            "",
        ]
    lines += [
        "## Detailed Source Reports",
        "Detailed reports are generated only when `--detailed-outputs true` is passed.",
    ]
    if detailed_outputs:
        lines += [
            "",
            "- `complete-seo-audit.md`: segment scorecard, priority roadmap, and per-post SEO score table.",
            "- `content-improvement-plan.md`: post-level content refresh guidance.",
            "- `code-audit.md`: SDK/API validation details.",
            "- `technical-seo-audit.md`: Hugo config, template, robots, schema, and social metadata findings.",
            "- `internal-linking-audit.md`: broken links, orphan posts, outgoing links, and weak anchors.",
            "- `quick-wins.md`: low-effort issue table.",
            "- `post-audit.csv` and `post-audit.json`: structured row-level audit data.",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def audit_run_rows(result: AuditResult, run_context: dict[str, object] | None = None, detailed_outputs: bool = False) -> list[list[str]]:
    context = run_context or {}

    def value(key: str, default: object = "") -> str:
        item = context.get(key, default)
        if isinstance(item, bool):
            return "true" if item else "false"
        if isinstance(item, (list, tuple, set)):
            return ", ".join(str(part) for part in item) if item else "All"
        if item is None or item == "":
            return str(default) if default not in (None, "") else ""
        return str(item)

    return [
        ["Blog", result.config.blog_name],
        ["Product", value("product_name", "All products")],
        ["Audit date", value("audit_date", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))],
        ["Repository", str(result.repo_root)],
        ["Blog config", value("blog_config", "")],
        ["Mode", value("mode", "report")],
        ["Product filter", value("product_filter", "All")],
        ["Post date filter", value("post_date_filter", "All")],
        ["Language filter", value("language_filter", "All")],
        ["Include translations", value("include_translations", "Unknown")],
        ["Detailed outputs", value("detailed_outputs", detailed_outputs)],
        ["LLM suggestions", value("llm_suggestions", bool(result.llm_metrics.get("enabled")))],
        ["LLM model", value("llm_model", "")],
        ["Draft fixes", value("draft_fixes", False)],
        ["Max draft fixes", value("max_draft_fixes", "All")],
        ["Priority only", value("priority_only", False)],
        ["Send metrics", value("send_metrics", False)],
        ["Output directory", value("output_dir", "")],
        ["Workdir", value("workdir", "")],
        ["Keep workdir", value("keep_workdir", False)],
    ]


def llm_suggestion_rows(result: AuditResult) -> list[list[str]]:
    rows: list[list[str]] = []
    for post in result.posts:
        for suggestion in post.llm_suggestions:
            rows.append([
                f"`{suggestion.file_path}`",
                suggestion.model,
                "Yes" if suggestion.cached else "No",
                suggestion.summary,
                suggestion.suggested_title,
                suggestion.suggested_description,
                "; ".join(suggestion.content_actions),
                "; ".join(suggestion.faq_questions),
                "; ".join(suggestion.risk_notes),
            ])
    return rows


def grouped_action_item_sections(items: list[dict[str, str]], result: AuditResult) -> list[str]:
    post_by_file = {post.relative_path: post for post in result.posts}
    post_groups: dict[str, list[dict[str, str]]] = {}
    sitewide_groups: dict[str, list[dict[str, str]]] = {}
    for item in items:
        file_path = item["file"]
        target = post_groups if file_path in post_by_file else sitewide_groups
        target.setdefault(file_path, []).append(item)

    lines: list[str] = []
    for file_path, group in post_groups.items():
        post = post_by_file[file_path]
        title = post.title or Path(file_path).parent.name
        lines += [
            f"### {title}",
            f"File: `{file_path}`",
            "",
            *action_item_table_without_file(group, "Post-level"),
            "",
        ]

    for file_path, group in sitewide_groups.items():
        lines += [
            "### Sitewide / Technical",
            f"Scope: `{file_path}`",
            "",
            *action_item_table_without_file(group, "Sitewide"),
            "",
        ]

    return lines or ["No action items found."]


def action_item_table_without_file(items: list[dict[str, str]], blank_line_scope: str) -> list[str]:
    return markdown_table(
        ["ID", "Priority", "Severity", "Area", "Issue", "Line / Scope", "Post Priority", "Recommended Action", "Effort", "Impact", "Source"],
        [
            [
                item["id"],
                item["priority"],
                item["severity"],
                item["area"],
                item["issue"],
                action_item_line_display(item, blank_line_scope),
                item["post_priority"],
                item["action"],
                item["effort"],
                item["impact"],
                item["source"],
            ]
            for item in items
        ],
    )


def action_item_line_display(item: dict[str, str], blank_line_scope: str) -> str:
    return item["line"] if item["line"].strip() else blank_line_scope


def audit_action_items(result: AuditResult) -> list[dict[str, str]]:
    rows: list[dict[str, str | int]] = []

    def add(issue: Issue, source: str, post: Post | None = None) -> None:
        post_priority = post.scores.get("priority", 0) if post else 0
        rows.append({
            "priority": action_priority(issue, post_priority),
            "severity": issue.severity,
            "area": issue_area(issue),
            "issue": issue.issue_type,
            "file": issue.file_path,
            "line": issue_line(issue),
            "post_priority": post_priority,
            "action": issue.recommended_fix,
            "effort": issue.estimated_effort,
            "impact": issue.expected_seo_impact,
            "source": source,
        })

    for post in result.posts:
        for item in post.issues:
            add(item, source_report_for_issue(item), post)
    for item in result.technical_issues:
        add(item, "technical-seo-audit.md")
    for item in result.internal_link_issues:
        add(item, "internal-linking-audit.md")

    rows = collapse_duplicate_action_rows(rows)
    rows.sort(key=lambda item: (
        action_priority_rank(str(item["priority"])),
        severity_rank(str(item["severity"])),
        -int(item["post_priority"]),
        str(item["area"]),
        str(item["file"]),
        str(item["issue"]),
    ))

    return [
        {
            "id": f"AA-{index:04d}",
            "priority": str(item["priority"]),
            "severity": str(item["severity"]),
            "area": str(item["area"]),
            "issue": str(item["issue"]),
            "file": str(item["file"]),
            "line": str(item["line"]),
            "post_priority": str(item["post_priority"]),
            "action": str(item["action"]),
            "effort": str(item["effort"]),
            "impact": str(item["impact"]),
            "source": str(item["source"]),
        }
        for index, item in enumerate(rows, start=1)
    ]


def collapse_duplicate_action_rows(rows: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    collapsed: list[dict[str, str | int]] = []
    too_few_by_file: dict[str, dict[str, str | int]] = {}
    for row in rows:
        if row["issue"] != "too_few_outgoing_internal_links":
            collapsed.append(row)
            continue
        file_path = str(row["file"])
        existing = too_few_by_file.get(file_path)
        if not existing:
            too_few_by_file[file_path] = row
            collapsed.append(row)
            continue
        preferred = preferred_duplicate_action_row(existing, row)
        if preferred is not existing:
            collapsed[collapsed.index(existing)] = preferred
            too_few_by_file[file_path] = preferred
    return collapsed


def preferred_duplicate_action_row(left: dict[str, str | int], right: dict[str, str | int]) -> dict[str, str | int]:
    def score(row: dict[str, str | int]) -> tuple[int, int]:
        line_score = 1 if str(row.get("line") or "").strip() else 0
        return (int(row.get("post_priority") or 0), line_score)

    return right if score(right) > score(left) else left


def issue_line(issue: Issue) -> str:
    if issue.line > 0:
        return str(issue.line)
    for text in (issue.explanation, issue.evidence):
        match = re.search(r"(?:Code block line|Code line|Markdown line|line)\s+(\d+)", text, re.I)
        if match:
            return match.group(1)
        match = re.search(r"\bline\s*[=:]\s*(\d+)", text, re.I)
        if match:
            return match.group(1)
    return ""


def action_priority(issue: Issue, post_priority: int) -> str:
    if issue.severity == "Critical":
        return "P0"
    if issue.severity == "High" or post_priority >= 80:
        return "P1"
    if issue.severity == "Medium" or post_priority >= 60:
        return "P2"
    return "P3"


def action_priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 9)


def severity_rank(severity: str) -> int:
    return {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Opportunity": 4}.get(severity, 9)


def source_report_for_issue(issue: Issue) -> str:
    area = issue_area(issue)
    if area == "Code/API":
        return "code-audit.md"
    if area == "Internal Linking":
        return "internal-linking-audit.md"
    if area == "Technical SEO":
        return "technical-seo-audit.md"
    if area == "Content Quality":
        return "content-improvement-plan.md"
    return "complete-seo-audit.md"


def issue_area(issue: Issue) -> str:
    typ = issue.issue_type
    if typ in code_issue_types():
        return "Code/API"
    if typ in {
        "weak_internal_links",
        "missing_external_links",
        "broken_internal_link",
        "weak_anchor_text",
        "too_few_outgoing_internal_links",
        "orphan_post",
    }:
        return "Internal Linking"
    if typ in {
        "missing_hugo_config",
        "missing_robots",
        "multilingual_config_unknown",
        "canonical_template",
        "hreflang_template",
        "open_graph",
        "twitter_cards",
        "schema_markup",
        "canonical_field_check",
    }:
        return "Technical SEO"
    if typ in {"missing_translation", "unlocalized_title", "unlocalized_description", "mismatched_headings"}:
        return "Multilingual SEO"
    if typ in {
        "weak_developer_audience_fit",
        "missing_code_example_for_developers",
        "missing_setup_context",
        "missing_file_format_context",
        "missing_troubleshooting_or_limitations",
        "missing_api_reference_link",
    }:
        return "Developer Audience Fit"
    if typ in {
        "missing_title",
        "short_title",
        "title_length",
        "missing_description",
        "description_length",
        "duplicate_title",
        "duplicate_description",
        "duplicate_slug",
        "multiple_h1",
        "missing_alt_text",
    }:
        return "On-Page SEO"
    if typ in {
        "thin_content",
        "moderate_thin_content",
        "weak_intro",
        "missing_headings",
        "missing_h2_sections",
        "heading_hierarchy",
        "missing_faq",
        "missing_conclusion",
        "missing_examples",
        "missing_post_image",
        "suggest_body_output_image",
        "placeholder_artifact",
        "mojibake_encoding_artifact",
        "unverified_product_mention",
        "missing_product_format_context",
        "missing_product_action_context",
        "missing_product_docs_link",
        "missing_product_page_link",
    }:
        return "Content Quality"
    if issue.policy_id:
        return issue.policy_id.replace("-", " ").title()
    return "General SEO"


def write_content_plan(result: AuditResult, path: Path, include_suggestions: bool) -> None:
    posts = sorted(result.posts, key=lambda p: p.scores.get("priority", 0), reverse=True)[:30]
    lines = ["# Content Improvement Plan", ""]
    for post in posts:
        lines += [
            f"## {post.title or post.relative_path}",
            f"- File: `{post.relative_path}`",
            f"- Priority score: {post.scores.get('priority', 0)}",
            f"- Recommended title rewrite: {_suggest_title(post) if include_suggestions else 'Enable report-with-fix-suggestions for rewrite ideas.'}",
            f"- Recommended meta description rewrite: {_suggest_description(post) if include_suggestions else 'Enable report-with-fix-suggestions for rewrite ideas.'}",
            "- Heading improvements: Add descriptive H2 sections for prerequisites, steps, troubleshooting, FAQs, and conclusion where missing.",
            "- FAQ ideas: What is the easiest way? What formats are supported? How do I troubleshoot common errors?",
            "- Schema opportunities: FAQPage and HowTo where content supports it.",
            "- Internal links: Link to related tutorials, product documentation, API reference, and pricing/download pages.",
            "- Content expansion areas: examples, screenshots, edge cases, performance notes, and localization-specific phrasing.",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_quick_wins(result: AuditResult, path: Path) -> None:
    issues = [i for p in result.posts for i in p.issues if i.estimated_effort == "Low"][:100]
    lines = ["# Quick Wins", "", *issue_table(issues)]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_draft_fixes(result: AuditResult, draft_dir: Path, max_fixes: int | None, priority_only: bool) -> None:
    draft_dir.mkdir(parents=True, exist_ok=True)
    posts = sorted(result.posts, key=lambda p: p.scores.get("priority", 0), reverse=True)
    if priority_only:
        posts = [p for p in posts if p.scores.get("priority", 0) >= 60]
    if max_fixes is not None:
        posts = posts[:max_fixes]
    index_rows = []
    for post in posts:
        target = draft_dir / post.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        original = post.path.read_text(encoding="utf-8", errors="replace")
        notes = [
            "<!--",
            "Suggested draft generated by hugo-blog-audit-agent.",
            "Review manually before publishing. Original source was not overwritten.",
            f"Top issues: {', '.join(i.issue_type for i in post.issues[:5])}",
            "-->",
            "",
        ]
        target.write_text("\n".join(notes) + original + "\n\n## Suggested FAQ\n\n- What problem does this tutorial solve?\n- Which file formats or platforms are supported?\n- Where can developers find related API documentation?\n\n## Suggested Conclusion\n\nSummarize the outcome, link to related resources, and give readers a clear next step.\n", encoding="utf-8")
        index_rows.append({"source": post.relative_path, "draft": target.relative_to(draft_dir).as_posix(), "priority": post.scores.get("priority", 0), "notes": "; ".join(i.issue_type for i in post.issues[:5])})
    with (draft_dir / "index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "draft", "priority", "notes"])
        writer.writeheader()
        writer.writerows(index_rows)


def _issue_bullets(issues: list[Issue]) -> list[str]:
    return [f"- {i.severity}: `{i.file_path}` - {i.explanation}" for i in issues] or ["- No critical or high issues detected."]


def _suggest_title(post: Post) -> str:
    base = post.title or Path(post.relative_path).parent.name.replace("-", " ").title()
    return base[:62]


def _suggest_description(post: Post) -> str:
    topic = post.title or "this tutorial"
    return f"Learn {topic.lower()} with clear steps, examples, and practical guidance for developers."


def issue_table(issues: list[Issue]) -> list[str]:
    if not issues:
        return ["No issues detected."]
    return markdown_table(
        ["Severity", "Issue", "Policy", "Rule", "Evidence", "Audience", "File", "Explanation", "Recommended Fix", "Effort", "Impact"],
        [
            [
                item.severity,
                item.issue_type,
                item.policy_id,
                item.rule_id,
                item.evidence,
                ", ".join(item.intended_audiences),
                f"`{item.file_path}`",
                item.explanation,
                item.recommended_fix,
                item.estimated_effort,
                item.expected_seo_impact,
            ]
            for item in issues
        ],
    )


def code_issue_types() -> set[str]:
    return {"unresolved_api_module", "unresolved_api_symbol", "unresolved_api_class", "unresolved_api_member", "deprecated_api_symbol"}


def code_class_resolution_rows(issues: list[Issue]) -> list[list[str]]:
    rows: list[list[str]] = []
    for issue in issues:
        if issue.issue_type not in {"unresolved_api_symbol", "unresolved_api_class", "unresolved_api_member", "deprecated_api_symbol"}:
            continue
        rows.append([
            f"`{issue.file_path}`",
            code_issue_line(issue),
            code_issue_symbol(issue),
            code_issue_status(issue),
            issue.recommended_fix,
        ])
    return rows


def code_issue_line(issue: Issue) -> str:
    return issue_line(issue)


def code_issue_symbol(issue: Issue) -> str:
    matches = re.findall(r"`([^`]+)`", issue.explanation)
    return matches[0] if matches else ""


def code_issue_status(issue: Issue) -> str:
    if issue.issue_type == "deprecated_api_symbol":
        return "Deprecated or renamed"
    if issue.issue_type == "unresolved_api_class":
        return "Missing from API reference"
    if issue.issue_type == "unresolved_api_member":
        return "Missing from API reference"
    return "Missing from indexed symbols"


def sdk_reference_rows(result: AuditResult) -> list[list[str]]:
    packages = result.config.sdk_validation.get("packages") or []
    rows = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        rows.append([
            str(package.get("id") or package.get("source") or "API reference"),
            str(package.get("product_key") or ""),
            str(package.get("source") or ""),
            ", ".join(str(namespace) for namespace in package.get("namespaces") or []),
            str(len(package.get("known_symbols") or [])),
        ])
    return rows


def seo_scorecard_rows(result: AuditResult) -> list[list[str]]:
    posts = result.posts
    if not posts:
        return [["Overall SEO Health", "0", "No posts were scanned."]]

    def avg_score(key: str) -> int:
        return round(sum(post.scores.get(key, 0) for post in posts) / len(posts))

    def issue_count(issue_types: set[str]) -> int:
        return sum(1 for post in posts for item in post.issues if item.issue_type in issue_types)

    content_issue_types = {
        "thin_content",
        "moderate_thin_content",
        "weak_intro",
        "missing_headings",
        "missing_h2_sections",
        "missing_faq",
        "missing_conclusion",
        "missing_examples",
        "missing_post_image",
        "suggest_body_output_image",
        "placeholder_artifact",
        "mojibake_encoding_artifact",
        "unverified_product_mention",
        "unresolved_api_module",
        "unresolved_api_symbol",
        "unresolved_api_class",
        "unresolved_api_member",
        "deprecated_api_symbol",
        "missing_product_format_context",
        "missing_product_action_context",
        "missing_product_docs_link",
        "missing_product_page_link",
    }
    on_page_issue_types = {
        "missing_title",
        "short_title",
        "title_length",
        "missing_description",
        "description_length",
        "duplicate_title",
        "duplicate_description",
        "duplicate_slug",
        "multiple_h1",
        "missing_alt_text",
    }
    translation_issue_types = {
        "missing_translation",
        "unlocalized_title",
        "unlocalized_description",
        "mismatched_headings",
    }
    content = max(0, avg_score("content_quality") - min(65, round((issue_count(content_issue_types) / len(posts)) * 8)))
    on_page = max(0, avg_score("on_page_seo") - min(45, round((issue_count(on_page_issue_types) / len(posts)) * 7)))
    technical = max(0, 100 - len(result.technical_issues) * 8)
    internal = max(0, avg_score("internal_linking") - min(75, round((len(result.internal_link_issues) / len(posts)) * 18)))
    missing_group_penalty = round((sum(1 for group in result.groups if group.missing_languages) / max(len(result.groups), 1)) * 35)
    translation = max(0, avg_score("translation_seo") - missing_group_penalty - min(45, round((issue_count(translation_issue_types) / len(posts)) * 8)))
    audience_issue_types = {
        "weak_developer_audience_fit",
        "missing_code_example_for_developers",
        "missing_setup_context",
        "missing_file_format_context",
        "missing_troubleshooting_or_limitations",
        "missing_api_reference_link",
    }
    audience_issues = sum(1 for post in posts for item in post.issues if item.issue_type in audience_issue_types)
    audience = max(0, 100 - min(80, round((audience_issues / len(posts)) * 25))) if result.config.developer_audience else 100
    overall = round((content * 0.24) + (on_page * 0.18) + (technical * 0.14) + (internal * 0.16) + (translation * 0.13) + (audience * 0.15))
    return [
        ["Overall SEO Health", str(overall), score_label(overall)],
        ["Content Quality", str(content), score_label(content)],
        ["On-Page SEO", str(on_page), score_label(on_page)],
        ["Technical SEO", str(technical), score_label(technical)],
        ["Internal Linking", str(internal), score_label(internal)],
        ["Translation SEO", str(translation), score_label(translation)],
        ["Developer Audience Fit", str(audience), score_label(audience) if result.config.developer_audience else "Not enabled for this config."],
    ]


def post_score_rows(posts: list[Post]) -> list[list[str]]:
    rows: list[list[str]] = []
    for post in sorted(posts, key=lambda p: p.scores.get("priority", 0), reverse=True):
        rows.append([
            f"`{post.relative_path}`",
            post.title,
            post.language,
            str(post.scores.get("content_quality", 0)),
            str(post.scores.get("on_page_seo", 0)),
            str(post.scores.get("technical_seo", 0)),
            str(post.scores.get("internal_linking", 0)),
            str(post.scores.get("translation_seo", 0)),
            str(developer_audience_post_score(post)),
            str(post.scores.get("organic_growth_opportunity", 0)),
            str(post.scores.get("priority", 0)),
            str(len(post.issues)),
            "; ".join(item.issue_type for item in post.issues[:5]),
        ])
    return rows


def audit_segment_summary_rows(result: AuditResult) -> list[list[str]]:
    posts = result.posts
    primary_posts = [post for post in posts if post.language == "en"] or posts
    post_issues = [item for post in posts for item in post.issues]
    content_types = {
        "thin_content",
        "moderate_thin_content",
        "weak_intro",
        "missing_headings",
        "missing_h2_sections",
        "missing_faq",
        "missing_conclusion",
        "missing_examples",
        "missing_post_image",
        "suggest_body_output_image",
        "placeholder_artifact",
        "mojibake_encoding_artifact",
        "unverified_product_mention",
        "unresolved_api_module",
        "unresolved_api_symbol",
        "unresolved_api_class",
        "unresolved_api_member",
        "deprecated_api_symbol",
        "missing_product_format_context",
        "missing_product_action_context",
        "missing_product_docs_link",
        "missing_product_page_link",
    }
    on_page_types = {
        "missing_title",
        "short_title",
        "title_length",
        "missing_description",
        "description_length",
        "duplicate_title",
        "duplicate_description",
        "duplicate_slug",
        "multiple_h1",
        "missing_alt_text",
        "canonical_field_check",
        "missing_external_links",
    }
    audience_types = {
        "weak_developer_audience_fit",
        "missing_code_example_for_developers",
        "missing_setup_context",
        "missing_file_format_context",
        "missing_troubleshooting_or_limitations",
        "missing_api_reference_link",
    }
    translation_types = {
        "missing_translation",
        "unlocalized_title",
        "unlocalized_description",
        "mismatched_headings",
    }

    def count_types(types: set[str]) -> int:
        return sum(1 for item in post_issues if item.issue_type in types)

    def status(issue_count: int) -> str:
        if issue_count == 0:
            return "Clear"
        if issue_count <= max(5, len(posts) // 10):
            return "Monitor"
        if issue_count <= max(10, len(posts)):
            return "Needs cleanup"
        return "Priority risk"

    content_issue_count = count_types(content_types)
    on_page_issue_count = count_types(on_page_types)
    audience_issue_count = count_types(audience_types)
    translation_issue_count = count_types(translation_types)
    technical_issue_count = len(result.technical_issues)
    internal_issue_count = len(result.internal_link_issues)
    code_issue_count = sum(1 for item in post_issues if item.issue_type in code_issue_types())
    quick_win_count = sum(1 for item in post_issues if item.estimated_effort == "Low")
    return [
        ["Complete SEO", "All audit areas", f"{len(posts)} posts, {sum(len(post.issues) for post in posts) + technical_issue_count + internal_issue_count} total issues", str(sum(len(post.issues) for post in posts) + technical_issue_count + internal_issue_count), status(sum(len(post.issues) for post in posts) + technical_issue_count + internal_issue_count), "complete-seo-audit.md"],
        ["Content Quality", "Markdown body and structure", f"{sum(1 for post in primary_posts if post.word_count < 800)} posts under 800 words", str(content_issue_count), status(content_issue_count), "content-improvement-plan.md"],
        ["Developer Audience Fit", "API/developer usefulness", f"{count_issue(primary_posts, 'missing_code_example_for_developers')} missing code examples", str(audience_issue_count), status(audience_issue_count), "complete-seo-audit.md"],
        ["Code/API Audit", "Code blocks and SDK/API symbols", f"{sum(len(post.code_samples) for post in posts)} code blocks", str(code_issue_count), status(code_issue_count), "code-audit.md"],
        ["On-Page SEO", "Titles, descriptions, headings, links, images", f"{count_issue(primary_posts, 'description_length')} description length issues", str(on_page_issue_count), status(on_page_issue_count), "post-audit.csv"],
        ["Technical Hugo SEO", "Config, templates, robots, canonical, hreflang, schema", f"{technical_issue_count} technical findings", str(technical_issue_count), status(technical_issue_count), "technical-seo-audit.md"],
        ["Internal Linking", "Outgoing links, incoming links, broken local links, anchors", f"{internal_issue_count} linking findings", str(internal_issue_count), status(internal_issue_count), "internal-linking-audit.md"],
        ["Multilingual SEO", "Translation groups and localized metadata", f"{sum(1 for group in result.groups if group.missing_languages)} groups missing languages", str(translation_issue_count), status(translation_issue_count), "complete-seo-audit.md"],
        ["Quick Wins", "Low-effort fixes", f"{quick_win_count} low-effort findings", str(quick_win_count), status(quick_win_count), "quick-wins.md"],
        ["Content Inventory", "Years and product-family distribution", f"{len(year_rows(primary_posts))} years, {len(product_rows(primary_posts))} product groups", "0", "Informational", "audit-summary.md"],
    ]


def developer_audience_post_score(post: Post) -> int:
    issue_types = {
        "weak_developer_audience_fit",
        "missing_code_example_for_developers",
        "missing_setup_context",
        "missing_file_format_context",
        "missing_troubleshooting_or_limitations",
        "missing_api_reference_link",
    }
    penalty = sum(18 if item.severity == "High" else 10 if item.severity == "Medium" else 4 for item in post.issues if item.issue_type in issue_types)
    return max(0, 100 - penalty)


def score_label(score: int) -> str:
    if score >= 85:
        return "Strong. Monitor and refine."
    if score >= 70:
        return "Good but has visible improvement opportunities."
    if score >= 50:
        return "Needs focused cleanup and refresh work."
    return "High risk. Prioritize remediation."


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    escaped_headers = [_cell(h) for h in headers]
    lines = [
        "| " + " | ".join(escaped_headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    if not rows:
        lines.append("| " + " | ".join("None" if idx == 0 else "" for idx, _ in enumerate(headers)) + " |")
        return lines
    for row in rows:
        padded = [*row, *[""] * (len(headers) - len(row))]
        lines.append("| " + " | ".join(_cell(value) for value in padded[: len(headers)]) + " |")
    return lines


def _cell(value: object) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ")
    text = text.replace("|", "\\|")
    return text[:260] + "..." if len(text) > 263 else text


def content_signal_rows(posts: list[Post]) -> list[list[str]]:
    total = max(len(posts), 1)
    signals = [
        ("Under 500 words", sum(1 for p in posts if p.word_count < 500)),
        ("Under 800 words", sum(1 for p in posts if p.word_count < 800)),
        ("No code block", sum(1 for p in posts if p.code_blocks == 0)),
        ("No post image", sum(1 for p in posts if not p.images)),
        ("No H2 heading", sum(1 for p in posts if not any(h.level == 2 for h in p.headings))),
        ("Placeholder/template terms", sum(1 for p in posts if any(i.issue_type == "placeholder_artifact" for i in p.issues))),
        ("Possible mojibake", sum(1 for p in posts if any(i.issue_type == "mojibake_encoding_artifact" for i in p.issues))),
        ("Draft true", sum(1 for p in posts if p.draft)),
    ]
    return [[name, str(count), f"{count / total:.1%}"] for name, count in signals]


def developer_audience_rows(posts: list[Post]) -> list[list[str]]:
    total = max(len(posts), 1)
    signals = [
        ("Weak developer audience fit", count_issue(posts, "weak_developer_audience_fit")),
        ("Missing code example", count_issue(posts, "missing_code_example_for_developers")),
        ("Missing setup/dependency context", count_issue(posts, "missing_setup_context")),
        ("Missing file-format context", count_issue(posts, "missing_file_format_context")),
        ("Missing troubleshooting/limitations", count_issue(posts, "missing_troubleshooting_or_limitations")),
        ("Missing API/reference link", count_issue(posts, "missing_api_reference_link")),
    ]
    return [[name, str(count), f"{count / total:.1%}"] for name, count in signals]


def count_issue(posts: list[Post], issue_type: str) -> int:
    return sum(1 for post in posts if any(issue.issue_type == issue_type for issue in post.issues))


def metadata_signal_rows(posts: list[Post]) -> list[list[str]]:
    titles = Counter(p.title.strip().lower() for p in posts if p.title)
    descs = Counter(p.description.strip().lower() for p in posts if p.description)
    duplicate_title_values = sum(1 for count in titles.values() if count > 1)
    duplicate_desc_values = sum(1 for count in descs.values() if count > 1)
    return [
        ["Missing title", str(sum(1 for p in posts if not p.title))],
        ["Titles under 30 chars", str(sum(1 for p in posts if p.title and len(p.title) < 30))],
        ["Titles over 60 chars", str(sum(1 for p in posts if len(p.title) > 60))],
        ["Missing description", str(sum(1 for p in posts if not p.description))],
        ["Descriptions under 120 chars", str(sum(1 for p in posts if p.description and len(p.description) < 120))],
        ["Descriptions over 170 chars", str(sum(1 for p in posts if len(p.description) > 170))],
        ["Duplicate title values", str(duplicate_title_values)],
        ["Files affected by duplicate titles", str(sum(titles[p.title.strip().lower()] > 1 for p in posts if p.title))],
        ["Duplicate description values", str(duplicate_desc_values)],
        ["Files affected by duplicate descriptions", str(sum(descs[p.description.strip().lower()] > 1 for p in posts if p.description))],
    ]


def year_rows(posts: list[Post]) -> list[list[str]]:
    counts: Counter[str] = Counter()
    for post in posts:
        year = extract_year(post)
        if year:
            counts[year] += 1
    return [[year, str(count)] for year, count in sorted(counts.items())]


def product_rows(posts: list[Post]) -> list[list[str]]:
    counts: Counter[str] = Counter()
    for post in posts:
        product = product_from_path(post.relative_path)
        if product:
            counts[product] += 1
    return [[product, str(count)] for product, count in counts.most_common(20)]


def extract_year(post: Post) -> str:
    match = re.search(r"\b(20\d{2}|19\d{2})\b", post.date or post.relative_path)
    return match.group(1) if match else ""


def product_from_path(relative_path: str) -> str:
    parts = Path(relative_path).parts
    lowered = [p.lower() for p in parts]
    if "aspose.blog" in lowered:
        idx = lowered.index("aspose.blog")
        if idx + 1 < len(parts):
            return parts[idx + 1].lower()
    if "content" in lowered:
        idx = lowered.index("content")
        if idx + 1 < len(parts):
            return parts[idx + 1].lower()
    return ""
