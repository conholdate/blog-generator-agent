from __future__ import annotations

import re


def slugify(text: str) -> str:
    """Lowercase, hyphen-separated, no dots or special characters — the
    Professional Blogging Guide's slug rule (e.g. no literal ".net").
    """
    text = text.replace(".", " ")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "post"
