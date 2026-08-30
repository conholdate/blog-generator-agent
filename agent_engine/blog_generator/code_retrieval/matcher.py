"""
Candidate scoring: weighted token overlap, no embeddings (see normalizer.py
docstring for why). Weighting is rarity-based (IDF-style): a query term that
shows up in almost every filename in this repo (e.g. "pptx" in a
PowerPoint-examples repo) is weak evidence, while a term that shows up in a
handful of files (e.g. "emf", "jpg") is strong evidence a candidate is
actually on-topic. This part is verified against real repos with no open
issues: fixed a case where an on-topic file lost to an off-topic one purely
on raw match count, and a separate tie that got broken by alphabetical luck
instead of relevance.

Also applies a bonus for a contiguous multi-word phrase match (e.g. "custom
function" appearing back-to-back in a filename is stronger evidence than
the same two words landing separately).

A further idea - "did this candidate match the single most distinctive
query term" as a second signal blended with recall (DISTINCTIVENESS_WEIGHT)
- is implemented but DISABLED (weight 0). Live-testing it against ~9 real
topics fixed 3 real ranking misses, but also produced two false
HIGH_CONFIDENCE picks on topics that have no real match in the repo at all
(worse than the honest LOW_CONFIDENCE those topics got without it) - and a
follow-up attempt to fix that by flooring the distinctiveness score against
an absolute rarity bar fixed those two but broke one of the original three
again. That's a sign this needs a proper before/after pass over a labeled
corpus (Phase 2), not more one-off adjustment against a handful of
hand-picked examples - left in place, disabled, as a documented starting
point for that pass rather than deleted.

Exact weights/thresholds below are placeholders, called out as such in the
architecture - real values come from Phase 2 tuning against a labeled
corpus of real blog topics, not invented here.
"""
import math

from .normalizer import candidate_terms

PHRASE_BONUS = 0.15
MAX_SCORE = 1.0


def _idf_weights(query_terms: set[str], all_candidate_terms: list[set[str]]) -> dict[str, float]:
    """Smoothed IDF per query term, computed against the corpus being ranked
    (the candidate list passed to this call) rather than a fixed global count -
    "rare" is relative to what else is actually being compared.

    A term with zero matches anywhere in the corpus gets zero weight, not the
    formula's maximum. That sounds backwards for "rare = important", but a
    term nothing can ever match isn't rare-and-diagnostic, it's simply
    unusable (e.g. a synonym like "powerpoint" when this repo's naming
    convention only ever spells out "PPTX"/"PPT") - the standard smoothed-IDF
    formula would otherwise hand it the single highest weight in the query,
    which then dilutes every real candidate's score against a term nothing
    could ever have matched."""
    n = len(all_candidate_terms)
    weights = {}
    for term in query_terms:
        doc_freq = sum(1 for terms in all_candidate_terms if term in terms)
        weights[term] = math.log((n + 1) / (doc_freq + 1)) + 1 if doc_freq else 0.0
    return weights


def _phrase_bonus(query_terms: set[str], lowered_text: str) -> float:
    query_list = sorted(query_terms)
    for i in range(len(query_list)):
        for j in range(i + 1, len(query_list)):
            if f"{query_list[i]}-{query_list[j]}" in lowered_text or f"{query_list[j]}-{query_list[i]}" in lowered_text:
                return PHRASE_BONUS
    return 0.0


DISTINCTIVENESS_WEIGHT = 0.0  # disabled - see module docstring for what was tried and why
# Absolute idf floor a term needs to count as genuinely distinctive (not just
# "least generic of a mediocre bunch"). Confirmed against the smoothed-idf
# formula over a ~2,270-file repo: terms appearing in <1% of files (e.g.
# "emf" df=4, "jpg" df=9) land at idf ~6.4-8; common terms (df 50+, i.e. 2%+
# of files) drop to ~4.8 or below. Without this floor, a query where the one
# truly rare term is unmatchable (a typo, or a repo that just doesn't have
# that example) still treats whichever leftover generic term is *relatively*
# less common as if it were fully distinctive - confirmed to cause a false
# HIGH_CONFIDENCE pick on a topic with no real match in the repo.
DISTINCTIVE_IDF_FLOOR = 6.0


def score_candidate(query_terms: set[str], candidate_text: str, idf: dict[str, float] | None = None) -> float:
    """`idf` is optional so this stays usable standalone (e.g. verification.py's
    header-topic check) - without it, every term is weighted equally, same as
    the original plain-overlap behavior.

    Blends two signals rather than using weighted recall alone: recall
    (matched_weight / total_weight) rewards breadth, but confirmed against 4
    real repo results that breadth alone lets several generic-term matches
    consistently outscore one match on the single most specific term in the
    query (e.g. "emf"/"jpg"/"png" losing to 3 matches on "ppt"/"convert"/
    "slide"). Blending in "did this candidate match the single most
    distinctive query term" gives that one high-value match a floor it can't
    be diluted below, without discarding recall entirely."""
    if not query_terms:
        return 0.0
    terms = candidate_terms(candidate_text)
    weights = idf or {t: 1.0 for t in query_terms}
    total_weight = sum(weights.values())
    matched = [t for t in query_terms if t in terms]
    matched_weight = sum(weights[t] for t in matched)
    recall = matched_weight / total_weight if total_weight else 0.0

    max_matched = max((weights[t] for t in matched), default=0.0)
    distinctiveness = min(1.0, max_matched / DISTINCTIVE_IDF_FLOOR)

    base = (1 - DISTINCTIVENESS_WEIGHT) * recall + DISTINCTIVENESS_WEIGHT * distinctiveness
    bonus = _phrase_bonus(query_terms, candidate_text.lower())
    return min(MAX_SCORE, base + bonus)


def rank(query_terms: set[str], candidates: list[tuple[str, str]], top_n: int) -> list[dict]:
    """candidates: list of (id, text_to_score_against). Returns top_n as
    [{"id": ..., "score": ...}], sorted descending, ties broken by id for determinism."""
    if not query_terms or not candidates:
        return []
    all_terms = [candidate_terms(text) for _, text in candidates]
    idf = _idf_weights(query_terms, all_terms)
    scored = [
        {"id": cand_id, "score": round(score_candidate(query_terms, text, idf), 4)}
        for cand_id, text in candidates
    ]
    scored.sort(key=lambda c: (-c["score"], c["id"]))
    return scored[:top_n]
