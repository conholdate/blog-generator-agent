from __future__ import annotations

import re
from urllib.parse import urlparse

from ..models.platform import PlatformContext

# Confirmed from releases.aspose.com/pdf/net/... and the sample post's
# products.aspose.com/pdf/python-net/, docs.aspose.com/pdf/python-net/ links.
# Only platforms we have verified naming conventions for get an install
# command; anything else gets None so the writer links to docs instead of
# guessing a package name.
_KNOWN_PLATFORMS: dict[str, dict[str, str]] = {
    "net": {"platform_name": ".NET", "language": "C#", "language_tag": "csharp", "package_manager": "NuGet"},
    "python": {"platform_name": "Python", "language": "Python", "language_tag": "python", "package_manager": "pip"},
    "java": {"platform_name": "Java", "language": "Java", "language_tag": "java", "package_manager": "Maven"},
    "cpp": {"platform_name": "C++", "language": "C++", "language_tag": "cpp", "package_manager": "NuGet"},
}

_PRODUCT_NAME_PATTERN = re.compile(r"Aspose\.(\S+?)\s+for\s+", re.IGNORECASE)


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


def detect_platform(source_url: str, release_title: str) -> PlatformContext | None:
    """Derives the target platform/language for the blog post from the
    releases.aspose.com URL structure: /<product>/<platform>/release-notes/...

    This is the mechanism behind the rule ".NET release notes -> C# .NET
    post, Python release notes -> Python post": the platform segment of the
    URL is authoritative, not a guess from the code sample's language.
    Returns None if the URL doesn't look like a releases.aspose.com release
    notes page, so callers can fall back to the language already present in
    the extracted code sample instead.
    """
    parts = [segment for segment in urlparse(source_url).path.split("/") if segment]
    if len(parts) < 2:
        return None

    product_key, platform_key = parts[0].lower(), parts[1].lower()
    known = _KNOWN_PLATFORMS.get(_classify(platform_key) or "")

    product_match = _PRODUCT_NAME_PATTERN.search(release_title)
    product_display = product_match.group(1) if product_match else product_key.upper()

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
        install_command=_build_install_command(platform_key, product_key, product_display),
        product_key=product_key,
        product_display=product_display,
        product_page_url=f"https://products.aspose.com/{product_key}/{platform_key}/",
        docs_url=f"https://docs.aspose.com/{product_key}/{platform_key}/",
        api_reference_url=f"https://reference.aspose.com/{product_key}/{platform_key}/",
        free_apps_url=f"https://products.aspose.app/{product_key}/family",
        forum_url=f"https://forum.aspose.com/c/{product_key}/",
    )


def fallback_platform(language: str) -> PlatformContext:
    """Used when the source URL doesn't match releases.aspose.com's layout.
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


def _build_install_command(platform_key: str, product_key: str, product_display: str) -> str | None:
    classified = _classify(platform_key)
    if classified == "net":
        return f"Install-Package Aspose.{product_display}"
    if classified == "python":
        return f"pip install aspose-{product_key}"
    if classified == "java":
        return f"<dependency>\n  <groupId>com.aspose</groupId>\n  <artifactId>aspose-{product_key}</artifactId>\n</dependency>"
    if classified == "cpp":
        return f"Install-Package Aspose.{product_display}.Cpp"
    return None
