"""
Entry point for the scheduled GitHub Actions job. Calls the reconciler
directly (no MCP transport needed for a batch run — the MCP server in
this same package is for the blog agent's own on-demand use) and writes
a human-readable report the workflow turns into the PR body.

Brand comes from the RECONCILE_BRAND env var so one generic workflow
(matrix over brands for schedule, a dropdown for manual runs) can drive
this same script for whichever brand is configured — see
reconciler/config.py for what's actually supported today.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv

load_dotenv()

from reconciler.run import reconcile  # noqa: E402


def _cell(value) -> str:
    """Markdown-table-safe rendering of one cell: escape pipes (they'd
    otherwise split the row) and turn real newlines into <br> so a
    multi-line value (e.g. Java's <repository>/<dependency> XML install
    block) stays inside its row instead of breaking the table."""
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def _table(headers: list, rows: list) -> str:
    if not rows:
        return "_(none)_\n"
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(_cell(c) for c in row) + " |")
    return "\n".join(out) + "\n"


def format_report(report: dict) -> str:
    brand = report.get("brand", "unknown")
    mode = report.get("mode", "unknown")
    new_products = report["new_products"]
    new_platforms = report["new_platforms"]
    fixed_fields = report["fixed_fields"]
    potential_removals = report["potential_removals"]
    unresolved = report["unresolved"]

    lines = [f"### Reconciliation Report — {brand} ({mode})", ""]

    lines.append(_table(
        ["New products", "New platforms", "Fixed fields", "Potential removals", "Unresolved"],
        [[len(new_products), len(new_platforms), len(fixed_fields), len(potential_removals), len(unresolved)]],
    ))

    lines.append(f"#### New products ({len(new_products)})")
    lines.append(_table(
        ["Product", "Platform", "Missing fields"],
        [[i["product"], i["platform"], ", ".join(i["missing_fields"]) or "—"] for i in new_products],
    ))

    lines.append(f"#### New platforms ({len(new_platforms)})")
    lines.append(_table(
        ["Product", "Platform", "Missing fields"],
        [[i["product"], i["platform"], ", ".join(i["missing_fields"]) or "—"] for i in new_platforms],
    ))

    lines.append(f"#### Fixed fields ({len(fixed_fields)})")
    lines.append(_table(
        ["Product", "Field", "Old value", "New value"],
        [[fx["product"], fx["field"], fx["old_value"], fx["new_value"]] for fx in fixed_fields],
    ))

    lines.append(f"#### Potential removals — flagged only, not deleted ({len(potential_removals)})")
    lines.append(_table(
        ["Product", "Platform"],
        [[r["product"], r["platform"]] for r in potential_removals],
    ))

    lines.append(f"#### Unresolved — needs a human ({len(unresolved)})")
    lines.append(_table(
        ["Platform", "Reason"],
        [[u["platform"], u["reason"]] for u in unresolved],
    ))

    return "\n".join(lines)


def main():
    brand = os.environ.get("RECONCILE_BRAND", "aspose.cloud")
    brand_safe = re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-")

    token = os.environ.get("REPO_PAT", "") or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("::error::No REPO_PAT/GITHUB_TOKEN available", file=sys.stderr)
        sys.exit(1)

    report = reconcile(brand=brand, token=token, dry_run=False)

    if "error" in report:
        print(f"::error::Reconciliation failed for {brand}: {report['error']}", file=sys.stderr)
        sys.exit(1)

    summary = format_report(report)
    print(summary)

    has_changes = bool(
        report["new_products"] or report["new_platforms"] or report["fixed_fields"]
    )

    out_dir = os.environ.get("GITHUB_OUTPUT")
    if out_dir:
        with open(out_dir, "a") as f:
            f.write(f"has_changes={'true' if has_changes else 'false'}\n")
            f.write(f"brand_safe={brand_safe}\n")

    with open(f"reconciliation_report_{brand_safe}.md", "w") as f:
        f.write(summary)

    with open(f"reconciliation_report_{brand_safe}.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
