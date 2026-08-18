"""
Derives every productsData field for one (url_prefix, platform_key) pair.

Split into two tiers, same distinction used when this was done by hand:
  - deterministic fields: pure URL patterns + brand constants, always
    available the moment the product page exists.
  - dynamic fields (InstallCommand, ForumsURL): read from a second
    source and independently verified; left blank rather than guessed
    when that source doesn't have an answer yet.

The two things that differ meaningfully by brand — what a product page
looks like, and how an install command is written — are delegated to
reconciler/brands/{name}.py rather than branched inline here. Everything
else (URL patterns, registry verification, the live-link safety check)
is brand-agnostic, driven entirely by BrandConfig.
"""
from dataclasses import dataclass, field

import requests

from .config import BrandConfig
from .github_client import GitHubClient
from .brands import aspose_cloud, groupdocs_cloud, aspose_com

_BRAND_MODULES = {
    "aspose.cloud": aspose_cloud,
    "groupdocs.cloud": groupdocs_cloud,
    "aspose.com": aspose_com,
}


@dataclass
class FieldResult:
    values: dict = field(default_factory=dict)
    unverified: list = field(default_factory=list)  # field names left blank, needing follow-up
    notes: dict = field(default_factory=dict)        # field name -> why it was set/left blank


def _http_status(url: str, timeout: int = 8) -> int:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=False)
        return r.status_code
    except requests.RequestException:
        return 0


def _resolve_redirect(url: str, timeout: int = 8) -> str | None:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.url if r.status_code < 400 else None
    except requests.RequestException:
        return None


def derive_deterministic_fields(url_prefix: str, platform_key: str, pf_name: str, config: BrandConfig) -> dict:
    """Fields derivable purely from the (url_prefix, platform_key) pair and
    the product's display name — no extra network round-trip beyond what
    already fetched pf_name."""
    info = config.platform_info.get(platform_key, {"language": platform_key})
    language = info["language"]
    prog_language = info.get("prog_language", language)
    category = config.category_template.format(pf_name=pf_name)
    category_slug = category.lower().replace(" ", "-")

    values = {
        "ProductName": config.product_name_template.format(pf_name=pf_name, language=language),
        "Category": category,
        "ProgrammingLanguage": prog_language,
        "ProductURL": f"https://{config.products_domain}/{url_prefix}/{platform_key}/",
        "DownloadURL": f"https://{config.releases_domain}/{url_prefix}/{platform_key}/",
        "DocumentationURL": config.docs_url_template.format(
            docs_domain=config.docs_domain, url_prefix=url_prefix, platform_key=platform_key,
        ),
        "APIReferenceURL": config.api_reference_url_template.format(
            reference_domain=config.reference_domain, url_prefix=url_prefix, platform_key=platform_key,
        ),
        "FreeAppsURL": config.apps_url_template.format(
            apps_domain=config.apps_domain, url_prefix=url_prefix, apps_family_suffix=config.apps_family_suffix,
        ),
        "BlogsURL": f"https://{config.blog_domain}/categories/{category_slug}/",
        "urlPrefix": url_prefix,
        "license": config.brand_license_url,
    }
    if config.pricing_url_template:
        values["pricing"] = config.pricing_url_template.format(url_prefix=url_prefix)
    return values


def _is_plausible_repo_url(url: str, platform_key: str, config: BrandConfig) -> bool:
    """Guards against copy-paste errors on the source page itself (found
    while testing: barcode/python's own page links to the PHP repo).
    A value that doesn't even mention the right platform is not
    trustworthy just because it came from the "real" source."""
    tokens = config.platform_repo_tokens.get(platform_key)
    if not tokens:
        return True  # no known tokens for this platform; nothing to check against
    url_lower = url.lower()
    return any(token in url_lower for token in tokens)


def resolve_forums_url(url_prefix: str, config: BrandConfig) -> tuple[str | None, str]:
    """forum.{brand}/c/{urlPrefix} redirects to the canonical
    /c/{urlPrefix}/{category_id} form on Discourse once the category
    exists. If it doesn't resolve yet, fall back to the un-verified slug
    URL rather than guessing a category number."""
    slug_url = f"https://{config.forum_domain}/c/{url_prefix}"
    resolved = _resolve_redirect(slug_url)
    if resolved:
        return resolved, "verified via redirect"
    return slug_url, "forum category not found yet; unverified slug URL"


def _registry_check(platform_key: str, ref, config: BrandConfig) -> str:
    if not ref:
        return "UNCHECKED"
    try:
        if platform_key == "net":
            code = _http_status(f"https://api.nuget.org/v3-flatcontainer/{ref.lower()}/index.json")
        elif platform_key == "python":
            code = _http_status(f"https://pypi.org/pypi/{ref}/json")
        elif platform_key == "php":
            code = _http_status(f"https://packagist.org/packages/{ref}.json")
        elif platform_key == "ruby":
            code = _http_status(f"https://rubygems.org/api/v1/gems/{ref}.json")
        elif platform_key in ("nodejs", "javascript"):
            enc = ref.replace("/", "%2F") if ref.startswith("@") else ref
            code = _http_status(f"https://registry.npmjs.org/{enc}")
        elif platform_key in ("java", "android") and isinstance(ref, tuple):
            artifact_id = ref[1]
            if not artifact_id:
                return "UNCHECKED"
            code = _http_status(f"https://{config.releases_domain}/java/repo/{config.java_group_path}/{artifact_id}/maven-metadata.xml")
        elif platform_key == "dart":
            code = _http_status(f"https://pub.dev/api/packages/{ref}")
        else:
            return "UNCHECKED"
    except Exception:
        return "UNCHECKED"
    return "VALID" if code == 200 else f"INVALID({code})"


def derive_full_entry(client: GitHubClient, url_prefix: str, platform_key: str, config: BrandConfig) -> FieldResult:
    result = FieldResult()
    brand_module = _BRAND_MODULES.get(config.name)
    if brand_module is None:
        result.notes["ProductName"] = f"no extraction logic registered for brand {config.name!r}"
        return result

    pf_name, external_dl = brand_module.fetch_product_info(client, url_prefix, platform_key, config)
    if not pf_name:
        result.unverified.append("ProductName")
        result.notes["ProductName"] = "product page not found or missing name field"
        return result

    result.values.update(derive_deterministic_fields(url_prefix, platform_key, pf_name, config))

    # Every pattern-derived URL field gets an actual live check — a folder
    # existing in a repo (or a URL template matching the usual shape)
    # doesn't guarantee the real page is deployed and reachable. Confirmed
    # necessary by testing: words/android's ProductURL source exists but
    # 404s live, and aspose.cloud's old (wrong) 3D DownloadURL pattern
    # still returned 200 — a "does it resolve" check alone wouldn't have
    # caught that one, which is why FreeAppsURL additionally gets the
    # stricter "old value must be broken first" rule in run.py; for every
    # other field here, a live check without that extra gate is enough,
    # since we have no evidence (yet) they share FreeAppsURL's ambiguity.
    for url_field in ("ProductURL", "DownloadURL", "DocumentationURL", "APIReferenceURL", "BlogsURL", "FreeAppsURL"):
        candidate = result.values[url_field]
        if _resolve_redirect(candidate) is None:
            result.unverified.append(url_field)
            result.notes[url_field] = f"{candidate} does not resolve live (page may exist in the repo but not be deployed yet)"

    if external_dl and _is_plausible_repo_url(external_dl, platform_key, config):
        if _resolve_redirect(external_dl) is not None:
            result.values["ExternalDownloadURL"] = external_dl
        else:
            result.unverified.append("ExternalDownloadURL")
            result.notes["ExternalDownloadURL"] = f"{external_dl} looks like a real {platform_key} repo but doesn't resolve live"
    elif external_dl:
        result.unverified.append("ExternalDownloadURL")
        result.notes["ExternalDownloadURL"] = (
            f"source page's download link ({external_dl!r}) doesn't look like a {platform_key} repo — "
            "possible copy-paste error on the source page itself; needs a human to confirm"
        )
    else:
        result.unverified.append("ExternalDownloadURL")
        result.notes["ExternalDownloadURL"] = "download link not present on product page"

    forums_url, forums_note = resolve_forums_url(url_prefix, config)
    result.values["ForumsURL"] = forums_url
    result.notes["ForumsURL"] = forums_note
    if "unverified" in forums_note:
        result.unverified.append("ForumsURL")

    cmd, ref, method = brand_module.scrape_install_command(client, url_prefix, platform_key, external_dl, config)
    if cmd:
        status = _registry_check(platform_key, ref, config) if method != "fallback" else "N/A"
        result.values["InstallCommand"] = cmd
        result.notes["InstallCommand"] = f"{method}, registry={status}"
        if method != "fallback" and status not in ("VALID", "N/A"):
            result.unverified.append("InstallCommand")
    else:
        result.unverified.append("InstallCommand")
        result.notes["InstallCommand"] = "no install-command source found"

    return result
