"""
Where each aspose.cloud product's capability data comes from - public,
unauthenticated sources only (confirmed live 2026-11-03):

- 14 products: Swagger spec at https://api.aspose.cloud/<version>/<product>/swagger/spec.
  The newest version differs per product (BarCode/Cells/Email v4.0, CAD/HTML
  v2.0, the rest v3.0), so it's discovered at run time, newest first - an
  older spec can silently miss features (Email v3.0 had no conversions).
- Aspose.Words Cloud: its v3.0 spec is from 2017 (78 endpoints vs ~192
  operations today), so its official Python SDK source is used instead.
- Aspose.Total Cloud: a bundle of all the APIs, no spec of its own - handled
  as "all products combined" at check time, never fetched here.

Every fetch distinguishes "not found" from "failed": the builder only
replaces a product's existing file on a real result, never on a network
error, so one bad run can't wipe a product's capabilities.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

SPEC_URL = "https://api.aspose.cloud/{version}/{product}/swagger/spec"
SPEC_VERSIONS = ("v4.0", "v3.0", "v2.0")
WORDS_SDK_URL = (
    "https://raw.githubusercontent.com/aspose-words-cloud/aspose-words-cloud-python/"
    "master/asposewordscloud/apis/words_api.py"
)
TIMEOUT = 120  # Slides/PDF specs are ~1 MB and occasionally slow

SDK_PRODUCTS = {"words"}
BUNDLE_PRODUCTS = {"total"}


@dataclass
class SourceResult:
    status: str  # "ok" | "not_found" | "error"
    kind: str = ""  # "spec" | "sdk"
    url: str = ""
    version: str = ""
    spec: dict | None = None
    sdk_source: str = ""
    error: str = ""


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


def fetch_spec(product: str, prior_version: str = "") -> SourceResult:
    """Newest available spec. A version that keeps failing (5xx/network) is
    skipped, but an OLDER version than `prior_version` (what we built from
    last time) is never accepted - that would silently downgrade to a stale
    spec because the newer one had a bad day. The caller keeps its previous
    data instead."""
    last_error, unreachable = "", []
    for version in SPEC_VERSIONS:
        url = SPEC_URL.format(version=version, product=product)
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
        return SourceResult(status="ok", kind="spec", url=url, version=version, spec=spec, error=note)
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
    return SourceResult(status="ok", kind="sdk", url=WORDS_SDK_URL, version="sdk-master", sdk_source=resp.text)


def fetch_source(product: str, prior_version: str = "") -> SourceResult:
    if product in SDK_PRODUCTS:
        return fetch_words_sdk()
    return fetch_spec(product, prior_version)
