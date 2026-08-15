"""
Derives every productsData field for one (url_prefix, platform_key) pair.

Split into two tiers, same distinction used when this was done by hand:
  - deterministic fields: pure URL patterns + brand constants, always
    available the moment the product page exists.
  - dynamic fields (InstallCommand, ForumsURL): read from a second
    source and independently verified; left blank rather than guessed
    when that source doesn't have an answer yet.

Note: unlike the config/repo/URL layer, this extraction logic (what a
"platform page" looks like, how an install command is written) is still
tied to aspose.cloud's specific page templates — confirmed today that
groupdocs.cloud and aspose.com each use meaningfully different markup.
A second brand needs its own extraction logic here, not just a new
BrandConfig entry.
"""
import html
import re
from dataclasses import dataclass, field

import requests

from .config import BrandConfig
from .github_client import GitHubClient


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
    category = f"{pf_name} Cloud Product Family"
    category_slug = category.lower().replace(" ", "-")

    return {
        "ProductName": f"{pf_name} Cloud SDK for {language}",
        "Category": category,
        "ProgrammingLanguage": language,
        "ProductURL": f"https://{config.products_domain}/{url_prefix}/{platform_key}/",
        "DownloadURL": f"https://{config.releases_domain}/{url_prefix}/{platform_key}/",
        "DocumentationURL": f"https://{config.docs_domain}/{url_prefix}/",
        "APIReferenceURL": f"https://{config.reference_domain}/{url_prefix}/",
        "FreeAppsURL": f"https://{config.apps_domain}/{url_prefix}/family/",
        "BlogsURL": f"https://{config.blog_domain}/categories/{category_slug}/",
        "urlPrefix": url_prefix,
        "license": config.brand_license_url,
    }


def fetch_pf_name_and_external_download(client: GitHubClient, url_prefix: str, platform_key: str, config: BrandConfig) -> tuple[str | None, str | None]:
    """Reads the product's own page for its display name (pfName) and its
    GitHub SDK repo link — the two things that aren't derivable from a URL
    pattern alone.

    Most products keep pages at content/{product}/{platform}/_index.md, but
    a few (cells, total — confirmed while testing this) are locale-nested
    at content/{product}/en/{platform}/_index.md instead. Try the common
    layout first, fall back to the locale-nested one."""
    md = client.get_raw_file(config.products_repo, f"content/{url_prefix}/{platform_key}/_index.md")
    if md is None:
        md = client.get_raw_file(config.products_repo, f"content/{url_prefix}/en/{platform_key}/_index.md")
    if md is None:
        return None, None
    pf_match = re.search(r'pfName="([^"]*)"', md)
    dl_match = re.search(r'directDownloadLink="([^"]*)"', md)
    pf_name = pf_match.group(1) if pf_match else None
    external_dl = dl_match.group(1) if dl_match else None
    return pf_name, external_dl


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


def _extract_install_script_blocks(html_text: str) -> dict:
    blocks = {}
    for m in re.finditer(
        r'<pre class=install-script id=([a-z0-9-]+)-text><code class=install-command-row>(.*?)</code>',
        html_text, re.S,
    ):
        blocks[m.group(1)] = html.unescape(m.group(2)).strip()
    return blocks


def _scrape_install_command(url_prefix: str, platform_key: str, external_download_url: str | None, config: BrandConfig) -> tuple[str | None, str | None, str]:
    """Returns (command, registry_ref, method). Mirrors the extraction
    logic validated against 113 real aspose.cloud entries earlier today.

    Note: unlike products.aspose.cloud, no clean Hugo source for
    releases.aspose.cloud's per-platform install text was confirmed, so
    this deliberately reads the live rendered page rather than guessing
    a repo path that was never verified."""
    page = _fetch_release_page_html(url_prefix, platform_key, config)
    if page is None:
        return None, None, "no_source"

    widgets = _extract_install_script_blocks(page)

    if platform_key == "net":
        m = re.search(r'dotnet add package [^<"\n]+', page)
        if m:
            return m.group(0).strip(), None, "verbatim"
        m = re.search(r'nuget\.org/packages/([A-Za-z0-9._-]+)', page)
        if m:
            return f"dotnet add package {m.group(1)}", m.group(1), "derived_badge"
        return None, None, "no_source"

    if platform_key == "java":
        if "package-manager" in widgets:
            xml = widgets["package-manager"]
            gm = re.search(r'<groupId>([^<]+)</groupId>', xml)
            am = re.search(r'<artifactId>([^<]+)</artifactId>', xml)
            return xml, (gm.group(1) if gm else None, am.group(1) if am else None), "verbatim"
        return None, None, "no_source"

    if platform_key == "python":
        m = re.search(r'pip install [A-Za-z0-9_.\-]+', page)
        return (m.group(0).strip(), m.group(0).replace("pip install ", "").strip(), "verbatim") if m else (None, None, "no_source")

    if platform_key == "php":
        m = re.search(r'composer require [A-Za-z0-9_.\-/]+', page)
        return (m.group(0).strip(), m.group(0).replace("composer require ", "").strip(), "verbatim") if m else (None, None, "no_source")

    if platform_key == "ruby":
        m = re.search(r'gem install [A-Za-z0-9_\-]+', page)
        return (m.group(0).strip(), m.group(0).replace("gem install ", "").strip(), "verbatim") if m else (None, None, "no_source")

    if platform_key in ("nodejs", "javascript"):
        m = re.search(r'npm install (@?[A-Za-z0-9_./\-]+)( --save)?', page)
        if m:
            save = " --save" if m.group(2) else ""
            return f"npm install {m.group(1)}{save}", m.group(1), "verbatim"
        m = re.search(r'npmjs\.(?:com|org)/package/([A-Za-z0-9@/_.\-]+)', page)
        if m:
            return f"npm install {m.group(1)}", m.group(1), "derived_badge"
        return None, None, "no_source"

    if platform_key == "go":
        m = re.search(r'go get [^\s<"]+', page)
        if m:
            return m.group(0).strip(), None, "verbatim"
        if external_download_url:
            return f"go get {external_download_url.replace('https://', '')}", None, "derived_external"
        return None, None, "no_source"

    if platform_key == "dart":
        m = re.search(r'pub (?:global activate|add) [A-Za-z0-9_\-]+', page)
        if m:
            return m.group(0).strip(), m.group(0).split()[-1], "verbatim"
        m = re.search(r'pub\.dev/packages/([A-Za-z0-9_.\-]+)', page)
        if m:
            return f"pub add {m.group(1)}", m.group(1), "derived_badge"
        return None, None, "no_source"

    if platform_key == "perl":
        m = re.search(r'cpan install [A-Za-z0-9:_\-]+', page)
        if m:
            return m.group(0).strip(), None, "verbatim"
        m = re.search(r'metacpan\.org/(?:release|dist)/([A-Za-z0-9_\-]+)', page)
        if m:
            return f"cpan install {m.group(1).replace('-', '::')}", None, "derived_badge"
        return None, None, "no_source"

    if platform_key == "swift":
        m = re.search(r'swift package add [^\s<"]+', page)
        return (m.group(0).strip(), None, "verbatim") if m else (None, None, "no_source")

    if platform_key == "cpp":
        return config.cpp_fallback_command, None, "fallback"

    return None, None, "no_source"


def _fetch_release_page_html(url_prefix: str, platform_key: str, config: BrandConfig) -> str | None:
    """releases.aspose.cloud doesn't expose its Hugo source the same way
    products.aspose.cloud does for every field, so InstallCommand falls
    back to the live rendered page, same source proven during today's
    113-entry audit."""
    try:
        r = requests.get(f"https://{config.releases_domain}/{url_prefix}/{platform_key}/", timeout=10)
        return r.text if r.status_code == 200 else None
    except requests.RequestException:
        return None


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
        elif platform_key == "java" and isinstance(ref, tuple):
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

    pf_name, external_dl = fetch_pf_name_and_external_download(client, url_prefix, platform_key, config)
    if not pf_name:
        result.unverified.append("ProductName")
        result.notes["ProductName"] = "product page not found or missing pfName attribute"
        return result

    result.values.update(derive_deterministic_fields(url_prefix, platform_key, pf_name, config))

    # A folder existing in the products repo doesn't guarantee the page is
    # actually deployed (found while testing: words/android's source
    # exists, but the site 404s on it — likely committed ahead of a real
    # release). Confirm the primary link is actually live before this
    # entry is trusted enough to add.
    product_url = result.values["ProductURL"]
    if _resolve_redirect(product_url) is None:
        result.unverified.append("ProductURL")
        result.notes["ProductURL"] = f"{product_url} does not resolve live (page may exist in the repo but not be deployed yet)"

    if external_dl and _is_plausible_repo_url(external_dl, platform_key, config):
        result.values["ExternalDownloadURL"] = external_dl
    elif external_dl:
        result.unverified.append("ExternalDownloadURL")
        result.notes["ExternalDownloadURL"] = (
            f"source page's directDownloadLink ({external_dl!r}) doesn't look like a {platform_key} repo — "
            "possible copy-paste error on the source page itself; needs a human to confirm"
        )
    else:
        result.unverified.append("ExternalDownloadURL")
        result.notes["ExternalDownloadURL"] = "directDownloadLink not present on product page"

    forums_url, forums_note = resolve_forums_url(url_prefix, config)
    result.values["ForumsURL"] = forums_url
    result.notes["ForumsURL"] = forums_note
    if "unverified" in forums_note:
        result.unverified.append("ForumsURL")

    cmd, ref, method = _scrape_install_command(url_prefix, platform_key, external_dl, config)
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
