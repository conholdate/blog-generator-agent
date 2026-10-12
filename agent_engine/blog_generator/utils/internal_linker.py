"""
Post-generation step: finds existing published posts in the same brand/
product/platform bucket that are topically related (not duplicate) to a
freshly generated draft, and asks the LLM to weave a handful of contextual
links into the draft's body - never changing anything else about it. Runs
right before generate_markdown_file() writes the finalized content, same
place repair_code_fences/strip_snippet_markers already run in orchestrator.py.

Reuses the exact data the dashboard's duplicate check already reads
(content/dashboard_topic_index.json for titles/urls, Redis topicvec:* for
quantized embedding vectors) - no new data source, and the same bucket-key
format append_new_post() already writes with, so a lookup here matches
whatever prior runs appended.

Best-effort throughout: any failure (missing Redis creds, embedding API
down, LLM call failing the safety check) returns the original content
unchanged rather than blocking a run that otherwise succeeded - same
philosophy as topic_index.py's append functions.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import settings
from services.LLMservice import llm_service
from .topic_embeddings import cosine_similarity, dequantize, embed_text, unpack_vector

# parents[0]=utils, [1]=blog_generator, [2]=agent_engine, [3]=repo root -
# same resolution topic_index.py uses for the same file.
REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = REPO_ROOT / "content" / "dashboard_topic_index.json"


def _bucket_key(brand: str, product: str, platform: str) -> str:
    return f"{brand}|{product}|{platform}"


# ── Lexical fallback (no embedding vectors needed) ──────────────────────────
# Word-overlap only (jaccardSimilarity, ported from lib/topic-duplicate.ts) -
# deliberately NOT that file's combined lexicalScore; see
# _lexical_fallback_related's docstring for why. Used when a bucket has no
# Redis vectors yet (not provisioned, or a brand-new bucket), so internal
# linking still works before anything's been embedded.
_STOPWORDS = {
    "a", "an", "the", "in", "on", "for", "to", "of", "and", "or", "with", "using", "how", "what",
    "is", "are", "your", "you", "guide", "tutorial", "complete", "step", "by", "steps", "easy", "simple",
}


def _normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def _token_set(text: str) -> set:
    return {t for t in _normalize_title(text).split(" ") if t and t not in _STOPWORDS}


def _jaccard_similarity(a: str, b: str) -> float:
    set_a, set_b = _token_set(a), _token_set(b)
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a) + len(set_b) - intersection
    return intersection / union if union else 0.0


def _lexical_fallback_related(lexical_entries: List[dict], title: str) -> List[dict]:
    """Jaccard (word-overlap) only, NOT the combined lexicalScore the
    dashboard's duplicate check uses - confirmed via direct testing that
    levenshtein ratio alone scores completely unrelated short titles
    (e.g. "Convert ODS to XLSX in Python" vs "Merge PDF Files in Java") at
    ~0.31 from incidental character overlap, with zero shared words. That's
    fine for a duplicate check (either signal firing is enough), but it's
    noise here - a "related" link target needs real shared vocabulary."""
    scored: List[Tuple[float, dict]] = []
    for entry in lexical_entries:
        if not entry.get("url") or not entry.get("title"):
            continue
        score = _jaccard_similarity(title, entry["title"])
        if settings.INTERNAL_LINK_LEXICAL_MIN_SIMILARITY <= score <= settings.INTERNAL_LINK_LEXICAL_MAX_SIMILARITY:
            scored.append((score, entry))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[: settings.INTERNAL_LINK_MAX_COUNT]]


def _redis_creds() -> Optional[Tuple[str, str]]:
    url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return None
    return url.rstrip("/"), token


def _fetch_bucket_vectors(bucket_key: str) -> Dict[str, List[float]]:
    """entry key (post url, or title when a post has no url) -> dequantized
    float vector. Empty dict if Redis isn't configured or this bucket has no
    vectors yet (never raises - callers treat that as "nothing to link")."""
    creds = _redis_creds()
    if not creds:
        return {}
    base_url, token = creds
    try:
        resp = requests.get(
            f"{base_url}/get/topicvec:{bucket_key}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if not resp.ok:
            return {}
        raw = resp.json().get("result")
        if not raw:
            return {}
        entries = json.loads(raw)
        return {
            e["key"]: dequantize(unpack_vector(e["vector"]))
            for e in entries
            if e.get("key") and e.get("vector")
        }
    except Exception as exc:
        print(f"⚠️ Could not fetch topic vectors for internal linking (non-fatal): {exc}", flush=True)
        return {}


def _find_related_posts(brand: str, product: str, platform: str, title: str) -> List[dict]:
    """Up to INTERNAL_LINK_MAX_COUNT existing posts in this bucket whose
    title embedding is related-but-not-duplicate to `title` (see config.py's
    INTERNAL_LINK_MIN/MAX_SIMILARITY), best match first. [] on any failure,
    missing Redis config, or an empty/new bucket."""
    if not INDEX_PATH.exists():
        return []
    try:
        index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

    bucket_key = _bucket_key(brand, product, platform)
    lexical_entries = index.get(bucket_key, [])
    if not lexical_entries:
        return []

    vectors = _fetch_bucket_vectors(bucket_key)
    if not vectors:
        print(
            "ℹ️ No embedding vectors for this bucket yet - falling back to lexical-only matching for internal linking",
            flush=True,
        )
        return _lexical_fallback_related(lexical_entries, title)

    try:
        new_vector = embed_text(title)
    except Exception as exc:
        print(f"⚠️ Could not embed new post title for internal linking (non-fatal): {exc}", flush=True)
        return []

    scored: List[Tuple[float, dict]] = []
    for entry in lexical_entries:
        if not entry.get("url"):
            continue  # nothing to link to without a real URL
        key = entry["url"] or entry.get("title")
        vector = vectors.get(key)
        if vector is None:
            continue
        sim = cosine_similarity(new_vector, vector)
        if settings.INTERNAL_LINK_MIN_SIMILARITY <= sim <= settings.INTERNAL_LINK_MAX_SIMILARITY:
            scored.append((sim, entry))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[: settings.INTERNAL_LINK_MAX_COUNT]]


def _build_insertion_prompt(content: str, related: List[dict]) -> str:
    targets = "\n".join(f'- "{e["title"]}" -> {e["url"]}' for e in related)
    return (
        "You will insert internal links into a blog post's Markdown body. "
        "Below is a list of existing posts to link to, each with its exact URL.\n\n"
        f"{targets}\n\n"
        "Rules:\n"
        "1. Insert exactly one Markdown link for EACH post above, at the single most "
        "relevant point in the text where that topic is already being discussed.\n"
        "2. The link text must be a short, natural phrase already present in or very "
        "close to the surrounding sentence - never invent a new sentence just to hold a link.\n"
        "3. Use the EXACT URL given for each post. Never invent a URL or link to anything "
        "not listed above.\n"
        "4. Do not change any other word, heading, code block, or formatting in the post. "
        "Do not add, remove, or reorder content beyond inserting the links.\n"
        "5. If you cannot find a natural spot for one of the links, skip that one rather "
        "than forcing it.\n\n"
        "Reply with ONLY the full post body, links inserted, nothing else - no preamble, "
        "no explanation, no surrounding markers.\n\n"
        "--- POST BODY START ---\n"
        f"{content}\n"
        "--- POST BODY END ---"
    )


def _looks_safe(original: str, linked: str) -> bool:
    """Cheap sanity check, not a full diff: strip link syntax back out and
    confirm the remaining text is close in length to the original. Guards
    against the LLM rewriting, truncating, or padding the post instead of
    only inserting links - on any doubt, the caller discards the result and
    keeps the original rather than risk a silently mangled post."""
    if not linked or not linked.strip():
        return False
    stripped = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", linked)
    len_ratio = len(stripped) / max(len(original), 1)
    return 0.97 <= len_ratio <= 1.05


async def add_internal_links(brand: str, product: str, platform: str, title: str, content: str) -> str:
    """Best-effort: returns `content` unchanged on any failure, missing
    config, no related posts found, or a result that fails the safety
    check - a bad outcome here must never block a run that otherwise
    succeeded."""
    if not settings.INTERNAL_LINKING_ENABLED:
        return content

    try:
        related = _find_related_posts(brand, product, platform, title)
        if not related:
            return content

        prompt = _build_insertion_prompt(content, related)
        linked, _usage = await llm_service.complete(
            prompt=prompt,
            temperature=0.3,
            max_tokens=max(4000, len(content)),
        )

        if not _looks_safe(content, linked):
            print(
                "⚠️ Internal-linking result failed the safety check - keeping original content (non-fatal)",
                flush=True,
            )
            return content

        print(f"✅ Inserted internal links for up to {len(related)} related post(s)", flush=True)
        return linked
    except Exception as exc:
        print(f"⚠️ Could not insert internal links (non-fatal): {exc}", flush=True)
        return content
