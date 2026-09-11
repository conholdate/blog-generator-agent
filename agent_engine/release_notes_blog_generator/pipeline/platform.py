from __future__ import annotations

import re
from urllib.parse import urlparse

from .. import brands
from ..models.platform import PlatformContext

# Language identity (name/tag/package-manager) is not carried in the configs/
# YAML, so it stays a small in-code table keyed by the URL's platform segment.
# Only platforms we have verified naming conventions for get an install command;
# anything else gets None so the writer links to docs instead of guessing.
_KNOWN_PLATFORMS: dict[str, dict[str, str]] = {
    "net": {"platform_name": ".NET", "language": "C#", "language_tag": "csharp", "package_manager": "NuGet"},
    "python": {"platform_name": "Python", "language": "Python", "language_tag": "python", "package_manager": "pip"},
    "java": {"platform_name": "Java", "language": "Java", "language_tag": "java", "package_manager": "Maven"},
    "cpp": {"platform_name": "C++", "language": "C++", "language_tag": "cpp", "package_manager": "NuGet"},
}


def _classify(platform_key: str) -> str | None:
    if platform_key in ("net", "dotnet"):
        return "net"
    if "python" in platform_key:
        return "python"
    if platform_key == "java":
        return "java"
    if "cpp" in platform_key or platform_key == "c++":
        return "cpp"
    return None


def detect_platform(
    source_url: str,
    release_title: str,
    configs_dir: str = brands.DEFAULT_CONFIGS_DIR,
) -> PlatformContext | None:
    """Derives the target platform/language and every brand cross-link for the
    blog post from the release-notes/docs URL: /<product>/<platform>/... on the
    brand's own host (releases.aspose.com, releases.groupdocs.com, ...).

    The brand is resolved from the URL host against configs/<brand>.yaml; the
    per-product configs/<brand>/<product>.yaml supplies money_pages / docs_pages
    when present, and the rest of the URLs are derived by convention from the
    brand's `website`. Returns None when the host matches no configured brand or
    the URL lacks the /<product>/<platform>/ shape, so callers fall back to the
    language already present in the extracted code sample.
    """
    brand = brands.resolve_brand_for_url(source_url, configs_dir)
    if brand is None:
        return None

    parts = [segment for segment in urlparse(source_url).path.split("/") if segment]
    if len(parts) < 2:
        return None

    product_key, platform_key = parts[0].lower(), parts[1].lower()
    classified = _classify(platform_key)
    known = _KNOWN_PLATFORMS.get(classified or "")

    product_pattern = re.compile(rf"{re.escape(brand.display_name)}\.(\S+?)\s+for\s+", re.IGNORECASE)
    product_match = product_pattern.search(release_title)
    product_display = product_match.group(1) if product_match else product_key.upper()

    product_cfg = brands.load_product(configs_dir, brand.key, product_key)
    money_pages = product_cfg.get("money_pages") if isinstance(product_cfg.get("money_pages"), dict) else None
    docs_pages = product_cfg.get("docs_pages") if isinstance(product_cfg.get("docs_pages"), dict) else None

    platform_name = known["platform_name"] if known else platform_key.upper()
    language = known["language"] if known else ""
    language_tag = known["language_tag"] if known else platform_key
    package_manager = known["package_manager"] if known else None

    return PlatformContext(
        platform_key=platform_key,
        platform_name=platform_name,
        language=language,
        language_tag=language_tag,
        package_manager=package_manager,
        install_command=brand.install_command(classified, product_key, product_display),
        product_key=product_key,
        product_display=product_display,
        brand_key=brand.key,
        brand_name=brand.display_name,
        product_full_name=brand.product_full_name(product_display),
        product_page_url=brand.product_page_url(product_key, platform_key, money_pages),
        docs_url=brand.docs_url(product_key, platform_key, docs_pages),
        api_reference_url=brand.api_reference_url(product_key, platform_key),
        free_apps_url=brand.free_apps_url(product_key),
        license_url=brand.license_url,
        forum_url=brand.forum_url(product_key),
        blog_domain=brand.blog_domain,
        blog_category_url=brand.blog_category_url(product_key),
    )


def fallback_platform(language: str) -> PlatformContext:
    """Used when the source URL doesn't match a configured brand's layout.
    Carries only the language actually seen in the extracted code sample —
    every URL field is left blank so the writer omits those links/sections
    instead of inventing them (see writer_agent.md).
    """
    normalized = language.lower().replace("c#", "csharp").replace("c++", "cpp").replace(".net", "dotnet")
    tag = re.sub(r"[^a-z0-9]+", "", normalized) or "code"
    return PlatformContext(
        platform_key="unknown",
        platform_name=language,
        language=language,
        language_tag=tag,
        product_key="",
        product_display="",
    )
