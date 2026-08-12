"""
Entry point for the scheduled GitHub Actions job. Calls the reconciler
directly (no MCP transport needed for a batch run — the MCP server in
this same package is for the blog agent's own on-demand use) and writes
a human-readable report the workflow turns into the PR body.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv

load_dotenv()

from reconciler.run import reconcile  # noqa: E402


def format_report(report: dict) -> str:
    lines = []
    lines.append(f"Mode: {report.get('mode', 'unknown')}")
    lines.append("")

    lines.append(f"## New products ({len(report['new_products'])})")
    for item in report["new_products"]:
        missing = f" (missing: {', '.join(item['missing_fields'])})" if item["missing_fields"] else ""
        lines.append(f"- {item['product']}{missing}")
    lines.append("")

    lines.append(f"## New platforms ({len(report['new_platforms'])})")
    for item in report["new_platforms"]:
        missing = f" (missing: {', '.join(item['missing_fields'])})" if item["missing_fields"] else ""
        lines.append(f"- {item['product']}{missing}")
    lines.append("")

    lines.append(f"## Fixed fields ({len(report['fixed_fields'])})")
    for line in report["fixed_fields"]:
        lines.append(f"- {line}")
    lines.append("")

    lines.append(f"## Potential removals — flagged only, not deleted ({len(report['potential_removals'])})")
    for line in report["potential_removals"]:
        lines.append(f"- {line}")
    lines.append("")

    lines.append(f"## Unresolved — needs a human ({len(report['unresolved'])})")
    for line in report["unresolved"]:
        lines.append(f"- {line}")

    return "\n".join(lines)


def main():
    token = os.environ.get("REPO_PAT", "") or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("::error::No REPO_PAT/GITHUB_TOKEN available", file=sys.stderr)
        sys.exit(1)

    report = reconcile(token=token, dry_run=False)

    if "error" in report:
        print(f"::error::Reconciliation failed: {report['error']}", file=sys.stderr)
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

    with open("reconciliation_report.md", "w") as f:
        f.write(summary)

    with open("reconciliation_report.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
