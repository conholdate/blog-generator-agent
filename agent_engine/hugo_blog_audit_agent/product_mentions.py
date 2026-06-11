from __future__ import annotations

import re

from .models import BlogConfig


PRODUCT_MENTION_RE = re.compile(r"\bAspose\.[A-Z0-9][A-Za-z0-9]*(?:\.[A-Z0-9][A-Za-z0-9]*)?\b")


def extract_product_mentions(text: str) -> list[str]:
    return sorted(set(PRODUCT_MENTION_RE.findall(text)))


def verified_product_mentions(config: BlogConfig | None) -> set[str]:
    if not config:
        return set()
    mentions = {str(mention).lower() for mention in config.known_product_mentions if str(mention).strip()}
    for product_config in config.product_configs.values():
        display_name = str(product_config.get("display_name") or "").strip()
        if display_name.lower().startswith("aspose."):
            mentions.add(display_name.lower())
    return mentions


def is_known_product_mention(mention: str, known_mentions: set[str]) -> bool:
    normalized = mention.lower()
    return normalized in known_mentions or any(normalized.startswith(f"{known}.") for known in known_mentions)
