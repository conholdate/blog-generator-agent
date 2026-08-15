"""
Discovers the live product/platform inventory from a brand's products
repo and normalizes platform identifiers so they compare cleanly
against that brand's productsData JSON.
"""
from dataclasses import dataclass

from .config import BrandConfig
from .github_client import GitHubClient


@dataclass(frozen=True)
class InventoryItem:
    url_prefix: str    # product family folder, e.g. "barcode"
    platform_key: str  # platform folder, e.g. "net"


def _alias_to_canonical(config: BrandConfig) -> dict:
    return {
        alias: canonical
        for canonical, aliases in config.platform_aliases.items()
        for alias in aliases
    }


def normalize_platform_key(name: str, config: BrandConfig) -> str:
    """Canonicalize a platform folder name so naming drift (node vs nodejs)
    doesn't get reported as a fake addition/removal."""
    n = name.strip().lower()
    return _alias_to_canonical(config).get(n, n)


def known_platform_keys(config: BrandConfig) -> set:
    return set(config.platform_info.keys()) | {a for aliases in config.platform_aliases.values() for a in aliases}


def _list_platform_folders(client: GitHubClient, product: str, config: BrandConfig) -> list[str]:
    """Most products keep platform folders directly under content/{product}/
    (e.g. barcode/net/). A few (confirmed: cells, total) are locale-nested
    instead — content/{product}/en/net/ — with the top level being locale
    codes, not platforms. Detect that by checking whether anything at the
    top level is a known platform key; if not, and "en" is present,
    descend into it."""
    top_level = client.list_dir(config.products_repo, f"{config.content_root}/{product}")
    if not top_level:
        return []

    known = known_platform_keys(config)
    if any(normalize_platform_key(name, config) in known for name in top_level):
        return top_level

    if "en" in top_level:
        nested = client.list_dir(config.products_repo, f"{config.content_root}/{product}/en")
        return nested or []

    return top_level


def discover_inventory(client: GitHubClient, config: BrandConfig) -> list[InventoryItem]:
    """Every (product, platform) pair currently published on this brand's
    products repo.

    Only folder names recognized as a known SDK platform (config.platform_info)
    are treated as platforms. This is deliberately conservative: a
    genuinely new platform type never shipped before needs a one-line
    addition to that brand's platform_info before it's picked up, but a
    random non-platform folder (a locale code, a feature/operation subpage
    like Cells' "merge"/"export" pages) can never masquerade as one —
    exactly the bug that surfaced while testing against the real repo."""
    product_folders = client.list_dir(config.products_repo, config.content_root)
    if not product_folders:
        reason = client.last_error or "no additional detail captured"
        raise RuntimeError(f"Could not list {config.products_repo}/{config.content_root} — {reason}")

    known = known_platform_keys(config)
    items: list[InventoryItem] = []
    for product in product_folders:
        if product.startswith("_") or product.startswith("."):
            continue
        platform_folders = _list_platform_folders(client, product, config)
        for platform in platform_folders:
            normalized = normalize_platform_key(platform, config)
            if normalized not in known:
                continue
            items.append(InventoryItem(url_prefix=product, platform_key=normalized))
    return items
