"""
Keeps content/dashboard_topic_index.json (and, once Redis credentials
exist, the matching embedding vectors) current as each new post is
generated - both autonomous and dashboard-triggered manual runs. This is
what stops the one-time historical seed (scripts/build_dashboard_topic_index.py)
from going stale: everything generated from here on is appended
immediately, independent of agent_engine/content_indexer_agent ever
running again.

Both append functions are best-effort and never raise - a failure here
must not fail a generation run that otherwise succeeded, same philosophy
as orchestrator.py's non-fatal mark_topic_as_generated wrapper.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import requests

from .topic_embeddings import embed_and_quantize, pack_vector
from .layouts import HEADING_SKIP_SENTINEL

# parents[0]=utils, [1]=blog_generator, [2]=agent_engine, [3]=repo root.
# Was parents[2] (resolved to .../agent_engine, one level too shallow) -
# a real bug that silently wrote every append to
# agent_engine/content/dashboard_topic_index.json (untracked, never
# committed) instead of the real file, confirmed via a live CI run's
# "Untracked files: agent_engine/content/" in its git status output.
REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = REPO_ROOT / "content" / "dashboard_topic_index.json"


def product_family_from_category(category: str) -> str:
    """'Aspose.CAD Cloud Product Family' -> 'Aspose.CAD' - the exact same
    rule scripts/build_dashboard_topic_index.py uses when deriving product
    names from content/productsData/<brand>.json, kept identical so both
    the historical seed and new appends bucket posts the same way."""
    name = category or ""
    for suffix in (" Cloud Product Family", " Product Family"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _bucket_key(brand: str, product: str, platform: str) -> str:
    return f"{brand}|{product}|{platform}"


def append_to_topic_index(brand: str, product: str, platform: str, title: str, url: str, date: str) -> None:
    """Appends one entry to content/dashboard_topic_index.json - the file the
    generator's own "Commit generated blog to this repository" workflow step
    already commits, so this needs no separate commit/push step."""
    if not title:
        return
    try:
        index: dict = {}
        if INDEX_PATH.exists():
            index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        key = _bucket_key(brand, product, platform)
        bucket = index.setdefault(key, [])
        dedupe_key = url or title
        if any((e.get("url") or e.get("title")) == dedupe_key for e in bucket):
            return
        bucket.append({"title": title, "url": url, "date": date})
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        print(f"✅ Appended to dashboard_topic_index.json: {key}", flush=True)
    except Exception as exc:
        print(f"⚠️ Could not update dashboard_topic_index.json (non-fatal): {exc}", flush=True)


def _redis_creds() -> Optional[tuple]:
    # KV_REST_API_URL/TOKEN are what Vercel's Upstash Marketplace
    # integration actually names them (confirmed against the real
    # provisioned instance); UPSTASH_REDIS_REST_* kept as a fallback in
    # case a future instance is set up directly via the Upstash console
    # instead of through Vercel.
    url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return None
    return url.rstrip("/"), token


def _append_vector_to_redis(bucket_key: str, entry_key: str, quantized_vector: List[int]) -> None:
    """No-ops silently if KV_REST_API_URL/TOKEN aren't set yet - the
    dashboard's topic-duplicate check falls back to lexical-only matching
    in that case, so this is safe to call before Redis is provisioned.

    Verified end-to-end against the real provisioned instance: this
    function's write, read back via raw REST, and read back via the
    dashboard's @upstash/redis client (which auto-parses the JSON) all
    round-trip a real quantized embedding correctly.
    """
    creds = _redis_creds()
    if not creds:
        return
    base_url, token = creds
    redis_key = f"topicvec:{bucket_key}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        get_resp = requests.get(f"{base_url}/get/{redis_key}", headers=headers, timeout=10)
        existing: list = []
        if get_resp.ok:
            raw = get_resp.json().get("result")
            if raw:
                existing = json.loads(raw)
        existing = [e for e in existing if e.get("key") != entry_key]
        existing.append({"key": entry_key, "vector": pack_vector(quantized_vector)})
        requests.post(
            f"{base_url}/set/{redis_key}",
            headers=headers,
            data=json.dumps(existing),
            timeout=10,
        )
    except Exception as exc:
        print(f"⚠️ Could not update Redis topic vectors (non-fatal): {exc}", flush=True)


def append_new_post(brand: str, product: str, platform: str, title: str, url: str, date: str) -> None:
    """Full append: lexical index (always) + embedding vector (only if
    Redis is configured; also skipped, non-fatally, if the embedding API
    call itself fails - a flaky LLM endpoint must not break a generation
    run that already succeeded)."""
    append_to_topic_index(brand, product, platform, title, url, date)
    if _redis_creds() is None:
        return
    try:
        quantized = embed_and_quantize(title)
        _append_vector_to_redis(_bucket_key(brand, product, platform), url or title, quantized)
    except Exception as exc:
        print(f"⚠️ Could not embed new post for topic index (non-fatal): {exc}", flush=True)


# ── Closing-section heading history (Conclusion/FAQs/Read More rotation) ───
# Redis-backed, not git-committed like the lexical index above - this is
# pure anti-repetition state nobody needs to read directly, so a small key
# that updates in place is a better fit than a file that would need
# committing on every single post. Scoped by brand|product only (not
# platform), matching helpers.py's get_recent_layouts - the same product
# across platforms shares one rotation history, same as layout selection
# already does. HEADING_SKIP_SENTINEL itself lives in layouts.py (imported
# above) since that's the pure module defining what a heading "choice" is -
# this file only persists/reads history of those choices.


def _heading_history_key(brand: str, product: str) -> str:
    return f"headinghist:{brand}|{product}"


def get_recent_headings(brand: str, product: str, limit: int = 2) -> dict:
    """{"conclusion"|"faqs"|"read_more": [last `limit` values]} for this
    brand|product - each value is either a heading variant string or
    HEADING_SKIP_SENTINEL. Passed to layouts.select_layout's
    recent_headings param so it can avoid repeating the same text (or the
    same skip) back-to-back, same anti-repetition pattern
    get_recent_layouts already provides for layout names.

    Returns {} (nothing excluded - normal unconstrained rotation) if Redis
    isn't configured or there's no history yet. Never raises."""
    creds = _redis_creds()
    if not creds:
        return {}
    base_url, token = creds
    try:
        resp = requests.get(
            f"{base_url}/get/{_heading_history_key(brand, product)}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if not resp.ok:
            return {}
        raw = resp.json().get("result")
        if not raw:
            return {}
        data = json.loads(raw)
        return {k: v[-limit:] for k, v in data.items() if isinstance(v, list)}
    except Exception as exc:
        print(f"⚠️ Could not fetch recent headings (non-fatal): {exc}", flush=True)
        return {}


def record_headings_used(brand: str, product: str, chosen: dict, keep: int = 5) -> None:
    """Appends this post's actual heading choices to the same history
    get_recent_headings reads - `chosen` is
    {"conclusion"|"faqs"|"read_more": heading text or HEADING_SKIP_SENTINEL},
    normally built directly from the LayoutChoice a generation run used.
    Keeps the last `keep` entries per section (more than the `limit`
    get_recent_headings reads, so there's always real history even right
    after a key's values were just trimmed). Best-effort, non-fatal -
    called right alongside append_new_post once a post succeeds."""
    creds = _redis_creds()
    if not creds:
        return
    base_url, token = creds
    key = _heading_history_key(brand, product)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        get_resp = requests.get(f"{base_url}/get/{key}", headers=headers, timeout=10)
        existing: dict = {}
        if get_resp.ok:
            raw = get_resp.json().get("result")
            if raw:
                existing = json.loads(raw)
        for section, value in chosen.items():
            lst = existing.setdefault(section, [])
            lst.append(value)
            existing[section] = lst[-keep:]
        requests.post(f"{base_url}/set/{key}", headers=headers, data=json.dumps(existing), timeout=10)
    except Exception as exc:
        print(f"⚠️ Could not record headings used (non-fatal): {exc}", flush=True)
