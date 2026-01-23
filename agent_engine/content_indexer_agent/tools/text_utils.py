from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List

import yaml

# Robust frontmatter:
# - Allows UTF-8 BOM at start
# - Allows leading whitespace/newlines
# - Supports LF and CRLF line endings
_FRONTMATTER_RE = re.compile(
    r"^\ufeff?\s*---\s*\r?\n(.*?)\r?\n---\s*\r?\n",
    re.DOTALL,
)

_HEADING_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$", re.MULTILINE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class ParsedMarkdown:
    title: str
    body: str
    # YAML-aware: may contain lists/dicts/booleans, not just strings
    frontmatter: Dict[str, Any]


def parse_markdown(path: Path) -> ParsedMarkdown:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    frontmatter: Dict[str, Any] = {}
    body = raw

    m = _FRONTMATTER_RE.match(raw)
    if m:
        fm_text = m.group(1)
        body = raw[m.end():]

        # Proper YAML parse
        try:
            fm_obj = yaml.safe_load(fm_text) or {}
            if isinstance(fm_obj, dict):
                # normalize keys to lowercase for compatibility with existing code
                frontmatter = {str(k).strip().lower(): v for k, v in fm_obj.items()}
            else:
                frontmatter = {}
        except Exception:
            # Legacy fallback: best-effort key:value parsing
            fm: Dict[str, Any] = {}
            for line in fm_text.splitlines():
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                fm[k.strip().lower()] = v.strip().strip('"').strip("'")
            frontmatter = fm

    title_val = frontmatter.get("title")
    title = (
        (title_val.strip() if isinstance(title_val, str) else None)
        or _first_h1(body)
        or path.stem.replace("-", " ").replace("_", " ")
    )

    return ParsedMarkdown(title=str(title).strip(), body=body, frontmatter=frontmatter)


def _first_h1(body: str) -> Optional[str]:
    m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    return m.group(1).strip() if m else None


def extract_subheadings(markdown_body: str, max_items: int = 30) -> List[str]:
    """
    Extract H2/H3/H4 headings from markdown body.
    Returns list of heading texts (deduped, ordered).
    """
    seen = set()
    out: List[str] = []
    for m in _HEADING_RE.finditer(markdown_body or ""):
        title = m.group(2).strip()
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(title)
        if len(out) >= max_items:
            break
    return out
