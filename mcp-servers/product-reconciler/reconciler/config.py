"""
Brand configuration registry for the product reconciler.

Each brand's repo locations, JSON path, and platform lookup tables live
in its own BrandConfig entry. Only aspose.cloud is populated so far —
the extraction logic in fields.py (how install commands are scraped,
what a "platform page" even looks like) is still tied to aspose.cloud's
specific page templates, confirmed today to differ meaningfully between
brands (groupdocs.cloud and aspose.com each use different markup).
Adding a real second brand means both a BrandConfig entry here AND
brand-aware extraction logic in fields.py, not just a config entry.
"""
import os
from dataclasses import dataclass, field

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class BrandConfig:
    name: str
    products_repo: str
    releases_repo: str
    products_data_path: str
    # platform folder name -> {"language": display name, "verb": package-manager verb or None}
    # This doubles as an allowlist: discover_inventory() only treats a folder
    # as a platform if its (normalized) name is a key here. Anything else —
    # locale codes, feature/operation subpages, "curl" (real folder, not an
    # SDK) — is silently skipped.
    platform_info: dict = field(default_factory=dict)
    # alternate spellings for the same platform across the two repos
    # (discovered auditing InstallCommand: cross-check both before
    # declaring "no source")
    platform_aliases: dict = field(default_factory=dict)
    # tokens expected in a platform's GitHub repo URL — plausibility check
    # on ExternalDownloadURL, since source pages have been found to contain
    # copy-paste errors (barcode/python's own page linking to the PHP repo)
    platform_repo_tokens: dict = field(default_factory=dict)
    cpp_fallback_command: str = "See GitHub for build instructions"
    # license is a brand-wide constant for aspose.cloud (confirmed identical
    # across all 113 existing entries) — may not hold for every future brand
    brand_license_url: str = ""

    # Domains for each URL field. Not all brands follow "{sub}.{brand}" —
    # aspose.cloud's own FreeAppsURL lives on aspose.app, not aspose.cloud,
    # so these are explicit per-field rather than derived from the brand
    # name.
    products_domain: str = ""
    releases_domain: str = ""
    docs_domain: str = ""
    reference_domain: str = ""
    apps_domain: str = ""
    blog_domain: str = ""
    forum_domain: str = ""
    # Path segment for this brand's custom Maven repo (releases_domain/java/repo/{java_group_path}/{artifactId})
    java_group_path: str = ""
    # Key order for a freshly-written entry — schema varies slightly by
    # brand (aspose.com.json carries an extra "pricing" field aspose.cloud
    # doesn't have).
    field_order: tuple = (
        "ProductName", "Category", "ProgrammingLanguage", "ProductURL", "DownloadURL",
        "ExternalDownloadURL", "DocumentationURL", "BlogsURL", "APIReferenceURL",
        "FreeAppsURL", "ForumsURL", "InstallCommand", "urlPrefix", "license",
    )


ASPOSE_CLOUD = BrandConfig(
    name="aspose.cloud",
    products_repo="aspose-cloud/products.aspose.cloud",
    releases_repo="aspose-cloud/releases.aspose.cloud",
    products_data_path=os.path.join(_MODULE_DIR, "../../../content/productsData/aspose.cloud.json"),
    platform_info={
        "net":     {"language": ".NET",       "verb": "dotnet add package"},
        "java":    {"language": "Java",       "verb": None},  # handled via data/repository/*.json
        "python":  {"language": "Python",     "verb": "pip install"},
        "php":     {"language": "PHP",        "verb": "composer require"},
        "ruby":    {"language": "Ruby",       "verb": "gem install"},
        "nodejs":  {"language": "Node.js",    "verb": "npm install"},
        # Distinct from nodejs, not an alias of it — confirmed while investigating a
        # false "removal" flag: Imaging ships both a separate browser "SDK for
        # JavaScript" (content/{product}/javascript/) and a server-side "Cloud SDK
        # for Node.js" (content/{product}/nodejs/) as two different real products.
        "javascript": {"language": "JavaScript", "verb": "npm install"},
        "go":      {"language": "Go",         "verb": "go get"},
        "swift":   {"language": "Swift",      "verb": "swift package add"},
        "cpp":     {"language": "C++",        "verb": None},  # no package manager; fallback text
        "dart":    {"language": "Dart",       "verb": "pub add"},
        "android": {"language": "Android",    "verb": None},  # gradle implementation line
        "aws":     {"language": "AWS",        "verb": "docker pull"},
        "perl":    {"language": "Perl",       "verb": "cpan install"},
    },
    platform_aliases={
        "nodejs": ["nodejs", "node"],
    },
    platform_repo_tokens={
        "net": ["net", "dotnet"],
        "java": ["java"],
        "python": ["python", "py"],
        "php": ["php"],
        "ruby": ["ruby"],
        "nodejs": ["node", "nodejs", "js"],
        "javascript": ["javascript", "js"],
        "go": ["go"],
        "swift": ["swift"],
        "cpp": ["cpp", "c++"],
        "dart": ["dart"],
        "android": ["android"],
        "aws": ["aws"],
        "perl": ["perl"],
    },
    brand_license_url="https://purchase.aspose.com/temporary-license/",
    products_domain="products.aspose.cloud",
    releases_domain="releases.aspose.cloud",
    docs_domain="docs.aspose.cloud",
    reference_domain="reference.aspose.cloud",
    apps_domain="products.aspose.app",
    blog_domain="blog.aspose.cloud",
    forum_domain="forum.aspose.cloud",
    java_group_path="com/aspose",
)

BRANDS: dict[str, BrandConfig] = {
    "aspose.cloud": ASPOSE_CLOUD,
}


def get_brand_config(brand: str) -> BrandConfig:
    if brand not in BRANDS:
        available = ", ".join(sorted(BRANDS))
        raise ValueError(f"Unsupported brand {brand!r}. Configured brands: {available}")
    return BRANDS[brand]
