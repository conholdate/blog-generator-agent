from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import requests

from agent_engine.config_sources import get_agent_metrics_config
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
        payload_data = dict(payload)

        print("[metrics] payload before send:")
        print(json.dumps(payload_data, ensure_ascii=False, indent=2))

        resp = requests.post(url, params={"token": token}, json=payload, timeout=5)
        if debug:
            print(f"[metrics:{payload.get('stage','')}] {resp.status_code} {resp.text[:200]!r}")
            print("[metrics] debug payload after send:")
    except Exception as exc:
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
    metrics_cfg = get_agent_metrics_config("blog_keyword_analyzer")
    webhooks = metrics_cfg.get("webhooks") or {}
    primary = webhooks.get("primary") or {}
    internal = webhooks.get("internal") or {}
    metrics_url = str(primary.get("url") or "").strip()
    metrics_token = str(primary.get("token") or "").strip()
    int_url = str(internal.get("url") or "").strip()
    int_token = str(internal.get("token") or "").strip()
    if not (metrics_url and metrics_token):
        return

    platform_label = platform_display(platform)
    PKT_TZ = timezone(timedelta(hours=5))
    agent_name = str(metrics_cfg.get("agent_name") or getattr(settings, "METRICS_AGENT_NAME", "Keyword Analyzer"))
    agent_owner = str(metrics_cfg.get("agent_owner") or getattr(settings, "METRICS_AGENT_OWNER", ""))

    payload: dict[str, Any] = {
        "timestamp": datetime.now(PKT_TZ).isoformat(),
        "agent_name": agent_name,
        "agent_owner": agent_owner,
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

    _post_json_best_effort(metrics_url, metrics_token, payload, debug=bool(getattr(settings, "DEBUG", False)))

    if int_url and int_token:
        payload_internal = dict(payload)
        payload_internal["run_env"] = "PROD"
        _post_json_best_effort(int_url, int_token, payload_internal, debug=bool(getattr(settings, "DEBUG", False)))
