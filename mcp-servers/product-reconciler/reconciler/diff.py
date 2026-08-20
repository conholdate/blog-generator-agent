"""
Compares a brand's live products-repo inventory against the entries
already recorded in that brand's productsData JSON, and buckets every
pair into one of the outcomes discussed with the product owner: new
product, new platform, existing (needs a freshness check), or
potential removal.

Renames are deliberately not auto-detected here — a removal and an
addition that might be the same product renamed are surfaced as two
separate, honest findings rather than a guessed link between them.
"""
from dataclasses import dataclass
from urllib.parse import urlparse

from .config import BrandConfig
from .inventory import InventoryItem, normalize_platform_key


@dataclass(frozen=True)
class Pair:
    url_prefix: str
    platform_key: str


@dataclass
class DiffResult:
    new_products: list[Pair]       # url_prefix has no entries in the JSON at all
    new_platforms: list[Pair]      # url_prefix exists, this platform doesn't
    existing: list[Pair]           # present on both sides -> candidate for a freshness check
    potential_removals: list[Pair] # in the JSON but no longer on products.aspose.cloud


def pairs_from_json(products: list[dict], config: BrandConfig) -> dict[Pair, dict]:
    by_pair: dict[Pair, dict] = {}
    for p in products:
        parts = [seg for seg in urlparse(p.get("ProductURL", "")).path.split("/") if seg]
        if len(parts) < 2:
            continue
        url_prefix, raw_platform = parts[0], parts[1]
        platform_key = config.json_slug_aliases.get(
            (url_prefix, raw_platform), normalize_platform_key(raw_platform, config)
        )
        by_pair[Pair(url_prefix, platform_key)] = p
    return by_pair


def compute_diff(inventory: list[InventoryItem], existing_products: list[dict], config: BrandConfig) -> DiffResult:
    live_pairs = {Pair(item.url_prefix, item.platform_key) for item in inventory}
    json_pairs = pairs_from_json(existing_products, config)
    json_url_prefixes = {pair.url_prefix for pair in json_pairs}

    new_products, new_platforms, existing = [], [], []
    for pair in sorted(live_pairs, key=lambda x: (x.url_prefix, x.platform_key)):
        if pair in json_pairs:
            existing.append(pair)
        elif pair.url_prefix not in json_url_prefixes:
            new_products.append(pair)
        else:
            new_platforms.append(pair)

    potential_removals = sorted(
        (pair for pair in json_pairs if pair not in live_pairs),
        key=lambda x: (x.url_prefix, x.platform_key),
    )

    return DiffResult(
        new_products=new_products,
        new_platforms=new_platforms,
        existing=existing,
        potential_removals=potential_removals,
    )
