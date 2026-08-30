"""
Repo Registry: brand/product/platform -> Example-Agent repo, read from a
maintained snapshot file (content/exampleRepos/<brand>.json), never a live
GitHub call during a blog run. See build_registry.py for how the snapshot
gets (re)generated.
"""
import json
import os
from dataclasses import dataclass
from typing import Optional

REGISTRY_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../../../content/exampleRepos"
)


@dataclass
class RepoRef:
    repository: str  # "org/name"
    branch: str
    status: str
    last_verified: str
    url_prefix: str


def _normalize_platform(platform: str) -> str:
    p = platform.strip().lower()
    if p in (".net", "net", "dotnet", "c#"):
        return ".NET"
    return platform.strip()


def load_snapshot(brand: str) -> list[dict]:
    path = os.path.join(REGISTRY_DIR, f"{brand.lower().strip()}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def _matches_product(target: str, entry_product: str) -> bool:
    """Exact match, or `target` as a whole-word prefix of the registry's full name
    (e.g. "Aspose.Slides" matching "Aspose.Slides for .NET") - forgives the
    shortened product names people naturally type, without loosening into a
    fuzzy match that could pick the wrong product."""
    entry_lower = entry_product.strip().lower()
    return entry_lower == target or entry_lower.startswith(target + " ")


def resolve(brand: str, product_name: str, platform: str) -> Optional[RepoRef]:
    """Returns a RepoRef only for a product/platform whose repo is known and verified."""
    target_product = product_name.strip().lower()
    target_platform = _normalize_platform(platform)
    matches = [
        e for e in load_snapshot(brand)
        if _matches_product(target_product, e["product"]) and _normalize_platform(e["platform"]) == target_platform
    ]
    if not matches:
        return None
    verified = [e for e in matches if e.get("status") == "verified" and e.get("repository")]
    if not verified:
        return None
    entry = verified[0]
    return RepoRef(
        repository=entry["repository"],
        branch=entry.get("branch", "main"),
        status=entry["status"],
        last_verified=entry.get("last_verified", ""),
        url_prefix=entry["urlPrefix"],
    )


def known_products(brand: str, platform: str | None = None) -> list[str]:
    """Product names that actually HAVE a verified repo, optionally filtered to one
    platform - used to build a helpful NO_MATCH hint instead of a silent dead end.
    Deliberately excludes not_found entries - listing a product with no repo as
    "known" would just recreate the confusion the hint is meant to resolve."""
    target_platform = _normalize_platform(platform) if platform else None
    return sorted({
        e["product"] for e in load_snapshot(brand)
        if e.get("status") == "verified" and e.get("repository")
        and (target_platform is None or _normalize_platform(e["platform"]) == target_platform)
    })
