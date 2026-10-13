"""
Post-generation step: finds existing published posts in the same brand/
product/platform bucket that are topically related (not duplicate) to a
freshly generated draft, and inserts a handful of contextual links into the
draft's body - never changing anything else about it. Runs right before
generate_markdown_file() writes the finalized content, same place
repair_code_fences/strip_snippet_markers already run in orchestrator.py.

The LLM is only asked to pick short anchor PHRASES that already exist
verbatim in the text (see _build_anchor_prompt) - it never rewrites the
post. The actual link insertion is a deterministic, verified string
replacement in code (_apply_anchors), which can't corrupt or truncate
content because it never regenerates it. An earlier version asked the LLM
to return the whole rewritten post and validated the result with a
length-ratio heuristic; confirmed broken on two real runs (PRs #63, #64)
where the self-hosted model didn't reproduce the document verbatim.

Reuses the exact data the dashboard's duplicate check already reads
(content/dashboard_topic_index.json for titles/urls, Redis topicvec:* for
quantized embedding vectors) - no new data source, and the same bucket-key
format append_new_post() already writes with, so a lookup here matches
whatever prior runs appended.

Best-effort throughout: any failure (missing Redis creds, embedding API
down, no anchor surviving validation) returns the original content
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


def _build_anchor_prompt(content: str, related: List[dict]) -> str:
    """Asks the LLM for ANCHOR PHRASES only, never a rewrite of the post.

    Earlier version asked the LLM to return the entire post body with links
    woven in. Confirmed broken on two real runs (PRs #63, #64): the
    self-hosted model doesn't reliably reproduce a long document verbatim -
    once it grew the content, once it quietly dropped ~9% of it, both
    caught by the old length-ratio safety check but with nothing usable to
    show for the attempt. Asking for a handful of short exact phrases
    instead keeps the LLM's job tiny (a few words per target, not 12K
    characters) and lets the actual insertion happen in code via exact
    string replacement - see _apply_anchors, which can't corrupt or
    truncate the post because it never rewrites it, only slices into it."""
    targets = "\n".join(f'{i + 1}. "{e["title"]}" -> {e["url"]}' for i, e in enumerate(related))
    return (
        "Below is a blog post body and a list of existing posts to link to from it.\n\n"
        f"{targets}\n\n"
        "For each post above, find a SHORT phrase (3-8 words) that appears VERBATIM, "
        "word-for-word, somewhere in the POST BODY below, and reads as a natural mention "
        "of that post's topic - a phrase worth linking, not a generic/filler phrase.\n\n"
        "Rules:\n"
        "- The phrase must be an EXACT substring of the post body - copy it character for "
        "character, do not paraphrase, fix, or retype it.\n"
        "- Never pick a phrase from a heading (a line starting with #) or from inside a "
        "code block (between ``` fences).\n"
        "- Never pick a phrase that's already inside a Markdown link, e.g. already between "
        "[ and ].\n"
        "- If you can't find a good, exact, natural phrase for one of the posts, skip it - "
        "do not force a weak match.\n\n"
        "Reply with ONLY one line per post you found a phrase for, in this exact format, "
        "nothing else - no preamble, no numbering, no explanation:\n"
        "URL | exact phrase from the text\n\n"
        "--- POST BODY START ---\n"
        f"{content}\n"
        "--- POST BODY END ---"
    )


def _code_block_spans(content: str) -> List[Tuple[int, int]]:
    return [m.span() for m in re.finditer(r"```.*?```", content, flags=re.DOTALL)]


def _parse_anchor_lines(raw: str) -> List[Tuple[str, str]]:
    """Each reply line -> (url, anchor). Malformed lines are skipped, not
    fatal - a partial, well-formed response is still useful."""
    pairs: List[Tuple[str, str]] = []
    for line in (raw or "").splitlines():
        line = line.strip().lstrip("-*0123456789. ").strip()
        if " | " not in line:
            continue
        url_part, _, anchor_part = line.partition(" | ")
        url = url_part.strip().strip('"')
        anchor = anchor_part.strip().strip('"')
        if url and anchor:
            pairs.append((url, anchor))
    return pairs


def _apply_anchors(content: str, related: List[dict], anchor_lines: List[Tuple[str, str]]) -> Tuple[str, int]:
    """Applies each (url, anchor) pair as a literal, exact string
    replacement - never a rewrite. Every check here exists to make a bad
    LLM pick a no-op rather than something that reaches the published post:
    the URL must be one we actually offered (no hallucinated links), the
    anchor must exist verbatim in the CURRENT content, must not fall inside
    a fenced code block, and must not already be part of a Markdown link.
    Only the first occurrence is replaced, and each application re-checks
    against the content as modified by prior ones so two anchors can never
    overlap or double-link the same text.

    Returns (new_content, inserted_count)."""
    valid_urls = {e["url"] for e in related if e.get("url")}
    inserted = 0
    for url, anchor in anchor_lines:
        if inserted >= settings.INTERNAL_LINK_MAX_COUNT:
            break
        if url not in valid_urls:
            print(f"⚠️ Internal linking: LLM proposed a URL not in the offered list, skipping ({url})", flush=True)
            continue
        if not (3 <= len(anchor) <= 120):
            continue
        idx = content.find(anchor)
        if idx == -1:
            print(f"ℹ️ Internal linking: anchor not found verbatim in the post, skipping ({anchor!r})", flush=True)
            continue
        if any(start <= idx < end for start, end in _code_block_spans(content)):
            print(f"ℹ️ Internal linking: anchor falls inside a code block, skipping ({anchor!r})", flush=True)
            continue
        line_start = content.rfind("\n", 0, idx) + 1
        if content[line_start:idx].lstrip().startswith("#"):
            print(f"ℹ️ Internal linking: anchor falls on a heading line, skipping ({anchor!r})", flush=True)
            continue
        if f"[{anchor}]" in content:
            print(f"ℹ️ Internal linking: anchor is already part of a link, skipping ({anchor!r})", flush=True)
            continue
        content = content[:idx] + f"[{anchor}]({url})" + content[idx + len(anchor):]
        inserted += 1
    return content, inserted


async def add_internal_links(brand: str, product: str, platform: str, title: str, content: str) -> str:
    """Best-effort: returns `content` unchanged on any failure, missing
    config, no related posts found, or no anchor the LLM proposed surviving
    validation - a bad outcome here must never block a run that otherwise
    succeeded. See _build_anchor_prompt's docstring for why this asks the
    LLM for short anchor phrases rather than a full rewrite."""
    if not settings.INTERNAL_LINKING_ENABLED:
        return content

    try:
        related = _find_related_posts(brand, product, platform, title)
        if not related:
            return content

        prompt = _build_anchor_prompt(content, related)
        raw, _usage = await llm_service.complete(prompt=prompt, temperature=0.2, max_tokens=500)

        anchor_lines = _parse_anchor_lines(raw)
        if not anchor_lines:
            print("ℹ️ Internal linking: LLM proposed no usable anchor phrases", flush=True)
            return content

        linked, inserted = _apply_anchors(content, related, anchor_lines)
        if inserted == 0:
            print("ℹ️ Internal linking: no proposed anchor survived validation - keeping original content", flush=True)
            return content

        print(f"✅ Inserted {inserted} internal link(s)", flush=True)
        return linked
    except Exception as exc:
        print(f"⚠️ Could not insert internal links (non-fatal): {exc}", flush=True)
        return content
