from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from .metrics import RunMetrics

logger = logging.getLogger(__name__)

_STRATEGIES = ("broaden", "narrow", "rephrase")
_DEFAULT_STRATEGY = "rephrase"


def choose_retry_strategy(
    client: Any,
    *,
    model: str,
    seed_topic: str,
    rejected_titles: List[str],
    metrics: Optional["RunMetrics"] = None,
) -> str:
    """
    Ask the model to choose ONE retry strategy ("broaden", "narrow", or
    "rephrase") given a seed topic and the titles it just proposed and had
    rejected as duplicates.

    This is a real branching decision informed by the model rather than a
    fixed Python rule — before this, every retry used the same fixed
    strategy (re-ask, excluding rejected titles) regardless of *why* every
    title collided. See Docs/adr/0004-model-chosen-retry-strategy.md.

    Falls back to "rephrase" (the prior, Python-only default behavior) if
    there's no seed topic, the call fails, or the response can't be parsed
    as one of the three options: this extra call is a genuine enhancement,
    not a reliability requirement, and a failure here must never break the
    retry it's meant to inform.
    """
    if not seed_topic or not rejected_titles or client is None:
        return _DEFAULT_STRATEGY

    prompt = (
        "A blog-topic generator proposed titles for this seed topic that all "
        "collided with existing content:\n"
        f"Seed topic: {seed_topic}\n"
        f"Rejected titles: {', '.join(rejected_titles[:5])}\n\n"
        "Choose exactly one retry strategy:\n"
        "- broaden: the seed topic is too narrow; widen its scope\n"
        "- narrow: the seed topic is too broad; make it more specific\n"
        "- rephrase: the scope is fine; just phrase it differently\n"
        "Respond with exactly one word: broaden, narrow, or rephrase."
    )

    raw = ""
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (resp.choices[0].message.content or "").strip().lower()
    except Exception as exc:
        logger.warning("choose_retry_strategy call failed, defaulting to %r: %s", _DEFAULT_STRATEGY, exc)

    strategy = next((s for s in _STRATEGIES if s in raw), _DEFAULT_STRATEGY)

    if metrics is not None:
        metrics.add_event(
            "RETRY_STRATEGY_CHOSEN",
            f"Model chose retry strategy: {strategy}",
            strategy=strategy,
            seed_topic=seed_topic,
        )
    return strategy


def apply_retry_strategy(seed_topic: str, strategy: str) -> str:
    """
    Deterministically transform seed_topic according to a chosen strategy.
    The *choice* of strategy is model-driven (choose_retry_strategy); this
    function's job is only to execute that choice predictably so the effect
    is testable independent of any live model call.
    """
    tokens = seed_topic.split()
    if strategy == "broaden" and len(tokens) > 3:
        return " ".join(tokens[:-1])
    if strategy == "narrow":
        return f"{seed_topic} tutorial"
    return seed_topic
