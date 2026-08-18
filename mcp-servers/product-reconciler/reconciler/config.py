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
    # Path under the products repo where product folders actually live.
    # aspose.cloud keeps them at content/{product}/ directly; groupdocs.cloud
    # nests everything one level deeper at content/english/{product}/ —
    # confirmed live, not a guess (products.groupdocs.cloud's content/ has
    # exactly one entry, "english").
    content_root: str = "content"
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
    # FreeAppsURL's path suffix — brands genuinely differ here, confirmed
    # live: aspose.app canonicalizes to a trailing slash ("family/"),
    # groupdocs.app does not ("family", no slash — adding one just adds an
    # unnecessary http->https + slash-drop redirect hop).
    apps_family_suffix: str = "family/"
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

    # How ProductName/Category get built from a brand module's pf_name.
    # Defaults reproduce the two cloud brands' exact current output
    # ("{pf_name} Cloud SDK for {language}" / "{pf_name} Cloud Product
    # Family") — aspose.com overrides both, since its pf_name (confirmed
    # live via releases.aspose.com's `linktitle` front-matter field, e.g.
    # "Aspose.Cells") already reads as a real product family name with no
    # "Cloud" branding involved.
    product_name_template: str = "{pf_name} Cloud SDK for {language}"
    category_template: str = "{pf_name} Cloud Product Family"
    # Same reasoning as apps_family_suffix but for the whole FreeAppsURL
    # shape: aspose.com's confirmed live value (products.aspose.app/cells)
    # has no platform segment or suffix at all, unlike either cloud brand.
    apps_url_template: str = "https://{apps_domain}/{url_prefix}/{apps_family_suffix}"
    # Both cloud brands' docs/reference sites are organized per product
    # family, not per platform ("docs.aspose.cloud/barcode/", confirmed
    # against real stored entries). aspose.com's real entries are
    # per-platform instead ("docs.aspose.com/cells/net/") — caught by
    # diffing a derived aspose.com sample against its real JSON entry
    # before this shipped.
    docs_url_template: str = "https://{docs_domain}/{url_prefix}/"
    api_reference_url_template: str = "https://{reference_domain}/{url_prefix}/"
    # Empty means this brand has no such field (aspose.cloud/groupdocs.cloud
    # don't). aspose.com's pricing URL is a plain brand-wide pattern,
    # confirmed against the live aspose.com.json data.
    pricing_url_template: str = ""


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

GROUPDOCS_CLOUD = BrandConfig(
    name="groupdocs.cloud",
    products_repo="groupdocs-cloud/products.groupdocs.cloud",
    releases_repo="groupdocs-cloud/releases.groupdocs.cloud",
    products_data_path=os.path.join(_MODULE_DIR, "../../../content/productsData/groupdocs.cloud.json"),
    content_root="content/english",
    platform_info={
        "net":     {"language": ".NET",    "verb": "dotnet add package"},
        "java":    {"language": "Java",    "verb": None},  # handled via data/repository/*.json
        "python":  {"language": "Python",  "verb": "pip install"},
        "php":     {"language": "PHP",     "verb": "composer require"},
        "ruby":    {"language": "Ruby",    "verb": "gem install"},
        "nodejs":  {"language": "Node.js", "verb": "npm install"},
        "android": {"language": "Android", "verb": None},  # gradle implementation line
        "go":      {"language": "Go",      "verb": "go get"},
        "swift":   {"language": "Swift",   "verb": "swift package add"},
        "cpp":     {"language": "C++",     "verb": None},  # no package manager; fallback text
        "apex":    {"language": "Apex",    "verb": None},  # no package manager; fallback text
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
        "android": ["android"],
        "go": ["go"],
        "swift": ["swift"],
        "cpp": ["cpp", "c++"],
        "apex": ["apex"],
    },
    brand_license_url="https://purchase.groupdocs.cloud/temporary-license/",
    products_domain="products.groupdocs.cloud",
    releases_domain="releases.groupdocs.cloud",
    docs_domain="docs.groupdocs.cloud",
    reference_domain="reference.groupdocs.cloud",
    apps_domain="products.groupdocs.app",
    blog_domain="blog.groupdocs.cloud",
    forum_domain="forum.groupdocs.cloud",
    java_group_path="com/groupdocs",
    apps_family_suffix="family",
)

ASPOSE_COM = BrandConfig(
    name="aspose.com",
    # Single repo serves both roles here — confirmed live: releases.aspose.com's
    # own product pages (content/en/{product}/{platform}/_index.md) already carry
    # the product name (`linktitle`), the install-command source
    # (`homepage_package_type`/`homepage_package_link`), and a GitHub examples
    # link in the body. Unlike the two cloud brands, there is no separate
    # products.aspose.com content repo to fall back to.
    products_repo="Aspose/releases.aspose.com",
    releases_repo="Aspose/releases.aspose.com",
    products_data_path=os.path.join(_MODULE_DIR, "../../../content/productsData/aspose.com.json"),
    content_root="content/en",
    # Deliberately conservative first cut: only platform folder names actually
    # confirmed live (via cells/net, cells/java, cells/php, cells/nodejs,
    # cells/cpp, words/python). aspose.com ships many more platform-folder
    # spellings (python-net, python-java, nodejs-cpp, nodejs-net, javascript-cpp,
    # go-cpp, androidjava, jasperreports, reportingservices, sharepoint, ...) —
    # real per-product bridge variants, not naming drift — but none of those
    # were inspected, so per discover_inventory's allowlist design they're
    # silently skipped rather than guessed at. Add each once its page markup
    # and homepage_package_type are confirmed.
    #
    # "language" here is the platform's display suffix as aspose.com's own
    # `linktitle` writes it (feeds ProductName, e.g. "... for .NET"); the
    # ProgrammingLanguage column value is separate and often differs (C# for
    # .NET) — see prog_language.
    platform_info={
        "net":    {"language": ".NET", "prog_language": "C#", "verb": "dotnet add package"},
        "java":   {"language": "Java", "verb": "maven"},  # groupId/artifactId derived from homepage_package_link
        "php":    {"language": "PHP", "verb": "composer require"},
        "nodejs": {"language": "Node.js", "prog_language": "JavaScript", "verb": "npm install"},
        "python": {"language": "Python", "verb": "pip install"},
        # Confirmed live (cells/cpp): distributed via NuGet like .NET, not a
        # no-package-manager fallback the way it is for aspose.cloud/groupdocs.cloud.
        "cpp":    {"language": "C++", "verb": "dotnet add package"},
    },
    # No plausibility check for now — aspose.com bridge products legitimately
    # link to a *different* platform's GitHub repo (e.g. cells/nodejs's
    # Examples link points at the Java repo, since it's Node.js-via-Java).
    # Guessing tokens here risks rejecting genuinely-correct links.
    platform_repo_tokens={},
    brand_license_url="https://purchase.aspose.com/temporary-license/",
    products_domain="products.aspose.com",
    releases_domain="releases.aspose.com",
    docs_domain="docs.aspose.com",
    reference_domain="reference.aspose.com",
    apps_domain="products.aspose.app",
    blog_domain="blog.aspose.com",
    forum_domain="forum.aspose.com",
    java_group_path="com/aspose",
    product_name_template="{pf_name} for {language}",
    category_template="{pf_name} Product Family",
    apps_url_template="https://{apps_domain}/{url_prefix}",
    docs_url_template="https://{docs_domain}/{url_prefix}/{platform_key}/",
    api_reference_url_template="https://{reference_domain}/{url_prefix}/{platform_key}/",
    pricing_url_template="https://purchase.aspose.com/pricing/{url_prefix}/family/",
    field_order=(
        "ProductName", "Category", "ProgrammingLanguage", "ProductURL", "DownloadURL",
        "ExternalDownloadURL", "DocumentationURL", "BlogsURL", "APIReferenceURL",
        "FreeAppsURL", "ForumsURL", "InstallCommand", "urlPrefix", "license", "pricing",
    ),
)

BRANDS: dict[str, BrandConfig] = {
    "aspose.cloud": ASPOSE_CLOUD,
    "groupdocs.cloud": GROUPDOCS_CLOUD,
    "aspose.com": ASPOSE_COM,
}


def get_brand_config(brand: str) -> BrandConfig:
    if brand not in BRANDS:
        available = ", ".join(sorted(BRANDS))
        raise ValueError(f"Unsupported brand {brand!r}. Configured brands: {available}")
    return BRANDS[brand]
