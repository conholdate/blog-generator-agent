from __future__ import annotations
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from agent_engine.config_sources import get_agent_metrics_config
from agent_engine.hugo_blog_audit_agent.metrics_api import send_metrics_api
from agent_engine.blog_keyword_analyzer.tools.normalization import canonical_platform_label, normalize_platform_family


def _metrics_enabled() -> bool:
    return str(os.getenv("METRICS_ENABLED", "true")).strip().lower() not in {"0", "false", "no", "off"}


def canonicalize_platform(value: Optional[str]) -> str:
    return normalize_platform_family(value)


def platform_display(value: Optional[str]) -> str:
    return canonical_platform_label(value)

def _send_metrics_api_best_effort(payload: dict[str, Any], debug: bool = False) -> None:
    """Best-effort metrics API delivery; never raises."""
    try:
        payload_data = dict(payload)

        print("[metrics] payload before send:")
        print(json.dumps(payload_data, ensure_ascii=False, indent=2))

        deliveries = send_metrics_api(
            payload,
            None,
        )
        if debug:
            print(f"[metrics:{payload.get('stage','')}] API deliveries: {deliveries!r}")
        failed = [
            delivery
            for delivery in deliveries
            if delivery.get("status") != "success"
        ]
        if failed:
            reasons = ", ".join(str(item.get("reason") or item.get("status") or "unknown") for item in failed)
            print(f"[metrics:{payload.get('stage','')}] Metrics API delivery failed: {reasons}")
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
    Sends ONE stage payload to the metrics API (best-effort).
    """
    if not _metrics_enabled():
        print("[metrics] disabled (METRICS_ENABLED=false). Not sending stage metrics.")
        return

    metrics_cfg = get_agent_metrics_config("blog_keyword_analyzer")

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

    _send_metrics_api_best_effort(payload, debug=bool(getattr(settings, "DEBUG", False)))
