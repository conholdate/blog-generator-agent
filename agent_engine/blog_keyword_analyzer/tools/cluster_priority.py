from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from .metrics import RunMetrics

logger = logging.getLogger(__name__)

# Relative score gap (against the top_n boundary score) within which two
# clusters are considered a "close call" rather than a confident ranking.
CLOSE_CALL_THRESHOLD = 0.15

# Bound the model prompt regardless of how many clusters happen to sit near
# the boundary (e.g. degenerate/flat scoring data).
_MAX_CONTESTED = 6


@dataclass(frozen=True)
class BoundaryZone:
    clearly_included: List[Any]
    contested: List[Any]
    remaining_slots: int


def _score(cluster: Any) -> float:
    return float(getattr(getattr(cluster, "metrics", None), "score", 0.0) or 0.0)


def find_boundary_zone(
    scored_clusters: List[Any],
    top_n: int,
    threshold: float = CLOSE_CALL_THRESHOLD,
) -> BoundaryZone:
    """
    Pure and deterministic. `scored_clusters` must already be sorted
    descending by score (as `tools/scoring.py`'s `score_clusters()` returns
    them). Identifies whether the score gap right at the top_n cutoff is
    narrow enough that the deterministic ranking isn't a confident signal —
    i.e. whether there's a genuine close call worth asking the model about.

    Returns `contested=[]` (no model call warranted) when: there aren't
    more clusters than top_n, the boundary score is ~0 (nothing to compare
    relative to), or only the boundary cluster itself is close to itself
    (no real ambiguity).
    """
    n = len(scored_clusters)
    if top_n <= 0 or n <= top_n:
        return BoundaryZone(clearly_included=list(scored_clusters[:top_n]), contested=[], remaining_slots=0)

    boundary_score = _score(scored_clusters[top_n - 1])
    if abs(boundary_score) < 1e-9:
        return BoundaryZone(clearly_included=list(scored_clusters[:top_n]), contested=[], remaining_slots=0)

    contested_indices = [
        i
        for i, c in enumerate(scored_clusters)
        if abs(_score(c) - boundary_score) / abs(boundary_score) <= threshold
    ]

    if len(contested_indices) <= 1:
        return BoundaryZone(clearly_included=list(scored_clusters[:top_n]), contested=[], remaining_slots=0)

    # Bound the contested set to the closest-to-boundary candidates, capped,
    # then restore ascending index order for stable, readable output.
    contested_indices.sort(key=lambda i: abs(_score(scored_clusters[i]) - boundary_score))
    contested_indices = sorted(contested_indices[:_MAX_CONTESTED])

    contested_set = set(contested_indices)
    clearly_included = [c for i, c in enumerate(scored_clusters[:top_n]) if i not in contested_set]
    contested = [scored_clusters[i] for i in contested_indices]
    remaining_slots = top_n - len(clearly_included)

    return BoundaryZone(clearly_included=clearly_included, contested=contested, remaining_slots=remaining_slots)


def choose_cluster_priority(
    client: Any,
    *,
    model: str,
    contested: List[Any],
    remaining_slots: int,
    metrics: Optional["RunMetrics"] = None,
) -> List[Any]:
    """
    Ask the model to rank a small boundary-zone shortlist (not the full
    cluster list) and return its preferred order. Falls back to the
    existing score order — `contested` is already sorted by closeness to
    the boundary, itself derived from the score-sorted input — if the call
    fails, the client is unavailable, there's nothing to reason about, or
    the response can't be matched back to real contested cluster ids.
    """
    fallback = list(contested)
    if not contested or client is None:
        return fallback

    def _keywords(cluster: Any) -> List[str]:
        return [m.keyword for m in getattr(cluster, "members", [])[:5]]

    candidates_desc = "\n".join(
        f"- id={c.cluster_id!r} label={c.label!r} intent={c.metrics.intent!r} "
        f"score={_score(c):.3f} keywords={_keywords(c)}"
        for c in contested
    )
    prompt = (
        "These candidate keyword clusters have nearly identical scores, so the "
        "numeric score alone isn't a confident signal for which to prioritize. "
        "Rank them by which would make the strongest, most coherent blog topic:\n\n"
        f"{candidates_desc}\n\n"
        "Respond with only the cluster ids, most preferred first, comma-separated, "
        "nothing else. Example: id1, id2, id3"
    )

    raw = ""
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning("choose_cluster_priority call failed, keeping score order: %s", exc)
        return fallback

    by_id = {str(c.cluster_id): c for c in contested}
    picked_ids = [token.strip().strip("\"'") for token in raw.split(",")]

    seen: set[str] = set()
    ordered: List[Any] = []
    for pid in picked_ids:
        if pid in by_id and pid not in seen:
            ordered.append(by_id[pid])
            seen.add(pid)
    # Anything the model didn't mention, or if the response didn't parse
    # into any valid id at all, is appended in its original score order —
    # this degrades to the fallback order, never to an incomplete list.
    missing = [c for c in contested if str(c.cluster_id) not in seen]
    result = ordered + missing

    if metrics is not None:
        metrics.add_event(
            "CLUSTER_PRIORITY_CHOSEN",
            "Model ranked a contested cluster boundary zone",
            contested_count=len(contested),
            model_informed=bool(ordered),
            chosen_first=str(result[0].cluster_id) if result else "",
        )
    return result


def apply_cluster_priority(
    all_clusters: List[Any],
    zone: BoundaryZone,
    prioritized_contested: List[Any],
) -> List[Any]:
    """
    Pure. Returns the full cluster list with only the top_n boundary zone
    reordered: clearly-included clusters keep their order, followed by the
    model-prioritized (or fallback score-ordered) contested clusters up to
    the number of remaining slots, followed by every other cluster from
    `all_clusters` unchanged, in its original order.
    """
    reordered_top = list(zone.clearly_included) + list(prioritized_contested)[: zone.remaining_slots]
    reordered_ids = {id(c) for c in reordered_top}
    rest = [c for c in all_clusters if id(c) not in reordered_ids]
    return reordered_top + rest
