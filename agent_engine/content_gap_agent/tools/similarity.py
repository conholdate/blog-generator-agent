from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .normalize import normalize_text


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    score: float
    candidate_id: Optional[str] = None
    candidate_title: Optional[str] = None
    candidate_topic: Optional[str] = None


def lexical_fast_match(baseline_topic: str, candidate_topic: str) -> MatchResult:
    """
    Step 1 implementation: deterministic lexical matching only.
    - Exact match on normalized topic text => score 1.0
    - Substring containment (either direction) => score 0.9
    - Else => no match

    Embedding-based matching will be added in Step 2 without changing the public API.
    """
    b = normalize_text(baseline_topic)
    c = normalize_text(candidate_topic)

    if not b or not c:
        return MatchResult(matched=False, score=0.0)

    if b == c:
        return MatchResult(matched=True, score=1.0)

    if b in c or c in b:
        return MatchResult(matched=True, score=0.9)

    return MatchResult(matched=False, score=0.0)
