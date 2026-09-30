"""
Embedding helper for the dashboard's topic-duplicate index
(content/dashboard_topic_index_vectors/*.json - see
scripts/build_dashboard_topic_index.py and orchestrator.py's
append-on-generate hook).

Standalone - calls the shared Professionalize embeddings endpoint directly
(same credentials already used for LLM generation, settings.py), no
dependency on agent_engine/content_indexer_agent's own embeddings module.

Vectors are quantized to int8 before storage - full float32 (4096 dims)
would be ~311MB across the current post corpus, too large to store/sync
cheaply. Quantization range [-0.3, 0.3] was chosen after checking real
model output (observed range ~[-0.09, 0.115], normalized vectors) - the
extra headroom avoids clipping outlier dimensions. Verified round-trip
accuracy against the real API: cosine similarity of a genuinely similar
title pair only moved from 0.9363 -> 0.9352 after quantize/dequantize
(negligible - well inside the noise a similarity threshold already has to
tolerate).
"""
from __future__ import annotations

import base64
import math
import os
import struct
import sys
from typing import List

from openai import OpenAI

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import settings

# Must match the constant used on the dashboard (TypeScript) side exactly -
# a mismatch here silently corrupts every cosine-similarity comparison.
QUANTIZE_CLAMP = 0.3
QUANTIZE_SCALE = 127 / QUANTIZE_CLAMP

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=settings.PROFESSIONALIZE_BASE_URL, api_key=settings.PROFESSIONALIZE_API_KEY_2)
    return _client


def embed_text(text: str) -> List[float]:
    """Raw float embedding for one string. Not cached - callers that embed
    many titles (the backfill script) should space out calls; this is a
    live API call every time."""
    resp = _get_client().embeddings.create(model=settings.PROFESSIONALIZE_EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


def quantize(vector: List[float]) -> List[int]:
    """Float embedding -> int8 list, clamped to +/-QUANTIZE_CLAMP before
    scaling so a rare outlier dimension can't blow out the whole scale."""
    return [max(-127, min(127, round(v * QUANTIZE_SCALE))) for v in vector]


def dequantize(qvector: List[int]) -> List[float]:
    return [q / QUANTIZE_SCALE for q in qvector]


def pack_vector(qvector: List[int]) -> str:
    """int8 list -> base64 string, for compact storage. A plain JSON int
    array runs ~3.5x larger (confirmed on a real 4096-dim vector: ~19KB vs
    ~5.5KB) - large enough that the plain-array encoding pushed one real
    bucket (767 posts) over Upstash's 10MB per-request limit. Decoded on
    the dashboard (TypeScript) side via Buffer + Int8Array, which reads
    the same two's-complement bytes struct.pack('b', ...) writes here."""
    return base64.b64encode(struct.pack(f"{len(qvector)}b", *qvector)).decode("ascii")


def unpack_vector(b64: str) -> List[int]:
    packed = base64.b64decode(b64)
    return list(struct.unpack(f"{len(packed)}b", packed))


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_and_quantize(text: str) -> List[int]:
    return quantize(embed_text(text))
