from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from agent_engine.config_sources import list_product_configs
from agent_engine.blog_keyword_analyzer.tools.normalization import (
    canonical_blog_platform_key,
    canonical_product_name,
    normalize_product_short_name,
)


def _brand_config_key(brand: str) -> str:
    return (brand or "").strip().lower().replace(".", "_").replace("-", "_").replace(" ", "_")


@lru_cache(maxsize=None)
def load_product_taxonomy(brand: str = "Aspose") -> dict[str, dict[str, Any]]:
    taxonomy: dict[str, dict[str, Any]] = {}
    for cfg in list_product_configs(_brand_config_key(brand)):
        display_name = str(cfg.get("display_name") or "").strip()
        key = str(cfg.get("key") or "").strip()
        if not display_name and not key:
            continue
        product_name = display_name or canonical_product_name(brand, key)
        data = dict(cfg)
        data["product"] = product_name
        if "languages" not in data:
            languages: list[str] = []
            for item in data.get("platforms") or []:
                if not isinstance(item, dict):
                    continue
                for platform_key, platform_data in item.items():
                    if isinstance(platform_data, dict) and platform_data.get("enabled") is False:
                        continue
                    languages.append(str(platform_key))
            if languages:
                data["languages"] = languages
        taxonomy[product_name] = data
        if key:
            taxonomy[key] = data
            taxonomy[canonical_product_name(brand, key)] = data
    return taxonomy


def resolve_product_taxonomy(product: str, brand: str = "Aspose") -> dict[str, Any]:
    taxonomy = load_product_taxonomy(brand)
    short_name = normalize_product_short_name(product)
    candidates = [
        product,
        short_name,
        canonical_product_name(brand, product),
        canonical_product_name(brand, short_name),
    ]
    for candidate in candidates:
        if candidate in taxonomy:
            data = dict(taxonomy[candidate])
            data["product"] = candidate
            return data

    # Generic fallback keeps non-Aspose or not-yet-modeled products useful.
    return {
        "product": short_name or product,
        "strategic_cluster": "Document Automation",
        "formats": [],
        "actions": [
            "convert",
            "create",
            "edit",
            "merge",
            "split",
            "extract",
            "render",
            "protect",
            "generate",
        ],
        "languages": ["java", "net", "python", "nodejs"],
        "money_pages": {},
        "docs_pages": {},
    }


def supported_formats(product: str, brand: str = "Aspose") -> list[str]:
    return list(resolve_product_taxonomy(product, brand).get("formats") or [])


def supported_actions(product: str, brand: str = "Aspose") -> list[str]:
    return list(resolve_product_taxonomy(product, brand).get("actions") or [])


def strategic_cluster(product: str, brand: str = "Aspose") -> str:
    return str(resolve_product_taxonomy(product, brand).get("strategic_cluster") or "")


def page_target(
    product: str,
    platform: Optional[str],
    *,
    brand: str = "Aspose",
    target_type: str = "money_pages",
) -> str:
    data = resolve_product_taxonomy(product, brand)
    pages = data.get(target_type) or {}
    if not isinstance(pages, dict):
        return ""
    key = canonical_blog_platform_key(platform or "")
    if key and key in pages:
        return str(pages[key])
    base_key = {
        "csharp": "net",
        "node": "nodejs",
    }.get(key or "", key or "")
    if base_key and base_key in pages:
        return str(pages[base_key])
    if pages:
        return str(next(iter(pages.values())))
    return ""
