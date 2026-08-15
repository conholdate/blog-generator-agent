"""
groupdocs.cloud-specific extraction. Implements the same interface as
brands/aspose_cloud.py:

  fetch_product_info(client, url_prefix, platform_key, config) -> (pf_name, external_dl)
  scrape_install_command(client, url_prefix, platform_key, external_dl, config) -> (cmd, ref, method)

Genuinely different markup from aspose.cloud, confirmed while auditing
this brand's InstallCommand field earlier:
  - Product pages use plain Hugo front-matter fields (product:, platform:,
    right.link_download:), not a shortcode with quoted attributes.
  - Java's real package data lives in structured JSON at
    data/repository/groupdocs_{product}_cloud/{version}.json on the
    releases repo (groupId/artifactId/version) — no page-scraping needed.
  - Every other platform's install command is plain markdown wrapped in
    blockquote markers (sometimes doubled: "> > npm install ...") inside
    a fenced code block, on the releases repo's content/en/ tree — a
    different content root than the products repo's content/english/.
"""
import json
import re


def fetch_product_info(client, url_prefix, platform_key, config):
    md = client.get_raw_file(config.products_repo, f"{config.content_root}/{url_prefix}/{platform_key}/_index.md")
    if md is None:
        return None, None
    # Anchored at line start: top-level front-matter fields only, not the
    # same-named keys nested under submenu.left further down the file.
    product_match = re.search(r'^product:\s*"([^"]*)"', md, re.M)
    if not product_match:
        return None, None
    pf_name = f"GroupDocs.{product_match.group(1)}"
    dl_match = re.search(r'link_download:\s*"([^"]*)"', md)
    external_dl = dl_match.group(1) if dl_match else None
    return pf_name, external_dl


def _strip_blockquote(text: str) -> str:
    return "\n".join(re.sub(r'^(>\s?)+', '', line) for line in text.split("\n"))


def _resolve_releases_folder(client, url_prefix: str, platform_key: str, config) -> str | None:
    """The releases repo's platform folder name doesn't always match the
    products repo's (confirmed: assembly's Node.js page is named "node"
    there, not "nodejs") — try every known alias against the real listing
    rather than assuming."""
    listing = client.list_dir(config.releases_repo, f"content/en/{url_prefix}")
    if not listing:
        return None
    candidates = [platform_key] + [a for a in config.platform_aliases.get(platform_key, []) if a != platform_key]
    for candidate in candidates:
        if candidate in listing:
            return candidate
    return None


def _latest_java_version(client, url_prefix: str, config) -> dict | None:
    folder = f"data/repository/groupdocs_{url_prefix}_cloud"
    names = client.list_dir(config.releases_repo, folder)
    if not names:
        return None
    names = [n for n in names if n.endswith(".json")]
    if not names:
        return None

    def sort_key(n):
        parts = re.findall(r"\d+", n.replace(".json", ""))
        return tuple(int(p) for p in parts) if parts else (0,)

    names.sort(key=sort_key)
    raw = client.get_raw_file(config.releases_repo, f"{folder}/{names[-1]}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def scrape_install_command(client, url_prefix: str, platform_key: str, external_download_url, config):
    """Returns (command, registry_ref, method). Mirrors the extraction
    logic validated against real groupdocs.cloud entries earlier today."""
    if platform_key == "java":
        j = _latest_java_version(client, url_prefix, config)
        if j and j.get("groupId") and j.get("artifactId"):
            xml = (
                f"<dependency>\n<groupId>{j['groupId']}</groupId>\n"
                f"<artifactId>{j['artifactId']}</artifactId>\n"
                f"<version>{j.get('version', '')}</version>\n</dependency>"
            )
            return xml, ("java", j["artifactId"]), "verbatim"
        return None, None, "no_source"

    if platform_key in ("cpp", "apex"):
        # No package manager for either — same fallback convention used
        # for C++ everywhere else in this brand's data.
        fallback = config.cpp_fallback_command if platform_key == "cpp" else "See documentation for build instructions"
        return fallback, None, "fallback"

    folder = _resolve_releases_folder(client, url_prefix, platform_key, config)
    if not folder:
        return None, None, "no_source"

    md = client.get_raw_file(config.releases_repo, f"content/en/{url_prefix}/{folder}/_index.md")
    if md is None:
        return None, None, "no_source"
    text = _strip_blockquote(md)

    if platform_key == "net":
        m = re.search(r'Install-Package\s+([A-Za-z0-9._-]+)', text)
        if m:
            return f"dotnet add package {m.group(1)}", m.group(1), "derived_badge"
        return None, None, "no_source"

    if platform_key == "python":
        m = re.search(r'```[a-z]*\s*\n(pip install [A-Za-z0-9_.\-]+)', text)
        if m:
            name = m.group(1).replace("pip install ", "").strip()
            return m.group(1).strip(), name, "verbatim"
        return None, None, "no_source"

    if platform_key == "php":
        m = re.search(r'```[a-z]*\s*\n(composer require [A-Za-z0-9_.\-/]+)', text)
        if m:
            name = m.group(1).replace("composer require ", "").strip()
            return m.group(1).strip(), name, "verbatim"
        return None, None, "no_source"

    if platform_key == "ruby":
        m = re.search(r'```[a-z]*\s*\n(gem install [A-Za-z0-9_\-]+)', text)
        if m:
            name = m.group(1).replace("gem install ", "").strip()
            return m.group(1).strip(), name, "verbatim"
        return None, None, "no_source"

    if platform_key == "nodejs":
        m = re.search(r'```[a-z]*\s*\n(npm install (@?[A-Za-z0-9_./\-]+))', text)
        if m:
            return m.group(1).strip(), m.group(2), "verbatim"
        return None, None, "no_source"

    if platform_key == "android":
        m = re.search(r"implementation '([^']+)'", text)
        if m:
            full = m.group(1)
            segments = full.split(":")
            artifact_id = segments[1] if len(segments) >= 2 else full
            return f"implementation '{full}'", ("android", artifact_id), "verbatim"
        return None, None, "no_source"

    if platform_key == "go":
        m = re.search(r'go get [^\s`<"]+', text)
        return (m.group(0).strip(), None, "verbatim") if m else (None, None, "no_source")

    if platform_key == "swift":
        m = re.search(r'swift package add [^\s`<"]+', text)
        if m:
            return m.group(0).strip(), None, "verbatim"
        m = re.search(r'\.package\(url:\s*"([^"]+)"', text)
        if m:
            return f'.package(url: "{m.group(1)}")', None, "verbatim"
        return None, None, "no_source"

    return None, None, "no_source"
