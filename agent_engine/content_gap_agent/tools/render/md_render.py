from __future__ import annotations

import os
import re
from typing import List, Optional, Tuple


def _use_details() -> bool:
    return os.getenv("CG_MD_SUMMARY_DETAILS", "1").strip() not in {"0", "false", "False", "no", "NO"}


_TAXONOMY_HEADERS = {"category", "subcategory", "topic"}
_UPPERCASE_TERMS = {
    ".net",
    "asp.net",
    "net",
    "java",
    "python",
    "node",
    "node.js",
    "nodejs",
    "javascript",
    "js",
    "typescript",
    "ts",
    "php",
    "go",
    "ruby",
    "swift",
    "kotlin",
    "android",
    "ios",
    "api",
    "3ds",
    "3mf",
    "7z",
    "ase",
    "bz2",
    "csv",
    "dae",
    "dcm",
    "djvu",
    "doc",
    "docm",
    "docx",
    "dotx",
    "drc",
    "dxf",
    "epub",
    "fbx",
    "gif",
    "glb",
    "gltf",
    "gz",
    "html",
    "htm",
    "igs",
    "iges",
    "jar",
    "jpeg",
    "jpg",
    "json",
    "ma",
    "obj",
    "odp",
    "ods",
    "odt",
    "pdf",
    "ply",
    "png",
    "potx",
    "ppt",
    "pptm",
    "pptx",
    "psd",
    "rar",
    "rtf",
    "sql",
    "stl",
    "svg",
    "tar",
    "tif",
    "tiff",
    "tsv",
    "txt",
    "u3d",
    "usd",
    "usdz",
    "vsdx",
    "wav",
    "webp",
    "wmf",
    "x",
    "xaml",
    "xls",
    "xlsb",
    "xlsm",
    "xlsx",
    "xml",
    "xps",
    "yaml",
    "yml",
    "zip",
}


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


def _uppercase_protected_terms(text: str, protected_terms: set[str]) -> str:
    normalized = " ".join(text.split())
    if not normalized or not protected_terms:
        return normalized

    rendered = normalized.lower()
    for term in sorted({t.lower() for t in protected_terms if t}, key=len, reverse=True):
        rendered = re.sub(
            rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])",
            term.upper(),
            rendered,
            flags=re.IGNORECASE,
        )
    return rendered


def _sentence_case_topic(topic: str, platform_terms: set[str]) -> str:
    protected_terms = set(_UPPERCASE_TERMS)
    protected_terms.update(t.lower() for t in platform_terms if t)

    rendered = _uppercase_protected_terms(topic, protected_terms)
    match = re.search(r"[a-z]", rendered)
    if not match:
        return rendered
    idx = match.start()
    return rendered[:idx] + rendered[idx].upper() + rendered[idx + 1 :]


def _topic_column_index(headers: List[str]) -> Optional[int]:
    for idx, header in enumerate(headers):
        if header.strip().lower() == "topic":
            return idx
    return None


def _platform_terms_from_headers(headers: List[str]) -> set[str]:
    terms: set[str] = set()
    for header in headers:
        value = header.strip()
        if not value or value.lower() in _TAXONOMY_HEADERS:
            continue
        terms.add(value)
    return terms


def _normalize_summary_value(label: str, value: str) -> str:
    if label.strip().lower() != "platforms evaluated":
        return value
    parts = [part.strip() for part in value.split(",")]
    return ", ".join(part.upper() for part in parts if part)


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
                table_rows.append([lv[0], _normalize_summary_value(lv[0], lv[1])])
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

    display_headers = [header.upper() for header in headers]
    topic_idx = _topic_column_index(headers)
    platform_terms = _platform_terms_from_headers(headers)

    out.append("| " + " | ".join(display_headers) + " |")
    out.append("| " + " | ".join(["---"] * len(display_headers)) + " |")

    for r in rows:
        rr = _align_row_to_headers(headers, r)
        if topic_idx is not None and topic_idx < len(rr):
            rr[topic_idx] = _sentence_case_topic(rr[topic_idx], platform_terms)
        out.append("| " + " | ".join(rr) + " |")

    out.append("")
    return "\n".join(out)
