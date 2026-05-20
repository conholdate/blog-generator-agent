from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_engine.content_gap_agent.tools.sheets_export import (  # noqa: E402
    build_payload,
    is_successful_sheet_response,
    post_payload,
    should_post_payload,
    write_payload,
)


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid YAML object: {path}")
    return data


def _resolve_outputs_root(brand_yaml: Path, brand_data: dict[str, Any]) -> Path:
    raw = brand_data.get("outputs_root") or "outputs"
    out = Path(str(raw))
    if not out.is_absolute():
        out = (brand_yaml.parent / out).resolve()
    return out


def _resolve_brand_yaml_from_product(product_yaml: Path, product_data: dict[str, Any]) -> Path:
    blog_key = str(product_data.get("blog") or "").strip()
    if not blog_key:
        raise SystemExit(f"Missing 'blog' in product YAML: {product_yaml}")
    brand_yaml = (REPO_ROOT / "configs" / f"{blog_key}.yaml").resolve()
    if not brand_yaml.exists():
        raise SystemExit(f"Resolved brand YAML not found for blog={blog_key}: {brand_yaml}")
    return brand_yaml


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    print("[local-workflow] Running:")
    print("  " + " ".join(cmd))
    subprocess.run(cmd, check=True, env=env, cwd=str(REPO_ROOT))


def _bool_flag(enabled: bool, true_flag: str, false_flag: str) -> str:
    return true_flag if enabled else false_flag


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the insert_missing_topics_in_google_sheet workflow locally: "
            "indexer -> gap agent -> Google Sheets payload export."
        )
    )
    parser.add_argument(
        "--brand-yaml",
        default="",
        help="Optional brand YAML path. If omitted, it is resolved from product_yaml.blog.",
    )
    parser.add_argument("--product-yaml", required=True, help="Path to product YAML, e.g. configs/aspose/3d.yaml")
    parser.add_argument("--index-platform", required=True, help="Indexer platform, e.g. net")
    parser.add_argument(
        "--gap-platform",
        default="",
        help=(
            "Optional gap baseline platform. Leave empty for blogs_to_blogs all-platform mode. "
            "If omitted in current workflow reproduction, this differs from GitHub Actions."
        ),
    )
    parser.add_argument("--steps", default="blog", help="CSV repo keys for indexer, e.g. blog")
    parser.add_argument("--case", default="blogs_to_blogs", choices=["blogs_to_blogs", "docs_to_blogs", "docs_to_tutorials"])
    parser.add_argument("--threshold-strict", default="0.86")
    parser.add_argument("--threshold-loose", default="0.80")
    parser.add_argument("--top-k", default="5")
    parser.add_argument("--platforms", default="", help="Optional comma-separated platform limit for gap run")
    parser.add_argument("--sheet-name", default="", help="Optional sheet tab override")
    parser.add_argument("--output-json", default="", help="Optional payload JSON path override")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--delete-missing", action="store_true")
    parser.add_argument("--use-agent", action="store_true")
    parser.add_argument("--no-normalize-topics", action="store_true")
    parser.add_argument("--no-embeddings", action="store_true")
    parser.add_argument("--no-metrics", action="store_true", help="Disable metrics for indexer and gap subprocesses.")
    parser.add_argument("--append", action="store_true", help="Append rows in Sheets. This is the default.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace the target sheet contents instead of appending. Use only for intentional full refreshes.",
    )
    parser.add_argument("--post", action="store_true", help="Actually POST to Google Sheets. Default is payload-only.")
    parser.add_argument(
        "--workflow-compatible",
        action="store_true",
        help=(
            "Force gap baseline to the index platform when --gap-platform is empty, "
            "matching the current GitHub workflow behavior."
        ),
    )
    args = parser.parse_args()
    if args.append and args.replace:
        raise SystemExit("Use only one of --append or --replace.")

    product_yaml = (REPO_ROOT / args.product_yaml).resolve() if not Path(args.product_yaml).is_absolute() else Path(args.product_yaml).resolve()
    if not product_yaml.exists():
        raise SystemExit(f"Product YAML not found: {product_yaml}")

    product_data = _read_yaml(product_yaml)
    if args.brand_yaml:
        brand_yaml = (REPO_ROOT / args.brand_yaml).resolve() if not Path(args.brand_yaml).is_absolute() else Path(args.brand_yaml).resolve()
        if not brand_yaml.exists():
            raise SystemExit(f"Brand YAML not found: {brand_yaml}")
    else:
        brand_yaml = _resolve_brand_yaml_from_product(product_yaml, product_data)

    brand_data = _read_yaml(brand_yaml)
    brand_key = str(brand_data.get("key") or "").strip()
    product_key = str(product_data.get("key") or "").strip()
    if not brand_key:
        raise SystemExit(f"Missing key in brand YAML: {brand_yaml}")
    if not product_key:
        raise SystemExit(f"Missing key in product YAML: {product_yaml}")

    expected_brand_yaml = _resolve_brand_yaml_from_product(product_yaml, product_data)
    if brand_yaml != expected_brand_yaml:
        raise SystemExit(
            f"Brand/product mismatch: product YAML expects brand file {expected_brand_yaml}, got {brand_yaml}"
        )

    outputs_root = _resolve_outputs_root(brand_yaml, brand_data)
    gap_platform = (args.gap_platform or "").strip()
    if not gap_platform and args.workflow_compatible:
        gap_platform = args.index_platform.strip()
    gap_dir = gap_platform or "all"
    coverage_json = outputs_root / brand_key / product_key / "coverage" / args.case / gap_dir / "coverage.json"

    env = os.environ.copy()
    env["CG_REPO_ROOT"] = str(REPO_ROOT)
    env["CG_OUTPUTS_ROOT"] = str(outputs_root)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["CG_SKIP_SHEETS_AUTO_POST"] = "true"
    if args.no_metrics:
        env["METRICS_ENABLED"] = "false"

    index_cmd = [
        sys.executable,
        "-m",
        "agent_engine.content_indexer_agent.cli",
        "--log-level",
        args.log_level,
        "run",
        "--brand",
        str(brand_yaml),
        "--product",
        str(product_yaml),
        "--platform",
        args.index_platform,
        "--steps",
        args.steps,
        _bool_flag(args.delete_missing, "--delete-missing", ""),
        _bool_flag(args.use_agent, "--use-agent", "--no-agent"),
        _bool_flag(not args.no_normalize_topics, "--normalize-topics", "--no-normalize-topics"),
        _bool_flag(args.no_metrics, "--no-metrics", ""),
    ]
    index_cmd = [part for part in index_cmd if part]
    _run(index_cmd, env=env)

    gap_cmd = [
        sys.executable,
        "-m",
        "agent_engine.content_gap_agent.cli",
        "run",
        "--brand",
        str(brand_yaml),
        "--product",
        str(product_yaml),
        "--case",
        args.case,
        "--threshold-strict",
        str(args.threshold_strict),
        "--threshold-loose",
        str(args.threshold_loose),
        "--top-k",
        str(args.top_k),
    ]
    if gap_platform:
        gap_cmd.extend(["--platform", gap_platform])
    if args.platforms.strip():
        gap_cmd.extend(["--platforms", args.platforms.strip()])
    if args.no_embeddings:
        gap_cmd.append("--no-embeddings")
    if args.no_metrics:
        gap_cmd.append("--no-metrics")
    _run(gap_cmd, env=env)

    if not coverage_json.exists():
        raise SystemExit(f"coverage.json not found after gap run: {coverage_json}")

    payload = build_payload(
        coverage_json=coverage_json,
        sheet_name=(args.sheet_name or "All Missing Topics").strip() or "All Missing Topics",
        replace=args.replace,
    )

    output_json = Path(args.output_json).expanduser() if args.output_json else outputs_root / "google_sheets" / f"{brand_key}_missing_topics.json"
    if not output_json.is_absolute():
        output_json = (REPO_ROOT / output_json).resolve()
    write_payload(payload, output_json)

    print(f"[local-workflow] Wrote payload JSON: {output_json}")
    print(f"[local-workflow] Brand YAML: {brand_yaml}")
    print(f"[local-workflow] Product YAML: {product_yaml}")
    print(f"[local-workflow] Coverage JSON: {coverage_json}")
    print(f"[local-workflow] Coverage sources: {payload['meta']['source_count']}")
    print(f"[local-workflow] Missing topic rows: {payload['meta']['row_count']}")
    print(f"[local-workflow] Mode: {'replace' if args.replace else 'append'}")

    if args.post:
        from agent_engine.content_gap_agent.settings import CoverageSettings  # noqa: E402
        from agent_engine.content_gap_agent.tools.sheets_export import resolve_sheet_config  # noqa: E402

        settings = CoverageSettings.from_env()
        cfg = resolve_sheet_config(settings, brand_key)
        post_url = str(cfg.get("webhook_url") or "").strip()
        token = str(cfg.get("token") or "").strip()
        if not post_url:
            raise SystemExit(f"No webhook_url configured for brand={brand_key}")
        should_post, reason = should_post_payload(payload)
        if not should_post:
            print(f"[local-workflow] {reason}")
        else:
            status, text = post_payload(payload, post_url, token)
            print(f"[local-workflow] POST status: {status}")
            print(text[:1000])
            ok, reason = is_successful_sheet_response(status, text)
            if not ok:
                raise SystemExit(reason)
    else:
        print("[local-workflow] POST skipped. Use --post to send to Google Sheets.")

    summary = {
        "brand_key": brand_key,
        "product_key": product_key,
        "index_platform": args.index_platform,
        "gap_platform": gap_platform or None,
        "coverage_json": str(coverage_json),
        "payload_json": str(output_json),
        "row_count": payload["meta"]["row_count"],
    }
    print("[local-workflow] Summary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
