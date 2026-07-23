from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Bound growth: keep only the most recent N titles per brand/product/platform key.
_MAX_TITLES_PER_KEY = 200

# Namespace for the failure-streak counters within the same history file.
# Never collides with a real history_key(), which is always
# "brand|product|platform" and never starts with an underscore.
_FAILURE_STREAK_NAMESPACE = "_failure_streaks"

# Consecutive zero-topic runs for the same key before escalating.
ESCALATION_THRESHOLD = 3


def history_key(brand: str, product: str, platform: Optional[str]) -> str:
    parts = [
        (brand or "").strip().lower(),
        (product or "").strip().lower(),
        (platform or "general").strip().lower(),
    ]
    return "|".join(parts)


def _read_history_file(history_path: Path) -> Dict[str, List[str]]:
    if not history_path.is_file():
        return {}
    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read run history at %s: %s", history_path, exc)
        return {}
    return data if isinstance(data, dict) else {}


def load_run_history(
    history_path: Path,
    *,
    brand: str,
    product: str,
    platform: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Return topic titles a previous, separate run already generated or had
    rejected for this brand/product/platform, as {"title": ...} dicts ready
    to merge into an existing_topics duplicate-avoidance list.

    This is what makes duplicate avoidance survive across CLI invocations,
    not just within a single run: content-index lookups only know about
    already-published posts, so two KRA runs for the same seed topic before
    publication would otherwise regenerate the same title twice.
    """
    data = _read_history_file(history_path)
    key = history_key(brand, product, platform)
    titles = data.get(key) or []
    return [{"title": title} for title in titles if isinstance(title, str) and title]


def record_run_history(
    history_path: Path,
    *,
    brand: str,
    product: str,
    platform: Optional[str],
    titles: List[str],
) -> None:
    """
    Persist newly seen topic titles (generated and/or rejected) so a later,
    separate run can avoid repeating them. Best-effort: failures are logged,
    never raised, since this is a quality improvement, not a correctness
    requirement of the run that produced the titles.
    """
    clean_titles = [t.strip() for t in titles if isinstance(t, str) and t.strip()]
    if not clean_titles:
        return

    try:
        data = _read_history_file(history_path)
        key = history_key(brand, product, platform)
        existing = list(data.get(key) or [])
        seen = set(existing)
        for title in clean_titles:
            if title not in seen:
                existing.append(title)
                seen.add(title)
        data[key] = existing[-_MAX_TITLES_PER_KEY:]

        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to record run history at %s: %s", history_path, exc)


def record_run_outcome(
    history_path: Path,
    *,
    brand: str,
    product: str,
    platform: Optional[str],
    succeeded: bool,
) -> int:
    """
    Track consecutive zero-topic runs for a brand/product/platform key across
    separate CLI invocations. Returns the streak after this update (0 means
    this run succeeded or reset a prior streak). Best-effort: failures are
    logged, never raised.

    This is what an escalation path looks like for a single-run-at-a-time
    pipeline with no independent monitoring loop: the fact that "this exact
    combination failed 3 times in a row" only exists if something remembers
    across runs, so it is stored here rather than recomputed from logs.
    """
    try:
        data = _read_history_file(history_path)
        streaks = data.get(_FAILURE_STREAK_NAMESPACE)
        if not isinstance(streaks, dict):
            streaks = {}
        key = history_key(brand, product, platform)
        streak = 0 if succeeded else int(streaks.get(key, 0) or 0) + 1
        streaks[key] = streak
        data[_FAILURE_STREAK_NAMESPACE] = streaks

        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return streak
    except Exception as exc:
        logger.warning("Failed to record run outcome at %s: %s", history_path, exc)
        return 0
