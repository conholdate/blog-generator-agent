from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import requests

from agent_engine.blog_keyword_analyzer.tools.normalization import canonical_platform_label, normalize_platform_family

def canonicalize_platform(value: Optional[str]) -> str:
    return normalize_platform_family(value)


def platform_display(value: Optional[str]) -> str:
    return canonical_platform_label(value)

def _post_json_best_effort(url: str, token: str, payload: dict[str, Any], debug: bool = False) -> None:
    """Best-effort POST; never raises."""
    if not url or not token:
        return
    try:
        resp = requests.post(url, params={"token": token}, json=payload, timeout=5)
        if debug:
            print(f"[metrics:{payload.get('stage','')}] {resp.status_code} {resp.text[:200]!r}")
    except Exception as exc:
        if debug:
            print(f"[metrics:{payload.get('stage','')}] Failed to send: {exc!r}")


def send_stage_metrics(
    *,
    settings: Any,
    run_id: str,
    stage: str,
    stage_status: str,
    req: Any,  # RunRequest
    platform: Optional[str],
    website: str,
    section: str,
    run_duration_ms: int,
    stage_duration_ms: int,
    item_name: str,
    items_discovered: int,
    items_succeeded: int,
    items_failed: int,
    llm_requests: int = 0,
    llm_prompt_tokens: int = 0,
    llm_completion_tokens: int = 0,
    llm_total_tokens: int = 0,
    extra_fields: Optional[dict[str, Any]] = None,
) -> None:
    """
    Sends ONE stage payload to BOTH external + internal webhook URLs (best-effort).
    """
    if not (getattr(settings, "METRICS_WEBHOOK_URL", "") and getattr(settings, "METRICS_TOKEN", "")):
        return

    platform_label = platform_display(platform)
    PKT_TZ = timezone(timedelta(hours=5))

    payload: dict[str, Any] = {
        "timestamp": datetime.now(PKT_TZ).isoformat(),
        "agent_name": settings.METRICS_AGENT_NAME,
        "agent_owner": settings.METRICS_AGENT_OWNER,
        "job_type": stage,
        "run_id": run_id,
        "status": stage_status,     # stage-level
        "product": req.product,
        "platform": platform_label or "",
        "website": website,
        "website_section": section,
        "item_name": item_name,
        "items_discovered": int(items_discovered),
        "items_succeeded": int(items_succeeded),
        "items_failed": int(items_failed),
        "run_duration_ms": int(stage_duration_ms),
        "api_calls_count": int(llm_requests),
        # "llm_prompt_tokens": int(llm_prompt_tokens),
        # "llm_completion_tokens": int(llm_completion_tokens),
        "token_usage": int(llm_total_tokens),
        # "run_duration_ms": int(run_duration_ms),
        # "stage_duration_ms": int(stage_duration_ms),
    }
    if extra_fields:
        payload.update(extra_fields)

    metrics_url = getattr(settings, "METRICS_WEBHOOK_URL", "")
    metrics_token = getattr(settings, "METRICS_TOKEN", "")

    _post_json_best_effort(metrics_url, metrics_token, payload, debug=bool(getattr(settings, "DEBUG", False)))

    int_url = getattr(settings, "INT_METRICS_WEBHOOK_URL", "")
    int_token = getattr(settings, "INT_METRICS_TOKEN", "")
    if int_url and int_token:
        payload_internal = dict(payload)
        payload_internal["run_env"] = "PROD"
        _post_json_best_effort(int_url, int_token, payload_internal, debug=bool(getattr(settings, "DEBUG", False)))
