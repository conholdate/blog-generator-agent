from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .auditor import run_audit
from .config import load_blog_config
from .metrics_api import AGENT_NAME, AGENT_OWNER, ITEM_NAME, JOB_TYPE, PLATFORM, WEBSITE_SECTION, send_metrics_api
from .reports import write_reports


MODES = {"report", "report-with-fix-suggestions", "report-with-draft-fixes"}


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "y", "on"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Hugo blog SEO/content/multilingual audit agent.")
    parser.add_argument("--blog-config", required=True, help="Path to blog YAML/JSON config.")
    parser.add_argument("--product", help="Optional product/path filter, for example Aspose.3d.")
    parser.add_argument("--post-date", "--date", dest="post_date", help="Optional YYYY-MM-DD post date filter. Combines with --product to audit dated posts under a selected product.")
    parser.add_argument("--mode", choices=sorted(MODES), default="report")
    parser.add_argument("--generate-draft-fixes", type=parse_bool, nargs="?", const=True, default=False)
    parser.add_argument("--max-draft-fixes", type=int)
    parser.add_argument("--priority-only", type=parse_bool, nargs="?", const=True, default=False)
    parser.add_argument("--languages", help="Comma-separated language list to scan.")
    parser.add_argument("--include-translations", type=parse_bool, nargs="?", const=True, default=True, help="Include translated Markdown files. Use false to scan source index.md files only.")
    parser.add_argument("--detailed-outputs", type=parse_bool, nargs="?", const=True, default=False, help="Generate the full detailed report set in addition to audit-action-items.md.")
    parser.add_argument("--llm-suggestions", type=parse_bool, nargs="?", const=True, default=None, help="Enable optional LLM-generated review suggestions. Sends selected post excerpts and findings to the configured LLM provider.")
    parser.add_argument("--llm-model", help="Override the configured LLM model for suggestion generation.")
    parser.add_argument("--llm-base-url", help="Override the configured OpenAI-compatible /v1 base URL or full chat completions URL.")
    parser.add_argument("--llm-max-posts", type=int, help="Limit how many highest-priority posts receive LLM suggestions.")
    parser.add_argument("--llm-timeout-seconds", type=float, help="LLM HTTP read timeout in seconds.")
    parser.add_argument("--llm-retries", type=int, help="Retry count for timeout or connection-style LLM failures.")
    parser.add_argument("--send-metrics", type=parse_bool, nargs="?", const=True, default=False, help="Send normalized run metrics to the configured metrics API. Defaults to false.")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress logs and final metrics in the console.")
    parser.add_argument("--keep-workdir", action="store_true", default=False)
    parser.add_argument("--workdir", default="outputs/_repos")
    parser.add_argument("--output-dir", help="Override output directory.")
    return parser


def blog_audit_dir(config_output_dir: str, blog_name: str) -> Path:
    output_path = Path(config_output_dir)
    if output_path.as_posix().rstrip("/").lower() in {"outputs", "output"}:
        slug = re.sub(r"[^a-z0-9]+", "-", blog_name.strip().lower()).strip("-") or "blog"
        return output_path / "audit" / slug
    return output_path


class RunLogger:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.lines: list[str] = []

    def log(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        self.lines.append(line)
        if self.enabled:
            print(line)


def main(argv: list[str] | None = None) -> None:
    started = time.perf_counter()
    run_id = str(uuid.uuid4())
    args = build_parser().parse_args(argv)
    logger = RunLogger(enabled=not args.quiet)
    logger.log("Loading blog configuration")
    config = load_blog_config(args.blog_config)
    apply_llm_cli_overrides(config, args)
    if args.post_date and not re.fullmatch(r"(?:19|20)\d{2}-\d{2}-\d{2}", args.post_date):
        raise SystemExit("--post-date must use YYYY-MM-DD format, for example 2026-06-05.")
    languages = [x.strip().lower() for x in args.languages.split(",") if x.strip()] if args.languages else None
    include_suggestions = args.mode in {"report-with-fix-suggestions", "report-with-draft-fixes"}
    draft_fixes = args.mode == "report-with-draft-fixes" or args.generate_draft_fixes
    output_dir = Path(args.output_dir) if args.output_dir else blog_audit_dir(config.output_dir, config.blog_name)
    logger.log(f"Audit output will be written to: {output_dir.resolve()}")
    result = run_audit(config, args.product, args.mode, languages, args.include_translations, args.keep_workdir, Path(args.workdir), post_date=args.post_date, log=logger.log)
    logger.log("Writing report files")
    run_context = build_report_run_context(args, config, output_dir, languages, draft_fixes)
    write_reports(result, output_dir, include_suggestions, draft_fixes, args.max_draft_fixes, args.priority_only, args.detailed_outputs, run_context)
    metrics = build_run_metrics(result, output_dir, args.mode, args.product, args.post_date, languages, args.include_translations, started, args.detailed_outputs, run_id)
    metrics["send_metrics"] = bool(args.send_metrics)
    metrics["metrics_api"] = deliver_metrics(metrics, args.send_metrics, logger.log)
    write_run_artifacts(output_dir, logger.lines, metrics)
    if args.verbose:
        print(f"Repository: {result.repo_root}")
        print(f"Posts scanned: {len(result.posts)}")
        print(f"Translation groups: {len(result.groups)}")
    if not args.quiet:
        print_metrics(metrics)
    print(f"Audit reports written to {output_dir.resolve()}")


def deliver_metrics(metrics: dict[str, Any], send_metrics: bool, log: Any | None = None) -> list[dict[str, Any]]:
    if not send_metrics:
        if log:
            log("Metrics API sending skipped; pass --send-metrics true to enable.")
        return [{"target": "all", "sent": False, "status": "skipped", "reason": "disabled_by_flag"}]
    if log:
        log("Sending metrics API payload")
    return send_metrics_api(metrics, log)


def build_report_run_context(args, config, output_dir: Path, languages: list[str] | None, draft_fixes: bool) -> dict[str, object]:
    product_name = product_display_name(config, args.product) if args.product else "All products"
    return {
        "audit_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "blog_config": args.blog_config,
        "mode": args.mode,
        "product_name": product_name,
        "product_filter": args.product or "All",
        "post_date_filter": args.post_date or "All",
        "language_filter": languages or [],
        "include_translations": args.include_translations,
        "detailed_outputs": args.detailed_outputs,
        "llm_suggestions": bool(config.llm.get("enabled")),
        "llm_model": config.llm.get("model") or args.llm_model or "",
        "draft_fixes": draft_fixes,
        "max_draft_fixes": args.max_draft_fixes if args.max_draft_fixes is not None else "All",
        "priority_only": args.priority_only,
        "send_metrics": args.send_metrics,
        "output_dir": str(output_dir.resolve()),
        "workdir": args.workdir,
        "keep_workdir": args.keep_workdir,
    }


def apply_llm_cli_overrides(config, args) -> None:
    if args.llm_suggestions is not None:
        config.llm["enabled"] = args.llm_suggestions
    if args.llm_model:
        config.llm["model"] = args.llm_model
    if args.llm_base_url:
        config.llm["base_url"] = args.llm_base_url
    if args.llm_max_posts is not None:
        config.llm["max_posts"] = args.llm_max_posts
    if args.llm_timeout_seconds is not None:
        config.llm["timeout_seconds"] = args.llm_timeout_seconds
    if args.llm_retries is not None:
        config.llm["retries"] = args.llm_retries


def build_run_metrics(
    result,
    output_dir: Path,
    mode: str,
    product: str | None,
    post_date: str | None,
    languages: list[str] | None,
    include_translations: bool,
    started: float,
    detailed_outputs: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    post_issues = [issue for post in result.posts for issue in post.issues]
    all_issues = post_issues + result.technical_issues + result.internal_link_issues
    severity_counts = Counter(issue.severity for issue in all_issues)
    issue_type_counts = Counter(issue.issue_type for issue in all_issues)
    audience_issue_types = {
        "weak_developer_audience_fit",
        "missing_code_example_for_developers",
        "missing_setup_context",
        "missing_file_format_context",
        "missing_troubleshooting_or_limitations",
        "missing_api_reference_link",
    }
    code_issue_types = {"unresolved_api_module", "unresolved_api_symbol", "unresolved_api_class", "unresolved_api_member", "deprecated_api_symbol"}
    detected_languages = sorted({post.language for post in result.posts})
    priority_scores = [post.scores.get("priority", 0) for post in result.posts]
    report_files = sorted(p.name for p in output_dir.glob("*") if p.is_file())
    llm_metrics = dict(getattr(result, "llm_metrics", {}) or {})
    duration_seconds = round(time.perf_counter() - started, 2)
    items_discovered = len(result.posts)
    items_failed = 0
    product_name = product_display_name(result.config, product)
    token_usage = int(llm_metrics.get("total_tokens") or 0)
    api_calls_count = int(llm_metrics.get("api_calls") or 0)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": AGENT_NAME,
        "agent_owner": AGENT_OWNER,
        "job_type": JOB_TYPE,
        "run_id": run_id or str(uuid.uuid4()),
        "status": "success",
        "blog_name": result.config.blog_name,
        "mode": mode,
        "product_filter": product or "",
        "product": product_name,
        "product_name": product_name,
        "platform": PLATFORM,
        "website": result.config.website,
        "website_section": WEBSITE_SECTION,
        "item_name": ITEM_NAME,
        "post_date_filter": post_date or "",
        "language_filter": languages or [],
        "include_translations": include_translations,
        "detailed_outputs": detailed_outputs,
        "llm": llm_metrics,
        "repository": str(result.repo_root),
        "output_dir": str(output_dir.resolve()),
        "duration_seconds": duration_seconds,
        "run_duration_ms": int(round(duration_seconds * 1000)),
        "markdown_files_scanned": len(result.posts),
        "items_discovered": items_discovered,
        "items_failed": items_failed,
        "items_succeeded": max(items_discovered - items_failed, 0),
        "token_usage": token_usage,
        "api_calls_count": api_calls_count,
        "languages_detected": len(detected_languages),
        "language_codes": detected_languages,
        "translation_groups": len(result.groups),
        "translation_groups_with_missing_languages": sum(1 for group in result.groups if group.missing_languages),
        "post_issues": len(post_issues),
        "technical_issues": len(result.technical_issues),
        "internal_linking_issues": len(result.internal_link_issues),
        "total_issues": len(all_issues),
        "audience_profile": result.config.audience_profile,
        "developer_audience_enabled": result.config.developer_audience,
        "audience_fit_issues": sum(1 for issue in all_issues if issue.issue_type in audience_issue_types),
        "code_api_issues": sum(1 for issue in all_issues if issue.issue_type in code_issue_types),
        "code_blocks": sum(len(post.code_samples) for post in result.posts),
        "severity_counts": {key: severity_counts.get(key, 0) for key in ["Critical", "High", "Medium", "Low", "Opportunity"]},
        "top_issue_types": dict(issue_type_counts.most_common(10)),
        "average_priority_score": round(sum(priority_scores) / len(priority_scores), 2) if priority_scores else 0,
        "high_priority_posts": sum(1 for score in priority_scores if score >= 70),
        "reports_written": report_files,
    }


def product_display_name(config, product: str | None) -> str:
    if product:
        normalized = product.replace("\\", "/").strip("/").lower()
        parts = [part for part in normalized.split("/") if part]
        candidates = [parts[-1]] if parts else []
        candidates.extend(part.replace("aspose.blog", "").strip(".-/") for part in parts)
        for candidate in candidates:
            if candidate in config.product_configs:
                return str(config.product_configs[candidate].get("display_name") or candidate)
        for key in sorted(config.product_configs, key=len, reverse=True):
            if re.search(rf"(^|[/\-.]){re.escape(key)}($|[/\-.])", normalized):
                return str(config.product_configs[key].get("display_name") or key)
    return str(config.blog_name)


def write_run_artifacts(output_dir: Path, log_lines: list[str], metrics: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audit-run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (output_dir / "audit-metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")


def print_metrics(metrics: dict[str, Any]) -> None:
    print("")
    print("Audit Metrics")
    print("-------------")
    print(f"Duration: {metrics['duration_seconds']}s")
    print(f"Markdown files scanned: {metrics['markdown_files_scanned']}")
    print(f"Include translations: {metrics['include_translations']}")
    print(f"Languages detected: {metrics['languages_detected']} ({', '.join(metrics['language_codes'])})")
    print(f"Translation groups: {metrics['translation_groups']}")
    print(f"Groups missing translations: {metrics['translation_groups_with_missing_languages']}")
    print(f"Total issues: {metrics['total_issues']}")
    print(f"Audience-fit issues: {metrics['audience_fit_issues']}")
    print(f"Code/API issues: {metrics['code_api_issues']}")
    print(f"Code blocks: {metrics['code_blocks']}")
    print(f"Post issues: {metrics['post_issues']}")
    print(f"Technical issues: {metrics['technical_issues']}")
    print(f"Internal linking issues: {metrics['internal_linking_issues']}")
    print(f"Average priority score: {metrics['average_priority_score']}")
    print(f"High-priority posts: {metrics['high_priority_posts']}")
    llm_metrics = metrics.get("llm") or {}
    if llm_metrics.get("enabled"):
        print(
            "LLM suggestions: "
            f"generated={llm_metrics.get('generated_suggestions', 0)}, "
            f"api_calls={llm_metrics.get('api_calls', 0)}, "
            f"cache_hits={llm_metrics.get('cache_hits', 0)}, "
            f"errors={llm_metrics.get('errors', 0)}"
        )
    print("Severity counts: " + ", ".join(f"{key}={value}" for key, value in metrics["severity_counts"].items()))


if __name__ == "__main__":
    main()
