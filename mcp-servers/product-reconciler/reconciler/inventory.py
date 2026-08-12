"""
Discovers the live product/platform inventory from products.aspose.cloud
and normalizes platform identifiers so they compare cleanly against
aspose.cloud.json.
"""
from dataclasses import dataclass

from .config import PRODUCTS_REPO, NON_PLATFORM_FOLDERS, PLATFORM_ALIASES, PLATFORM_INFO

_ALIAS_TO_CANONICAL = {
    alias: canonical
    for canonical, aliases in PLATFORM_ALIASES.items()
    for alias in aliases
}
from .github_client import GitHubClient


@dataclass(frozen=True)
class InventoryItem:
    url_prefix: str    # product family folder, e.g. "barcode"
    platform_key: str  # platform folder, e.g. "net"


def normalize_platform_key(name: str) -> str:
    """Canonicalize a platform folder name so naming drift (node vs nodejs)
    doesn't get reported as a fake addition/removal."""
    n = name.strip().lower()
    return _ALIAS_TO_CANONICAL.get(n, n)


def _list_platform_folders(client: GitHubClient, product: str) -> list[str]:
    """Most products keep platform folders directly under content/{product}/
    (e.g. barcode/net/). A few (confirmed: cells, total) are locale-nested
    instead — content/{product}/en/net/ — with the top level being locale
    codes, not platforms. Detect that by checking whether anything at the
    top level is a known platform key; if not, and "en" is present,
    descend into it."""
    top_level = client.list_dir(PRODUCTS_REPO, f"content/{product}")
    if not top_level:
        return []

    known_platforms = set(PLATFORM_INFO.keys()) | {a for aliases in PLATFORM_ALIASES.values() for a in aliases}
    if any(normalize_platform_key(name) in known_platforms for name in top_level):
        return top_level

    if "en" in top_level:
        nested = client.list_dir(PRODUCTS_REPO, f"content/{product}/en")
        return nested or []

    return top_level


_KNOWN_PLATFORM_KEYS = set(PLATFORM_INFO.keys()) | {a for aliases in PLATFORM_ALIASES.values() for a in aliases}


def discover_inventory(client: GitHubClient) -> list[InventoryItem]:
    """Every (product, platform) pair currently published on products.aspose.cloud.

    Only folder names recognized as a known SDK platform (PLATFORM_INFO)
    are treated as platforms. This is deliberately conservative: a
    genuinely new platform type Aspose has never shipped before needs a
    one-line addition to PLATFORM_INFO before it's picked up, but a random
    non-platform folder (a locale code, a feature/operation subpage like
    Cells' "merge"/"export" pages) can never masquerade as one — exactly
    the bug that surfaced while testing against the real repo."""
    product_folders = client.list_dir(PRODUCTS_REPO, "content")
    if not product_folders:
        raise RuntimeError("Could not list products.aspose.cloud content/ — check repo access")

    items: list[InventoryItem] = []
    for product in product_folders:
        if product.startswith("_") or product.startswith("."):
            continue
        platform_folders = _list_platform_folders(client, product)
        for platform in platform_folders:
            normalized = normalize_platform_key(platform)
            if normalized not in _KNOWN_PLATFORM_KEYS:
                continue
            items.append(InventoryItem(url_prefix=product, platform_key=normalized))
    return items
