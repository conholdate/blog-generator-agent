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


def _pair_from_url(url: str, config: BrandConfig) -> Pair | None:
    parts = [seg for seg in urlparse(url).path.split("/") if seg]
    if len(parts) < 2:
        return None
    url_prefix, raw_platform = parts[0], parts[1]
    platform_key = config.json_slug_aliases.get(
        (url_prefix, raw_platform), normalize_platform_key(raw_platform, config)
    )
    return Pair(url_prefix, platform_key)


def _candidate_pairs(entry: dict, config: BrandConfig) -> list[Pair]:
    """Every (url_prefix, platform_key) this entry's own stored URLs
    suggest, DownloadURL first then ProductURL, deduplicated.

    DownloadURL is normally the more reliable signal — fields.py's
    deterministic template always derives it straight from platform_key,
    with no slug override applied — but either field can, for a product
    that shares a page with a sibling, collide with a different, real
    product: confirmed live twice on aspose.com. ocr/java-gpu has no
    standalone product page, so its ProductURL points at ocr/java's
    (DownloadURL stays correctly distinct). slides/net-core is a
    discontinued SDK whose DownloadURL was never given its own release
    page and still points at slides/net's (ProductURL stays correctly
    distinct, and net-core isn't even a live platform any more). Neither
    field is safe to trust alone; keeping both lets pairs_from_json's
    collision resolution fall back to whichever one is actually unique
    for this particular entry.
    """
    seen, candidates = set(), []
    for field_name in ("DownloadURL", "ProductURL"):
        pair = _pair_from_url(entry.get(field_name, ""), config)
        if pair and pair not in seen:
            seen.add(pair)
            candidates.append(pair)
    return candidates


def pairs_from_json(products: list[dict], config: BrandConfig) -> dict[Pair, dict]:
    """Match each stored entry back to its (url_prefix, platform_key) pair.

    Two entries can legitimately propose the same first-choice pair (see
    _candidate_pairs) when they share a URL with a sibling product.
    Resolve that by giving the contested pair to whichever entry has no
    other viable candidate, and letting the other fall back to its
    alternate — which is never a guess, only ever a pair that entry's own
    stored URL actually names. This is enough to correctly split both
    confirmed real cases (ocr/java vs ocr/java-gpu, slides/net vs
    slides/net-core) without needing a live network check, since in both
    cases exactly one side of the collision has a genuinely unique
    alternate and the other doesn't.
    """
    entries = [(p, _candidate_pairs(p, config)) for p in products]

    claimants: dict[Pair, list[int]] = {}
    for i, (_, candidates) in enumerate(entries):
        if candidates:
            claimants.setdefault(candidates[0], []).append(i)

    by_pair: dict[Pair, dict] = {}
    contested: list[int] = []
    for pair, idxs in claimants.items():
        if len(idxs) == 1:
            by_pair[pair] = entries[idxs[0]][0]
        else:
            contested.extend(idxs)

    still_contested: list[int] = []
    for i in contested:
        entry, candidates = entries[i]
        for pair in candidates[1:]:
            if pair not in by_pair:
                by_pair[pair] = entry
                break
        else:
            still_contested.append(i)

    # Last resort for a pair still contested with no viable alternate on
    # either side (not yet observed in real data): keep this function's
    # original behavior, the last entry in the array wins, rather than
    # dropping the pair entirely.
    for i in still_contested:
        entry, candidates = entries[i]
        if candidates:
            by_pair[candidates[0]] = entry

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
