#!/usr/bin/env python3
"""
One-time (re-runnable) bulk population of Redis with quantized embedding
vectors for every post already in content/dashboard_topic_index.json (see
scripts/build_dashboard_topic_index.py for how that lexical index itself
was built).

Writes are batched PER BUCKET (one Redis SET per brand|product|platform
key holding the whole bucket's vectors) rather than reusing
orchestrator.py's append_new_post() one-post-at-a-time GET+SET, which
would be O(n^2) data transfer for a bucket with n existing posts - fine
for appending one new post at a time in production, wasteful for a bulk
backfill of thousands.

Usage:
  python scripts/build_dashboard_topic_vectors.py                  # full run
  python scripts/build_dashboard_topic_vectors.py --limit-buckets 2  # smoke test
  python scripts/build_dashboard_topic_vectors.py --concurrency 10
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "agent_engine" / "blog_generator"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / ".env")

import requests  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402

from config import settings  # noqa: E402
from utils.topic_embeddings import quantize, pack_vector  # noqa: E402

INDEX_PATH = REPO_ROOT / "content" / "dashboard_topic_index.json"


def redis_creds() -> tuple:
    url = os.getenv("KV_REST_API_URL")
    token = os.getenv("KV_REST_API_TOKEN")
    if not url or not token:
        raise SystemExit("KV_REST_API_URL / KV_REST_API_TOKEN not set in .env - add them first.")
    return url.rstrip("/"), token


async def embed_with_retry(
    client: AsyncOpenAI, model: str, text: str, semaphore: asyncio.Semaphore, retries: int = 3
) -> Optional[List[float]]:
    async with semaphore:
        for attempt in range(1, retries + 1):
            try:
                resp = await client.embeddings.create(model=model, input=text)
                return resp.data[0].embedding
            except Exception as exc:
                if attempt == retries:
                    print(f"⚠️ Failed to embed after {retries} attempts: {text!r}: {exc}", flush=True)
                    return None
                await asyncio.sleep(1.5 * attempt)
    return None


async def run(concurrency: int, limit_buckets: Optional[int]) -> None:
    index: Dict[str, List[dict]] = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    base_url, token = redis_creds()
    headers = {"Authorization": f"Bearer {token}"}
    client = AsyncOpenAI(base_url=settings.PROFESSIONALIZE_BASE_URL, api_key=settings.PROFESSIONALIZE_API_KEY_2)
    semaphore = asyncio.Semaphore(concurrency)

    bucket_items = list(index.items())
    if limit_buckets:
        bucket_items = bucket_items[:limit_buckets]

    total_posts = sum(len(entries) for _, entries in bucket_items)
    done = 0
    embedded = 0
    start = time.time()

    for bucket_key, entries in bucket_items:
        tasks = [
            embed_with_retry(client, settings.PROFESSIONALIZE_EMBEDDING_MODEL, e["title"], semaphore)
            for e in entries
        ]
        vectors = await asyncio.gather(*tasks)

        redis_entries = []
        for entry, vec in zip(entries, vectors):
            done += 1
            if vec is None:
                continue
            redis_entries.append({"key": entry.get("url") or entry["title"], "vector": pack_vector(quantize(vec))})
            embedded += 1

        ok = True
        if redis_entries:
            ok = False
            payload = json.dumps(redis_entries)
            for attempt in range(1, 4):
                try:
                    resp = requests.post(
                        f"{base_url}/set/topicvec:{bucket_key}",
                        headers=headers,
                        data=payload,
                        timeout=30,
                    )
                    ok = resp.ok
                    break
                except requests.exceptions.RequestException as exc:
                    if attempt == 3:
                        print(f"⚠️ Redis write failed after 3 attempts for {bucket_key}: {exc}", flush=True)
                    else:
                        time.sleep(2 * attempt)

        elapsed = time.time() - start
        print(
            f"[{done}/{total_posts}] {bucket_key}: {len(redis_entries)}/{len(entries)} vectors written "
            f"({'ok' if ok else 'FAILED'}) - {elapsed:.0f}s elapsed",
            flush=True,
        )

    print(f"\nDone. {embedded}/{total_posts} embedded across {len(bucket_items)} buckets in {time.time()-start:.0f}s.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=15)
    parser.add_argument("--limit-buckets", type=int, default=None, help="Process only the first N buckets (smoke test).")
    args = parser.parse_args()
    asyncio.run(run(args.concurrency, args.limit_buckets))
