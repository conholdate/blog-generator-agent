from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence

from .normalization import normalize_text


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    score: float
    candidate_id: Optional[str] = None
    candidate_title: Optional[str] = None
    candidate_topic: Optional[str] = None
    candidate_url: Optional[str] = None
    candidate_rank: Optional[int] = None
    match_type: str = "lexical"
    match_band: str = "none"


@dataclass(frozen=True)
class MatchConfig:
    threshold_strict: float = 0.86
    threshold_loose: float = 0.80
    top_k: int = 5
    no_embeddings: bool = False

    def normalized(self) -> "MatchConfig":
        strict = _clamp01(self.threshold_strict)
        loose = _clamp01(self.threshold_loose)
        if loose > strict:
            loose = strict
        return MatchConfig(
            threshold_strict=strict,
            threshold_loose=loose,
            top_k=max(1, int(self.top_k or 1)),
            no_embeddings=bool(self.no_embeddings),
        )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


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


def match_band(score: float, config: MatchConfig) -> str:
    cfg = config.normalized()
    if score >= cfg.threshold_strict:
        return "strict"
    if score >= cfg.threshold_loose:
        return "loose"
    return "none"


def best_lexical_record_match(
    baseline_topic: str,
    candidates: Sequence[Any],
    *,
    config: MatchConfig,
) -> MatchResult:
    """
    Rank candidates lexically and return the best candidate inside top_k that
    reaches threshold_loose. This keeps threshold/top-k behavior deterministic
    for the current coverage engine.
    """
    cfg = config.normalized()
    scored: list[tuple[float, int, Any]] = []
    for idx, candidate in enumerate(candidates):
        cand_text = (getattr(candidate, "topic", "") or getattr(candidate, "title", "") or "").strip()
        score = lexical_fast_match(baseline_topic, cand_text).score
        scored.append((score, idx, candidate))

    scored.sort(key=lambda item: (-item[0], item[1]))
    for rank, (score, _idx, candidate) in enumerate(scored[: cfg.top_k], start=1):
        band = match_band(score, cfg)
        if band == "none":
            continue
        return MatchResult(
            matched=True,
            score=float(score),
            candidate_id=getattr(candidate, "id", None),
            candidate_title=getattr(candidate, "title", None),
            candidate_topic=getattr(candidate, "topic", None),
            candidate_url=getattr(candidate, "url", None),
            candidate_rank=rank,
            match_type="lexical",
            match_band=band,
        )

    best_score = scored[0][0] if scored else 0.0
    return MatchResult(matched=False, score=float(best_score), match_type="lexical", match_band="none")
