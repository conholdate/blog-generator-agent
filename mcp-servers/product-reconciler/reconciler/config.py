"""
Static configuration for the aspose.cloud product reconciler:
repo locations, the JSON file it maintains, and the lookup tables that
encode platform-naming and verb quirks discovered while auditing this
brand's data by hand.
"""
import os

PRODUCTS_REPO = "aspose-cloud/products.aspose.cloud"
RELEASES_REPO = "aspose-cloud/releases.aspose.cloud"

PRODUCTS_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../../../content/productsData/aspose.cloud.json"
)

# Folders under products.aspose.cloud/content/{product}/ that are not
# platform SDKs and must never be treated as a new platform.
NON_PLATFORM_FOLDERS = {"family", "embed", "release-notes"}

# platform folder name -> (ProgrammingLanguage display name, package-manager verb)
# Verb is used to pick the right consolebox/install-script block when a
# release page offers more than one package manager for the same platform.
PLATFORM_INFO = {
    "net":     {"language": ".NET",       "verb": "dotnet add package"},
    "java":    {"language": "Java",       "verb": None},  # handled via data/repository/*.json
    "python":  {"language": "Python",     "verb": "pip install"},
    "php":     {"language": "PHP",        "verb": "composer require"},
    "ruby":    {"language": "Ruby",       "verb": "gem install"},
    "nodejs":  {"language": "Node.js",    "verb": "npm install"},
    "go":      {"language": "Go",         "verb": "go get"},
    "swift":   {"language": "Swift",      "verb": "swift package add"},
    "cpp":     {"language": "C++",        "verb": None},  # no package manager; fallback text
    "dart":    {"language": "Dart",       "verb": "pub add"},
    "android": {"language": "Android",    "verb": None},  # gradle implementation line
    "curl":    {"language": "cURL",       "verb": None},
    "aws":     {"language": "AWS",        "verb": "docker pull"},
    "perl":    {"language": "Perl",       "verb": "cpan install"},
}

# Some products.aspose.cloud folders use a different spelling than the
# releases.aspose.cloud folder for the same platform (discovered while
# auditing InstallCommand: cross-check both before declaring "no source").
PLATFORM_ALIASES = {
    "nodejs": ["nodejs", "node"],
}

CPP_FALLBACK_COMMAND = "See GitHub for build instructions"

# Tokens expected to appear in a platform's GitHub repo name/URL. Used as a
# plausibility check on ExternalDownloadURL: source pages have been found
# to contain copy-paste errors (e.g. barcode/python's own page linking to
# the PHP repo) — a value from the "real" source is still wrong if it
# doesn't even mention the right platform.
PLATFORM_REPO_TOKENS = {
    "net": ["net", "dotnet"],
    "java": ["java"],
    "python": ["python", "py"],
    "php": ["php"],
    "ruby": ["ruby"],
    "nodejs": ["node", "nodejs", "js"],
    "go": ["go"],
    "swift": ["swift"],
    "cpp": ["cpp", "c++"],
    "dart": ["dart"],
    "android": ["android"],
    "curl": ["curl"],
    "aws": ["aws"],
    "perl": ["perl"],
}

# license is a brand-wide constant, confirmed identical across all 113
# existing aspose.cloud entries.
BRAND_LICENSE_URL = "https://purchase.aspose.com/temporary-license/"
