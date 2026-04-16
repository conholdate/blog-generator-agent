from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_engine.content_gap_agent.settings import CoverageSettings
from agent_engine.content_gap_agent.tools.sheets_export import (
    build_payload,
    post_payload,
    resolve_sheet_config,
    write_payload,
)


def main() -> None:
    settings = CoverageSettings.from_env()

    parser = argparse.ArgumentParser(
        description="Export missing topics from a coverage.json file to a Google Sheets payload JSON, with optional POST to Apps Script. This script requires a coverage.json path; the cg-cover auto-post flow does not."
    )
    parser.add_argument("--brand", default="aspose", help="Brand key used to resolve TOPICS_SHEETS config.")
    parser.add_argument("--coverage-json", help="Explicit path to the coverage.json file to export.")
    parser.add_argument("--sheet-name", help="Target tab name inside the spreadsheet.")
    parser.add_argument("--output-json", help="Path to write the generated payload JSON.")
    parser.add_argument("--append", action="store_true", help="Append rows in Sheets instead of replacing the entire sheet.")
    parser.add_argument("--post-url", help="Override the configured Apps Script web app URL.")
    parser.add_argument("--token", help="Override the configured Apps Script token.")
    args = parser.parse_args()

    brand_key = str(args.brand or "").strip().lower()
    brand_cfg = resolve_sheet_config(settings, brand_key)

    coverage_json_arg = str(args.coverage_json or brand_cfg.get("coverage_json") or "").strip()
    if not coverage_json_arg:
        raise SystemExit(
            "Missing coverage file path for standalone export. Set --coverage-json or provide coverage_json in TOPICS_SHEETS. "
            "This is not required when using the automatic cg-cover posting flow."
        )

    post_url = str(args.post_url or brand_cfg.get("webhook_url") or "").strip()
    token = str(args.token or brand_cfg.get("token") or "").strip()
    sheet_name = str(args.sheet_name or brand_cfg.get("sheet_name") or "All Missing Topics").strip()
    output_json_arg = str(
        args.output_json
        or brand_cfg.get("output_json")
        or (settings.outputs_root / "google_sheets" / f"{brand_key}_missing_topics.json")
    ).strip()

    coverage_json = Path(coverage_json_arg).expanduser().resolve()
    if not coverage_json.exists():
        raise SystemExit(f"coverage.json not found: {coverage_json}")

    output_json = Path(output_json_arg).expanduser()
    if not output_json.is_absolute():
        output_json = (settings.repo_root / output_json).resolve()

    payload = build_payload(
        coverage_json=coverage_json,
        sheet_name=sheet_name or "All Missing Topics",
        replace=not args.append,
    )
    write_payload(payload, output_json)

    print(f"Wrote payload JSON: {output_json}")
    print(f"Coverage sources: {payload['meta']['source_count']}")
    print(f"Missing topic rows: {payload['meta']['row_count']}")

    if post_url:
        status, text = post_payload(payload, post_url, token)
        print(f"POST status: {status}")
        print(text[:1000])
    else:
        print("POST skipped: no Apps Script URL configured.")


if __name__ == "__main__":
    main()
