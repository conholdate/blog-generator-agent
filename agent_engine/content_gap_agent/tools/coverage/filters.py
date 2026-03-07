from __future__ import annotations

import re

from ..io import IndexRecord

_RELEASE_PATTERNS = [
    r"\brelease\s*notes?\b",
    r"\bproduct\s*updates?\b",
    r"\bproduct\s*release(s)?\b",
    r"\bversion\s*updates?\b",
    r"\bv?\d+(\.\d+){1,3}\b",
    r"\b(beta|rc|ga)\b",
    r"\bwhat'?s\s*new\b",
    r"\bnew\s*release\b",
]
_RELEASE_RE = re.compile("|".join(_RELEASE_PATTERNS), re.IGNORECASE)


def is_release_update_record(record: IndexRecord) -> bool:
    parts = [
        record.title or "",
        record.topic or "",
        record.url or "",
        record.source_path or "",
        record.category or "",
        record.sub_category or "",
    ]
    text = " ".join(parts)
    return bool(_RELEASE_RE.search(text))

