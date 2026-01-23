from __future__ import annotations

import os
from typing import List, Optional, Tuple


def _use_details() -> bool:
    return os.getenv("CG_MD_SUMMARY_DETAILS", "1").strip() not in {"0", "false", "False", "no", "NO"}


def _split_label_value(line: str) -> Optional[Tuple[str, str]]:
    # Handles "Label: value"
    if ":" not in line:
        return None
    left, right = line.split(":", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        return None
    return left, right


def _render_md_table(headers: List[str], rows: List[List[str]]) -> List[str]:
    out: List[str] = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def _align_row_to_headers(headers: List[str], row: List[str]) -> List[str]:
    """
    Align a row to the header length.

    Fix for your case:
      headers = ["Topic", ...platforms]
      row     = ["Category", "Subcategory", "Topic", ...platform cells]

    We drop the two leading taxonomy cells when:
      - header starts with "Topic"
      - row is longer than headers
    """
    hlen = len(headers)
    rlen = len(row)
    if hlen == 0:
        return row

    header0 = headers[0].strip().lower()

    # Most common mismatch after you removed taxonomy from headers:
    # row has 2 extra leading cells (Category, Subcategory).
    if header0 == "topic" and rlen >= hlen + 2:
        # Keep the last `hlen` cells so we preserve [Topic, platform...]
        # This is safer than row[2:] in case upstream adds more leading fields later.
        return row[-hlen:]

    # Generic fallback: truncate or pad to fit
    if rlen > hlen:
        return row[:hlen]
    if rlen < hlen:
        return row + [""] * (hlen - rlen)
    return row


def render_md_matrix(
    title: str,
    summary_lines: List[str],
    headers: List[str],
    rows: List[List[str]],
) -> str:
    """
    Simple Markdown matrix renderer. Keeps output stable for golden tests.

    Enhancements (no agent changes):
    - Summary rendered as a Metric/Value table where possible (collapsible).
    - Matrix rows auto-aligned to headers (drops Category/Subcategory if headers start with Topic).
    """
    out: List[str] = []
    out.append(f"# {title}")
    out.append("")

    if summary_lines:
        out.append("## Summary")
        out.append("")

        # Convert label:value lines into a table, keep other lines as bullets.
        table_rows: List[List[str]] = []
        bullet_lines: List[str] = []

        for line in summary_lines:
            lv = _split_label_value(line)
            if lv:
                table_rows.append([lv[0], lv[1]])
            else:
                bullet_lines.append(line)

        if table_rows:
            table_md_lines = _render_md_table(["Metric", "Value"], table_rows)
            if _use_details():
                out.append("<details>")
                out.append("<summary><strong>Run Metrics</strong></summary>")
                out.append("")
                out.extend(table_md_lines)
                out.append("")
                out.append("</details>")
                out.append("")
            else:
                out.extend(table_md_lines)
                out.append("")

        for line in bullet_lines:
            out.append(f"- {line}")
        if bullet_lines:
            out.append("")

    out.append("## Coverage Matrix")
    out.append("")

    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for r in rows:
        rr = _align_row_to_headers(headers, r)
        out.append("| " + " | ".join(rr) + " |")

    out.append("")
    return "\n".join(out)
