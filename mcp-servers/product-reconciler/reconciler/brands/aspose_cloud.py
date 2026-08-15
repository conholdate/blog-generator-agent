"""
aspose.cloud-specific extraction: what a product page looks like, and
where an install command is found. Implements the interface fields.py
dispatches to:

  fetch_product_info(client, url_prefix, platform_key, config) -> (pf_name, external_dl)
  scrape_install_command(url_prefix, platform_key, external_dl, config) -> (cmd, ref, method)

Product pages use a Hugo shortcode (pfName="..." directDownloadLink="...")
rather than plain front matter, and install commands live on the live
rendered releases.aspose.cloud page (no clean repo source for that field
was ever confirmed) inside either a "consolebox" shortcode or, for Java,
a pre-rendered dependency snippet under an "install-script" id.
"""
import html
import re

import requests


def fetch_product_info(client, url_prefix, platform_key, config):
    """Most products keep pages at content/{product}/{platform}/_index.md, but
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


def _extract_install_script_blocks(html_text: str) -> dict:
    blocks = {}
    for m in re.finditer(
        r'<pre class=install-script id=([a-z0-9-]+)-text><code class=install-command-row>(.*?)</code>',
        html_text, re.S,
    ):
        blocks[m.group(1)] = html.unescape(m.group(2)).strip()
    return blocks


def _fetch_release_page_html(url_prefix: str, platform_key: str, config) -> str | None:
    try:
        r = requests.get(f"https://{config.releases_domain}/{url_prefix}/{platform_key}/", timeout=10)
        return r.text if r.status_code == 200 else None
    except requests.RequestException:
        return None


def scrape_install_command(client, url_prefix: str, platform_key: str, external_download_url, config):
    """Returns (command, registry_ref, method). Mirrors the extraction
    logic validated against 113 real aspose.cloud entries.

    client is accepted for interface parity with other brands (groupdocs.cloud
    needs it to read the GitHub API) but unused here — aspose.cloud's install
    command comes from the live rendered page, not a repo file."""
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
