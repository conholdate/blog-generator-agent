"""
Ties discovery, diffing, field derivation, and applying together into
the one operation the MCP tool exposes.

Safety rule that shapes this whole module: a freshly-derived field only
overwrites a stored value when it was independently confirmed (not in
`FieldResult.unverified`). An uncertain re-derivation must never
replace a value that might still be perfectly fine — same principle
used throughout today's manual InstallCommand fixes.
"""
from .config import get_brand_config
from .github_client import GitHubClient
from .inventory import discover_inventory
from .diff import compute_diff, pairs_from_json
from .fields import derive_full_entry, _resolve_redirect
from .apply import apply_field_fixes, append_new_entries, load_raw_and_parsed

# Fields where the "correct" pattern can't be determined from HTTP status
# alone — confirmed for FreeAppsURL while testing groupdocs.cloud: every
# candidate suffix ("family/" and "total") resolves via the exact same
# http->https + trailing-slash redirect chain, so "does it eventually
# resolve" can't tell a genuinely-wrong guess apart from a stylistic one.
# For these, only propose a change when the *current* value is actually
# broken — a working link's exact form isn't worth "fixing" on a guess.
FIELDS_REQUIRE_BROKEN_OLD_VALUE = {"FreeAppsURL"}


def reconcile(brand: str, token: str, dry_run: bool = False) -> dict:
    config = get_brand_config(brand)
    client = GitHubClient(token)

    inventory = discover_inventory(client, config)
    _, existing_products = load_raw_and_parsed(config)
    diff = compute_diff(inventory, existing_products, config)
    stored_by_pair = pairs_from_json(existing_products, config)

    report = {
        "brand": brand,
        "new_products": [],
        "new_platforms": [],
        "fixed_fields": [],
        "unresolved": [],
        "potential_removals": [f"{p.url_prefix}/{p.platform_key}" for p in diff.potential_removals],
    }

    new_entries = []
    for pair in diff.new_products + diff.new_platforms:
        result = derive_full_entry(client, pair.url_prefix, pair.platform_key, config)
        bucket = "new_products" if pair in diff.new_products else "new_platforms"
        if not result.values.get("ProductName"):
            report["unresolved"].append(f"{pair.url_prefix}/{pair.platform_key}: {result.notes.get('ProductName')}")
            continue
        if "ProductURL" in result.unverified:
            # Exists in the source repo, but the live page 404s — likely
            # committed ahead of an actual deploy. Don't add a product
            # whose own primary link is dead; wait for it to go live.
            report["unresolved"].append(f"{pair.url_prefix}/{pair.platform_key}: {result.notes.get('ProductURL')}")
            continue
        new_entries.append(result.values)
        report[bucket].append({
            "product": result.values["ProductName"],
            "missing_fields": result.unverified,
        })

    field_fixes = []
    for pair in diff.existing:
        stored = stored_by_pair.get(pair)
        if not stored:
            continue
        result = derive_full_entry(client, pair.url_prefix, pair.platform_key, config)
        for field_name, new_value in result.values.items():
            if field_name in result.unverified:
                continue
            if field_name == "ProductName":
                continue  # never rename the key we match on in the same pass
            old_value = stored.get(field_name, "")
            if not new_value or new_value == old_value:
                continue
            if field_name in FIELDS_REQUIRE_BROKEN_OLD_VALUE and old_value and _resolve_redirect(old_value) is not None:
                continue  # old value still resolves — a differently-formatted guess isn't a fix
            field_fixes.append({
                "ProductName": stored["ProductName"],
                "field": field_name,
                "value": new_value,
                "old_value": old_value,
            })

    report["fixed_fields"] = [
        f"{fx['ProductName']}.{fx['field']}: {fx['old_value']!r} -> {fx['value']!r}"
        for fx in field_fixes
    ]

    if dry_run:
        report["mode"] = "dry_run"
        return report

    report["mode"] = "applied"
    if field_fixes:
        apply_field_fixes(field_fixes, config)
    if new_entries:
        append_new_entries(new_entries, config)
    return report
