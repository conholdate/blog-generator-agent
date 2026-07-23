from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AuditResult

STATE_FILENAME = "audit-state.json"
STATE_SCHEMA_VERSION = 1


def load_previous_run_state(output_dir: Path) -> dict[str, Any]:
    """Read the state left by the previous run in this output directory.

    A missing or unreadable file means "no previous run to compare against",
    not a failure — the caller treats an empty dict as a first run.
    """
    state_path = output_dir / STATE_FILENAME
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict) or data.get("schema_version") != STATE_SCHEMA_VERSION:
        return {}
    return data


def build_current_run_state(result: AuditResult, run_id: str, generated_at: str) -> dict[str, Any]:
    posts: dict[str, Any] = {}
    for post in result.posts:
        posts[post.relative_path] = {
            "priority": int(post.scores.get("priority", 0)),
            "total_issues": len(post.issues),
            "issue_types": sorted({issue.issue_type for issue in post.issues}),
        }
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": generated_at,
        "posts": posts,
    }


def write_run_state(output_dir: Path, current_state: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / STATE_FILENAME).write_text(json.dumps(current_state, indent=2, ensure_ascii=False), encoding="utf-8")


def diff_run_state(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare this run's per-post state against the previous run's.

    Priority is capped at 100 and saturates easily, so it is not sensitive
    enough on its own once a post is already at the ceiling. Total issue
    count is unbounded and decides direction whenever priority is unchanged.
    """
    previous_posts: dict[str, Any] = previous.get("posts", {}) if previous else {}
    current_posts: dict[str, Any] = current.get("posts", {})

    previous_paths = set(previous_posts)
    current_paths = set(current_posts)

    regressed: list[dict[str, Any]] = []
    improved: list[dict[str, Any]] = []
    for path in sorted(previous_paths & current_paths):
        prev_priority = int(previous_posts[path].get("priority", 0))
        curr_priority = int(current_posts[path].get("priority", 0))
        prev_issues = int(previous_posts[path].get("total_issues", 0))
        curr_issues = int(current_posts[path].get("total_issues", 0))
        priority_delta = curr_priority - prev_priority
        issue_delta = curr_issues - prev_issues
        if priority_delta == 0 and issue_delta == 0:
            continue
        direction_delta = priority_delta if priority_delta != 0 else issue_delta
        entry = {
            "relative_path": path,
            "previous_priority": prev_priority,
            "current_priority": curr_priority,
            "priority_delta": priority_delta,
            "previous_total_issues": prev_issues,
            "current_total_issues": curr_issues,
            "issue_delta": issue_delta,
            "delta": direction_delta,
        }
        (regressed if direction_delta > 0 else improved).append(entry)

    regressed.sort(key=lambda item: item["delta"], reverse=True)
    improved.sort(key=lambda item: item["delta"])

    return {
        "has_previous_run": bool(previous),
        "previous_run_id": previous.get("run_id") if previous else None,
        "previous_generated_at": previous.get("generated_at") if previous else None,
        "new_posts": sorted(current_paths - previous_paths),
        "removed_posts": sorted(previous_paths - current_paths),
        "regressed_posts": regressed,
        "improved_posts": improved,
        "unchanged_posts": len((previous_paths & current_paths)) - len(regressed) - len(improved),
    }
