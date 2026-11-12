"""
Where each cloud brand's product capability data comes from (aspose.cloud,
and groupdocs.cloud since 2026-11-12 - same Swagger layout, different host) - public,
unauthenticated sources only (confirmed live 2026-11-03):

- 14 products: Swagger/OpenAPI spec, discovered at run time newest first
  from both the standard https://api.aspose.cloud/<version>/<product>/swagger/spec
  addresses and whatever the product's reference.aspose.cloud page loads
  (OCR/OMR only exist at v5.1 under different paths). An older spec can
  silently miss features (Email v3.0 had no conversions; OCR v3.0 had 6
  endpoints vs 27 in v5.1).
- Aspose.Words Cloud: its v3.0 spec is from 2017 (78 endpoints vs ~192
  operations today), so its official Python SDK source is used instead.
- Aspose.Total Cloud: a bundle of all the APIs, no spec of its own - handled
  as "all products combined" at check time, never fetched here.

Every fetch distinguishes "not found" from "failed": the builder only
replaces a product's existing file on a real result, never on a network
error, so one bad run can't wipe a product's capabilities.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import requests

# Per-brand hosts. Both brands publish specs at
# https://api.<host>/<version>/<product>/swagger/spec and a Swagger UI page at
# https://reference.<host>/<product>/. GroupDocs Cloud also needs v1.0: 7 of
# its 14 APIs only exist there (checked live 2026-11-12).
BRAND_SOURCES = {
    "aspose.cloud": {"host": "aspose.cloud", "versions": ("v4.0", "v3.0", "v2.0"), "sdk_products": {"words"}},
    "groupdocs.cloud": {"host": "groupdocs.cloud", "versions": ("v4.0", "v3.0", "v2.0", "v1.0"), "sdk_products": set()},
}
DEFAULT_BRAND = "aspose.cloud"
SPEC_URL = "https://api.{host}/{version}/{product}/swagger/spec"
WORDS_SDK_URL = (
    "https://raw.githubusercontent.com/aspose-words-cloud/aspose-words-cloud-python/"
    "master/asposewordscloud/apis/words_api.py"
)
TIMEOUT = 120  # Slides/PDF specs are ~1 MB and occasionally slow

BUNDLE_PRODUCTS = {"total"}  # Aspose.Total / GroupDocs.Total Cloud


@dataclass
class SourceResult:
    status: str  # "ok" | "not_found" | "error"
    kind: str = ""  # "spec" | "sdk"
    url: str = ""
    version: str = ""
    spec: dict | None = None
    sdk_source: str = ""
    error: str = ""
    reference_url: str = ""  # the product's reference.<host> page
    deep_link: bool = False  # True if #/<tag>/<operationId> links work for this spec
    reference_spec_name: str | None = None  # ?urls.primaryName= value on multi-spec pages


def _version_number(version: str) -> float:
    try:
        return float(version.lstrip("v"))
    except ValueError:
        return 0.0


def _get_with_retry(url: str) -> requests.Response | None:
    """One retry on network errors / 5xx - api.aspose.cloud intermittently
    answers 500/502 (confirmed 2026-11-03), including for versions that
    don't exist for a product (CAD v4.0 returned 500, then 404)."""
    resp = None
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
        except requests.RequestException:
            resp = None
        if resp is not None and resp.status_code < 500:
            return resp
        if attempt == 0:
            time.sleep(5)
    return resp


REFERENCE_URL = "https://reference.{host}/{product}/"
_REF_URLS_ENTRY_RE = re.compile(r'\{\s*url:\s*"([^"]+)"\s*,\s*name:\s*"([^"]+)"\s*\}')
_REF_SINGLE_URL_RE = re.compile(r'\burl:\s*"(https://api\.(?:aspose|groupdocs)\.cloud/[^"]+)"')
_REF_DEEPLINK_RE = re.compile(r"deepLinking:\s*true")
_URL_VERSION_RE = re.compile(r"/v(\d+(?:\.\d+)?)/")


@dataclass
class ReferencePage:
    url: str
    deep_linking: bool = False
    # Specs the page can show: [(spec url, selector name or None)]. A
    # multi-spec page (Cells, BarCode) needs ?urls.primaryName=<name> to
    # open the right one - the default isn't always the newest.
    specs: list = field(default_factory=list)


def parse_reference_page(html: str, page_url: str) -> ReferencePage:
    """Which specs reference.aspose.cloud/<product>/ (Swagger UI) loads, and
    whether it supports #/<tag>/<operationId> deep links. Confirmed in a
    real browser 2026-11-04 that both a plain deep link (Imaging) and one
    with ?urls.primaryName= (Cells v4) open the exact operation."""
    specs = [(u, n) for u, n in _REF_URLS_ENTRY_RE.findall(html)]
    if not specs:
        specs = [(u, None) for u in dict.fromkeys(_REF_SINGLE_URL_RE.findall(html))]
    return ReferencePage(url=page_url, deep_linking=bool(_REF_DEEPLINK_RE.search(html)), specs=specs)


def fetch_reference_page(product: str, brand: str = DEFAULT_BRAND) -> ReferencePage:
    url = REFERENCE_URL.format(host=BRAND_SOURCES[brand]["host"], product=product)
    resp = _get_with_retry(url)
    if resp is None or resp.status_code != 200:
        return ReferencePage(url=url)
    return parse_reference_page(resp.text, url)


def url_version(url: str) -> str:
    m = _URL_VERSION_RE.search(url)
    return f"v{m.group(1)}" if m else ""


def fetch_spec(product: str, prior_version: str = "", brand: str = DEFAULT_BRAND) -> SourceResult:
    """Newest available spec - from the standard addresses AND whatever the
    product's reference page loads (OCR/OMR only exist at v5.1 under a
    different path, found via their reference pages 2026-11-04). A version
    that keeps failing (5xx/network) is skipped, but an OLDER version than
    `prior_version` (what we built from last time) is never accepted - that
    would silently downgrade to a stale spec because the newer one had a bad
    day. The caller keeps its previous data instead."""
    src = BRAND_SOURCES[brand]
    ref = fetch_reference_page(product, brand)
    candidates = {SPEC_URL.format(host=src["host"], version=v, product=product): None for v in src["versions"]}
    for spec_url, name in ref.specs:
        candidates[spec_url] = name
    ordered = sorted(candidates, key=lambda u: _version_number(url_version(u)), reverse=True)

    last_error, unreachable = "", []
    for url in ordered:
        version = url_version(url)
        resp = _get_with_retry(url)
        if resp is None or resp.status_code >= 500:
            unreachable.append(f"{version}: {'network error' if resp is None else f'HTTP {resp.status_code}'}")
            continue
        if resp.status_code != 200:  # 3xx/4xx: this version doesn't exist for the product
            continue
        try:
            spec = resp.json()
        except ValueError:
            last_error = f"{version}: invalid JSON"
            continue
        if not isinstance(spec, dict) or not spec.get("paths"):
            last_error = f"{version}: spec has no paths"
            continue
        if prior_version and _version_number(version) < _version_number(prior_version):
            return SourceResult(status="error", url=url,
                                error=f"only {version} reachable, previously built from {prior_version} ({'; '.join(unreachable)})")
        note = f"newer unreachable: {'; '.join(unreachable)}" if unreachable else ""
        # Deep links only work when the reference page shows THIS spec.
        on_page = any(u == url for u, _ in ref.specs)
        return SourceResult(status="ok", kind="spec", url=url, version=version, spec=spec, error=note,
                            reference_url=ref.url, deep_link=ref.deep_linking and on_page,
                            reference_spec_name=next((n for u, n in ref.specs if u == url), None) if len(ref.specs) > 1 else None)
    if unreachable:
        return SourceResult(status="error", error="; ".join(unreachable))
    return SourceResult(status="not_found", error=last_error or "no spec at any known version")


def fetch_words_sdk() -> SourceResult:
    try:
        resp = requests.get(WORDS_SDK_URL, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return SourceResult(status="error", url=WORDS_SDK_URL, error=str(exc)[:200])
    if resp.status_code == 404:
        return SourceResult(status="not_found", url=WORDS_SDK_URL, error="HTTP 404")
    if resp.status_code != 200:
        return SourceResult(status="error", url=WORDS_SDK_URL, error=f"HTTP {resp.status_code}")
    # Words' reference page is a custom (non-Swagger) page - no per-operation
    # links, so proof links point at the product's reference page.
    return SourceResult(status="ok", kind="sdk", url=WORDS_SDK_URL, version="sdk-master", sdk_source=resp.text,
                        reference_url=REFERENCE_URL.format(host=BRAND_SOURCES["aspose.cloud"]["host"], product="words"))


def fetch_source(product: str, prior_version: str = "", brand: str = DEFAULT_BRAND) -> SourceResult:
    if product in BRAND_SOURCES[brand]["sdk_products"]:
        return fetch_words_sdk()
    return fetch_spec(product, prior_version, brand)
