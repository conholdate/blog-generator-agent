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
    # (url_prefix, platform_key) -> the slug products.aspose.com/docs.aspose.com/
    # reference.aspose.com actually serve this platform under, when it
    # differs from the releases-repo folder name (platform_key) that
    # DownloadURL correctly uses as-is. Confirmed live: needed only for
    # pdf's 4 concatenated-spelling folders (pythoncpp/pythonjava/
    # javascriptcpp/nodejscpp/rustcpp all 404 on those three domains;
    # their hyphenated siblings 200) and ocr/java-gpu (which has no
    # standalone product/docs page at all — it shares ocr/java's).
    # Empty for every other brand/platform, where platform_key already
    # serves both roles.
    url_slug_overrides: dict = field(default_factory=dict)
    # (url_prefix, platform_key) -> Category text base, for the rare case
    # where splitting pf_name on " for " doesn't yield the real family
    # name. Confirmed live: ocr/java-gpu's linktitle is "Aspose.OCR-GPU
    # for Java" — the generic split reads "Aspose.OCR-GPU" as the family,
    # but every sibling OCR entry (and the family's own blog category)
    # uses plain "Aspose.OCR".
    category_base_overrides: dict = field(default_factory=dict)
    # (url_prefix, slug as it appears in a stored ProductURL) -> the real
    # platform_key (releases-repo folder name) that slug corresponds to.
    # The inverse of url_slug_overrides, and deliberately NOT auto-derived
    # from it: diff.py's pairs_from_json parses stored ProductURLs to
    # match them against live-discovered (url_prefix, platform_key) pairs,
    # and for pdf's 4 concatenated-spelling platforms the stored JSON
    # already has real rows under the hyphenated public slug (confirmed
    # live) — without this, those rows would never match their live
    # counterpart and running for real would append duplicates instead of
    # updating them. ocr/java-gpu is deliberately NOT here: it has no
    # existing row to match (confirmed), and its override target ("java")
    # is itself a real, independent platform_key for ocr — reversing it
    # here would incorrectly steal the genuine ocr/java entry's pairing.
    json_slug_aliases: dict = field(default_factory=dict)
    # (url_prefix, platform_key) -> slug, applied to ProductURL ONLY —
    # unlike url_slug_overrides (which applies the same slug to
    # ProductURL/DocumentationURL/APIReferenceURL uniformly). Confirmed
    # live this split is real, not an oversight: every "reportingservices"
    # platform's ProductURL only resolves under the hyphenated
    # "reporting-services" slug, but its DocumentationURL only resolves
    # under the plain concatenated platform_key — the two domains
    # genuinely disagree for this platform type, so one shared override
    # would break whichever field didn't match.
    product_url_slug_overrides: dict = field(default_factory=dict)


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
        # --- Phase 1: language-bridge variants, scoped to folder names
        # confirmed spelled identically across every product that has them
        # (surveyed live across all 29 top-level products). "pdf" spells
        # five of these differently (javascriptcpp, nodejscpp, pythoncpp,
        # pythonjava, rustcpp) and go-cpp/rust-cpp don't carry
        # homepage_package_type at all (install command lives only in body
        # text) — both deliberately left out, to be handled separately.
        # "language"/"prog_language" come from tabulating real
        # ProgrammingLanguage values already in
        # content/productsData/aspose.com.json per folder name, not
        # guessed. homepage_package_type on every key below was spot-checked
        # live and uses the same NuGet/Maven/Composer/NPM/Pip dispatch as
        # the core six — no new install-command logic needed.
        "python-net":  {"language": "Python via .NET", "prog_language": "Python", "verb": "pip install"},
        "python-java": {"language": "Python via Java", "prog_language": "Python", "verb": "pip install"},
        "python-cpp":  {"language": "Python via C++", "prog_language": "Python", "verb": "pip install"},
        "pythonnet":   {"language": "Python via .NET", "prog_language": "Python", "verb": "pip install"},  # email-only spelling
        "nodejs-java": {"language": "Node.js via Java", "prog_language": "JavaScript", "verb": "npm install"},
        "nodejs-cpp":  {"language": "Node.js via C++", "prog_language": "JavaScript", "verb": "npm install"},
        "nodejs-net":  {"language": "Node.js via .NET", "prog_language": "JavaScript", "verb": "npm install"},
        "javascript-cpp": {"language": "JavaScript via C++", "prog_language": "JavaScript", "verb": "npm install"},
        "javascript-net": {"language": "JavaScript via .NET", "prog_language": "JavaScript", "verb": "npm install"},
        "php-java":    {"language": "PHP via Java", "prog_language": "PHP", "verb": "composer require"},
        # Confirmed live: folder is always "androidjava" (no hyphen) —
        # products.aspose.com's hyphenated "android-java" is a redirect
        # alias, not a real releases-repo folder, so it's not a key here.
        "androidjava": {"language": "Android via Java", "prog_language": "Java", "verb": "maven"},
        # --- remaining 9: 3 pdf-only concatenated spellings sharing the
        # same front-matter mechanism as their hyphenated siblings above
        # (javascriptcpp/nodejscpp/pythonjava — confirmed live), one
        # standalone GPU variant (java-gpu, Maven+dataFolder same as any
        # Java entry), and 3 platforms with no homepage_package_type at
        # all (go-cpp x3, pythoncpp) handled by the body-scrape fallback
        # in brands/aspose_com.py — see scrape_install_command there.
        # rustcpp is included for URL/name/category derivation even
        # though it has no derivable InstallCommand on its own page
        # (confirmed: no front matter, no body command either) — stays
        # blank rather than guessed, same as any other missing source.
        "javascriptcpp": {"language": "JavaScript via C++", "prog_language": "JavaScript", "verb": "npm install"},
        "nodejscpp":     {"language": "Node.js via C++", "prog_language": "JavaScript", "verb": "npm install"},
        "pythonjava":    {"language": "Python via Java", "prog_language": "Python", "verb": "pip install"},
        "pythoncpp":     {"language": "Python via C++", "prog_language": "Python", "verb": "pip install"},
        "go-cpp":        {"language": "Go via C++", "prog_language": "Go", "verb": "go install"},
        "rustcpp":       {"language": "Rust via C++", "prog_language": "Rust", "verb": None},
        # Category derives to "Aspose.OCR-GPU Product Family" (splitting
        # linktitle "Aspose.OCR-GPU for Java" on " for "), not "Aspose.OCR
        # Product Family" like its sibling entries — Aspose's own page
        # bakes "-GPU" into the family name with no space, so the generic
        # split can't distinguish it from a real family name. Flagged, not
        # special-cased for one entry.
        "java-gpu":      {"language": "Java (GPU)", "prog_language": "Java", "verb": "maven"},
        # --- Phase 2: plugin/extension-style integration platforms.
        # Genuinely different product shape, confirmed live across
        # barcode/cad/cells/imaging/pdf/slides/total/words: none of these
        # pages carry homepage_package_type front matter OR any install
        # command in the body (no consolebox, no pip/npm/go pattern) —
        # they're downloadable plugin binaries for a host application, not
        # a package-manager-installable library. InstallCommand correctly
        # stays blank for all of them via the existing no-match fallthrough
        # — no new scraping code needed. Same for ExternalDownloadURL: none
        # of these pages have an "Examples"/"Code Samples" link either.
        "jasperreports":     {"language": "JasperReports", "prog_language": "JasperReports", "verb": None},
        "jasperreport":      {"language": "JasperReports", "prog_language": "JasperReports", "verb": None},  # slides-only spelling, confirmed live
        "reportingservices": {"language": "Reporting Services", "prog_language": "Reporting Services", "verb": None},
        "sharepoint":        {"language": "SharePoint", "prog_language": "SharePoint", "verb": None},
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
    # pf_name is already the full display name (fetch_product_info returns
    # linktitle/family_listing_page_title verbatim, unsplit, so bridge
    # suffixes like "for Python via .NET" stay intact) — identity template,
    # not "{pf_name} for {language}" like the cloud brands use.
    product_name_template="{pf_name}",
    category_template="{pf_name} Product Family",
    apps_url_template="https://{apps_domain}/{url_prefix}",
    docs_url_template="https://{docs_domain}/{url_prefix}/{platform_key}/",
    api_reference_url_template="https://{reference_domain}/{url_prefix}/{platform_key}/",
    pricing_url_template="https://purchase.aspose.com/pricing/{url_prefix}/family/",
    url_slug_overrides={
        ("pdf", "pythoncpp"):     "python-cpp",
        ("pdf", "pythonjava"):    "python-java",
        ("pdf", "javascriptcpp"): "javascript-cpp",
        ("pdf", "nodejscpp"):     "nodejs-cpp",
        ("pdf", "rustcpp"):       "rust-cpp",
        ("ocr", "java-gpu"):      "java",
        # slides' jasperreport(s): confirmed live that BOTH
        # products.aspose.com AND docs.aspose.com only resolve under the
        # plural "jasperreports", unlike reportingservices below where the
        # two domains disagree — so this belongs in the uniform override,
        # not product_url_slug_overrides.
        ("slides", "jasperreport"): "jasperreports",
    },
    category_base_overrides={
        ("ocr", "java-gpu"): "Aspose.OCR",
    },
    json_slug_aliases={
        ("pdf", "python-cpp"):     "pythoncpp",
        ("pdf", "python-java"):    "pythonjava",
        ("pdf", "javascript-cpp"): "javascriptcpp",
        ("pdf", "nodejs-cpp"):     "nodejscpp",
        ("pdf", "rust-cpp"):       "rustcpp",
        ("slides", "jasperreports"): "jasperreport",
        # reportingservices: every stored row's ProductURL uses the
        # hyphenated "reporting-services" slug (matching
        # product_url_slug_overrides below); without this reverse mapping
        # each of these 6 would look brand new and get duplicated on a
        # real run instead of matched and updated.
        ("barcode", "reporting-services"): "reportingservices",
        ("cells", "reporting-services"):   "reportingservices",
        ("pdf", "reporting-services"):     "reportingservices",
        ("slides", "reporting-services"):  "reportingservices",
        ("total", "reporting-services"):   "reportingservices",
        ("words", "reporting-services"):   "reportingservices",
    },
    product_url_slug_overrides={
        # Confirmed live: products.aspose.com/{family}/reportingservices/
        # (concatenated) 404s everywhere it was checked — only the
        # hyphenated slug resolves. docs.aspose.com and reference.aspose.com
        # disagree (they want the concatenated form, matching platform_key
        # directly, same as DownloadURL) — hence ProductURL-only, not
        # url_slug_overrides.
        ("barcode", "reportingservices"): "reporting-services",
        ("cells", "reportingservices"):   "reporting-services",
        ("pdf", "reportingservices"):     "reporting-services",
        ("slides", "reportingservices"):  "reporting-services",
        ("total", "reportingservices"):   "reporting-services",
        ("words", "reportingservices"):   "reporting-services",
    },
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
