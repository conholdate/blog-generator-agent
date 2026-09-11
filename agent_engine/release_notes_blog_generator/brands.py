"""Brand configuration: turns the per-brand / per-product YAML under ``configs/``
into the handful of strings the pipeline needs (cross-link URL templates, blog
domain, package-name conventions, prompt labels, metrics identity).

The ``configs/`` tree was authored for a separate content-audit tool, so it
carries fields this pipeline ignores and lacks a few it needs. The rule
(agreed with the repo owner): use the values that are present, derive the rest
by convention from ``website`` / ``key``, and auto-detect the brand from the
source URL host.

Only ``configs/<brand>.yaml`` (brand level) and ``configs/<brand>/<product>.yaml``
(product level, optional) are read here.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

# configs/ lives at the repo root, a sibling of agent_engine/ — three parents up
# from this file (release_notes_blog_generator/ -> agent_engine/ -> repo root).
DEFAULT_CONFIGS_DIR = str(Path(__file__).resolve().parents[2] / "configs")


class BrandProfile:
    """Everything the pipeline needs to know about one brand (Aspose, GroupDocs,
    Conholdate, ...). URL builders take the product/platform keys parsed from the
    source URL and an optional per-platform override map from the product YAML.
    """

    __slots__ = ("key", "display_name", "website", "_app_base")

    def __init__(self, key: str, display_name: str, website: str) -> None:
        self.key = key
        self.display_name = display_name
        self.website = website.strip().lower().lstrip(".")
        # products.aspose.app / products.groupdocs.app — the app host drops the
        # brand's real TLD for ".app". Derived from the first label of website.
        self._app_base = self.website.split(".")[0] if self.website else self.key

    # -- brand-level, product-independent ------------------------------------
    @property
    def blog_domain(self) -> str:
        return f"https://blog.{self.website}" if self.website else ""

    @property
    def license_url(self) -> str:
        return f"https://purchase.{self.website}/temporary-license/" if self.website else ""

    # -- product / platform scoped -----------------------------------------
    def product_full_name(self, product_display: str) -> str:
        """``Aspose.PDF`` / ``GroupDocs.Conversion``."""
        if not product_display:
            return ""
        return f"{self.display_name}.{product_display}"

    def blog_category_url(self, product_key: str) -> str:
        if not (self.blog_domain and product_key):
            return ""
        return f"{self.blog_domain}/categories/{self.key}.{product_key}-product-family/"

    def product_page_url(self, product_key: str, platform_key: str, overrides: dict | None = None) -> str:
        found = _lookup_platform_url(overrides, platform_key)
        if found:
            return found
        if not (self.website and product_key):
            return ""
        return f"https://products.{self.website}/{product_key}/{platform_key}/"

    def docs_url(self, product_key: str, platform_key: str, overrides: dict | None = None) -> str:
        found = _lookup_platform_url(overrides, platform_key)
        if found:
            return found
        if not (self.website and product_key):
            return ""
        return f"https://docs.{self.website}/{product_key}/{platform_key}/"

    def api_reference_url(self, product_key: str, platform_key: str) -> str:
        if not (self.website and product_key):
            return ""
        return f"https://reference.{self.website}/{product_key}/{platform_key}/"

    def free_apps_url(self, product_key: str) -> str:
        if not (self._app_base and product_key):
            return ""
        return f"https://products.{self._app_base}.app/{product_key}/family"

    def forum_url(self, product_key: str) -> str:
        if not (self.website and product_key):
            return ""
        return f"https://forum.{self.website}/c/{product_key}/"

    def install_command(self, classified_platform: str | None, product_key: str, product_display: str) -> str | None:
        """Brand-templated version of the old hard-coded Aspose commands."""
        base = self._app_base or self.key
        if classified_platform == "net":
            return f"Install-Package {self.display_name}.{product_display}"
        if classified_platform == "python":
            return f"pip install {base}-{product_key}"
        if classified_platform == "java":
            return (
                f"<dependency>\n  <groupId>com.{base}</groupId>\n"
                f"  <artifactId>{base}-{product_key}</artifactId>\n</dependency>"
            )
        if classified_platform == "cpp":
            return f"Install-Package {self.display_name}.{product_display}.Cpp"
        return None


def _lookup_platform_url(mapping: dict | None, platform_key: str) -> str | None:
    """Match a URL-derived platform segment (``net``, ``python-net``) against a
    ``money_pages`` / ``docs_pages`` map whose keys vary across the config files
    (``python`` vs ``python_net`` vs ``python-net``). Normalises both sides."""
    if not mapping:
        return None
    want = _normalize_key(platform_key)
    for raw_key, value in mapping.items():
        if _normalize_key(str(raw_key)) == want and isinstance(value, str) and value:
            return value
    return None


def _normalize_key(key: str) -> str:
    return re.sub(r"[-_\s]", "", key.strip().lower())


@lru_cache(maxsize=None)
def _brand_index(configs_dir: str) -> tuple[tuple[str, str], ...]:
    """``((website, brand_key), ...)`` for every ``configs/<brand>.yaml``,
    longest website first so the most specific host match wins."""
    index: list[tuple[str, str]] = []
    root = Path(configs_dir)
    if not root.is_dir():
        return ()
    for path in sorted(root.glob("*.yaml")):
        data = _read_yaml(path)
        key = str(data.get("key") or path.stem)
        website = str(data.get("website") or "").strip().lower().lstrip(".")
        if website:
            index.append((website, key))
    index.sort(key=lambda pair: len(pair[0]), reverse=True)
    return tuple(index)


@lru_cache(maxsize=None)
def load_brand(configs_dir: str, key: str) -> BrandProfile | None:
    path = Path(configs_dir) / f"{key}.yaml"
    if not path.is_file():
        return None
    data = _read_yaml(path)
    return BrandProfile(
        key=str(data.get("key") or key),
        display_name=str(data.get("display_name") or key.replace("_", " ").title()),
        website=str(data.get("website") or ""),
    )


@lru_cache(maxsize=None)
def load_product(configs_dir: str, brand_key: str, product_key: str) -> dict:
    """Per-product YAML (``money_pages`` / ``docs_pages`` / ``display_name`` /
    ``platform_definitions``). Returns ``{}`` when there is no file — the caller
    then falls back to the derived URL templates."""
    path = Path(configs_dir) / brand_key / f"{product_key}.yaml"
    if not path.is_file():
        return {}
    return _read_yaml(path)


def resolve_brand_for_url(url: str, configs_dir: str = DEFAULT_CONFIGS_DIR) -> BrandProfile | None:
    """Pick the brand whose ``website`` the URL host matches (exact or subdomain).
    Returns ``None`` for an unrecognised host so callers fall back exactly as
    they did before brand support existed."""
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return None
    for website, key in _brand_index(configs_dir):
        if host == website or host.endswith(f".{website}"):
            return load_brand(configs_dir, key)
    return None


def allowed_domains_for_url(url: str, configs_dir: str = DEFAULT_CONFIGS_DIR) -> list[str]:
    """``[releases.<website>, docs.<website>]`` for the brand whose config
    matches this URL's host, else ``[]``. The fetcher unions this into its
    allowlist so a URL on a configured brand's own release/docs host is always
    fetchable — matching a brand config *is* the authorization — regardless of
    a narrower ``ALLOWED_DOMAINS`` override."""
    brand = resolve_brand_for_url(url, configs_dir)
    if brand is None or not brand.website:
        return []
    return [f"releases.{brand.website}", f"docs.{brand.website}"]


def default_allowed_domains(configs_dir: str = DEFAULT_CONFIGS_DIR) -> list[str]:
    """``releases.<website>`` + ``docs.<website>`` for every brand config —
    the fetcher allowlist default, so any brand under ``configs/`` works
    without an explicit ``ALLOWED_DOMAINS`` override."""
    domains: list[str] = []
    for website, _key in _brand_index(configs_dir):
        domains.append(f"releases.{website}")
        domains.append(f"docs.{website}")
    return domains or ["releases.aspose.com", "docs.aspose.com"]


def _read_yaml(path: Path) -> dict:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return loaded if isinstance(loaded, dict) else {}
