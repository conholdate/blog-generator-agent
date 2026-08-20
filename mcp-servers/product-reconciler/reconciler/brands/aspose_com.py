"""
aspose.com-specific extraction. Implements the same interface as
brands/aspose_cloud.py and brands/groupdocs_cloud.py:

  fetch_product_info(client, url_prefix, platform_key, config) -> (pf_name, external_dl)
  scrape_install_command(client, url_prefix, platform_key, external_dl, config) -> (cmd, ref, method)

Genuinely different shape from both other brands, confirmed by reading real
pages from releases.aspose.com (content/en/{product}/{platform}/_index.md):
  - There is no separate products-repo lookup — this one repo's own pages
    carry the product name, the install-command source, and a GitHub
    examples link, all in one file (see BrandConfig.products_repo ==
    releases_repo for this brand).
  - Body markup varies by platform (net uses <details> blocks, php/nodejs
    use a "consolebox" shortcode, java's isn't scraped from the body at
    all) — but front matter does NOT vary: every page confirmed so far
    carries `linktitle` (the real product name, e.g. "Aspose.Cells for
    .NET") and a `homepage_package_type` / `homepage_package_link` pair
    (NuGet/Maven/Composer/NPM, each pointing at the real package). Deriving
    InstallCommand from that front-matter pair rather than the body avoids
    needing separate scraping logic per platform's shortcode template.

  Java is the one exception: homepage_package_link only gives
  groupId/artifactId, but every real stored Java InstallCommand also
  carries a <version> and a brand-wide <repository> block (Aspose's Java
  packages live on a custom Maven repo, repository.aspose.com/repo/, not
  Maven Central -- confirmed identical across every existing Java entry
  checked). The version comes from a second source: front matter's
  dataFolder names a directory under data/repository/ on this same repo
  holding one JSON file per release (mirrors groupdocs.cloud's Java
  version data, see brands/groupdocs_cloud.py's _latest_java_version).
"""
import json
import re

_JAVA_REPOSITORY_XML = (
    "<repository>\n"
    "  <id>AsposeJavaAPI</id>\n"
    "  <name>Aspose Java API</name>\n"
    "  <url>https://repository.aspose.com/repo/</url>\n"
    "</repository>"
)


def fetch_product_info(client, url_prefix, platform_key, config):
    md = client.get_raw_file(config.products_repo, f"{config.content_root}/{url_prefix}/{platform_key}/_index.md")
    if md is None:
        return None, None

    linktitle_m = re.search(r'^linktitle:\s*"([^"]*)"', md, re.M)
    if linktitle_m:
        pf_name = linktitle_m.group(1).strip()
    else:
        # A handful of pages omit linktitle entirely (confirmed live:
        # content/en/3d/nodejs-java/_index.md) but still carry the same
        # display name under family_listing_page_title instead.
        fallback_m = re.search(r'^family_listing_page_title:\s*"([^"]*)"', md, re.M)
        if not fallback_m:
            return None, None
        pf_name = fallback_m.group(1).strip()
    # pf_name is the FULL display name, e.g. "Aspose.Cells for .NET" or
    # "Aspose.Cells for Node.js via Java" — kept whole (not split) so
    # bridge-platform ProductNames keep their "via X" suffix. Category is
    # derived separately in fields.py by splitting on " for ".

    # No single consistent shortcode/badge form for the GitHub examples
    # link across platforms (badge image on net, plain markdown link on
    # nodejs, "Code Samples" instead of "Examples" on pdf/pythoncpp) —
    # match any of them.
    external_dl = None
    for pattern in (r'\[!\[Examples\][^\]]*\]\(([^)\s]+)\)', r'\[Examples\]\(([^)\s]+)\)', r'\[Code Samples\]\(([^)\s]+)\)'):
        m = re.search(pattern, md)
        if m:
            external_dl = m.group(1)
            break

    return pf_name, external_dl


def _latest_java_release(client, data_folder: str, config) -> dict | None:
    names = client.list_dir(config.releases_repo, f"data/repository/{data_folder}")
    if not names:
        return None
    names = [n for n in names if n.endswith(".json")]
    if not names:
        return None

    def sort_key(n):
        parts = re.findall(r"\d+", n.replace(".json", ""))
        return tuple(int(p) for p in parts) if parts else (0,)

    names.sort(key=sort_key)
    raw = client.get_raw_file(config.releases_repo, f"data/repository/{data_folder}/{names[-1]}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _scrape_body_install_command(md: str):
    """Fallback for pages with no homepage_package_type/link front matter.
    Confirmed live shapes: "go install github.com/.../vNN@latest" (cells,
    total go-cpp, inside <details>/blockquote text) and "go get
    github.com/...@latest" (pdf's go-cpp, inside a consolebox shortcode) —
    one regex covers both. pdf/pythoncpp has a plain "pip install <pkg>"
    inside the same consolebox shortcode. Returns method "scraped_body" so
    fields.py still runs its usual registry-check gate on the result."""
    m = re.search(r'\bgo (install|get) ([A-Za-z0-9./@_-]+)', md)
    if m:
        pkg = m.group(2)
        return f"go {m.group(1)} {pkg}", pkg, "scraped_body"

    m = re.search(r'\bpip install ([A-Za-z0-9._-]+)', md)
    if m:
        pkg = m.group(1)
        return f"pip install {pkg}", pkg, "scraped_body"

    return None, None, "no_source"


def scrape_install_command(client, url_prefix: str, platform_key: str, external_download_url, config):
    """Returns (command, registry_ref, method), derived from the
    `homepage_package_type` / `homepage_package_link` front-matter pair
    rather than the (per-platform-inconsistent) body markup. Confirmed
    live: NuGet (net, and cpp — cpp ships via NuGet here, unlike the
    other two brands' no-package-manager convention), Maven (java),
    Composer (php), NPM (nodejs), Pip (python). Any other package type
    is left unverified rather than guessed."""
    md = client.get_raw_file(config.products_repo, f"{config.content_root}/{url_prefix}/{platform_key}/_index.md")
    if md is None:
        return None, None, "no_source"

    type_m = re.search(r'^homepage_package_type:\s*"?([^"\n]+?)"?\s*$', md, re.M)
    link_m = re.search(r'^homepage_package_link:\s*"([^"]*)"', md, re.M)
    if not type_m or not link_m:
        # A handful of pages (confirmed: every go-cpp folder, pdf/pythoncpp)
        # never got the homepage_package_type/link front-matter fields at
        # all, but still carry a real, working install command as literal
        # text inside a body shortcode (consolebox / <details>) rather than
        # a structured field. pdf/rustcpp has neither — this correctly
        # falls through to "no_source" for it, same as any product with no
        # discoverable install source.
        return _scrape_body_install_command(md)
    pkg_type = type_m.group(1).strip()
    pkg_link = link_m.group(1).strip()

    if pkg_type == "NuGet":
        m = re.search(r'nuget\.org/packages/([A-Za-z0-9._-]+)', pkg_link)
        if m:
            pkg = m.group(1)
            return f"dotnet add package {pkg}", pkg, "derived_badge"
        return None, None, "no_source"

    if pkg_type == "Maven":
        folder_m = re.search(r'^dataFolder:\s*(\S+)\s*$', md, re.M)
        if not folder_m:
            return None, None, "no_source"
        release = _latest_java_release(client, folder_m.group(1).strip(), config)
        if not release or not release.get("groupId") or not release.get("artifactId"):
            return None, None, "no_source"
        group_id, artifact_id, version = release["groupId"], release["artifactId"], release.get("version", "")
        xml = (
            f"{_JAVA_REPOSITORY_XML}\n"
            f"<dependency>\n<groupId>{group_id}</groupId>\n<artifactId>{artifact_id}</artifactId>\n"
            f"<version>{version}</version>\n</dependency>"
        )
        return xml, (group_id, artifact_id), "verbatim"

    if pkg_type == "Composer":
        m = re.search(r'packagist\.org/packages/([A-Za-z0-9._-]+/[A-Za-z0-9._-]+)', pkg_link)
        if m:
            pkg = m.group(1)
            return f"composer require {pkg}", pkg, "derived_badge"
        return None, None, "no_source"

    if pkg_type == "NPM":
        m = re.search(r'npmjs\.(?:com|org)/package/([A-Za-z0-9@/_.-]+)', pkg_link)
        if m:
            pkg = m.group(1)
            return f"npm install {pkg}", pkg, "derived_badge"
        return None, None, "no_source"

    if pkg_type == "Pip":
        m = re.search(r'pypi\.org/project/([A-Za-z0-9._-]+)', pkg_link)
        if m:
            pkg = m.group(1)
            return f"pip install {pkg}", pkg, "derived_badge"
        return None, None, "no_source"

    return None, None, "no_source"
