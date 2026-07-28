from __future__ import annotations

import json
import math
import os
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

AGENT_NAME = "Release Notes Blog Generator"
AGENT_OWNER = "Muzammil Khan"
JOB_TYPE = "Blog Post Generation"
WEBSITE = "aspose.com"
WEBSITE_SECTION = "Blog"
ITEM_NAME = "Blog Post"
PLATFORM = "Unknown platform"
DEFAULT_METRICS_ENDPOINT = "https://metrics-api.aspose.app/agents"
METRICS_TARGET = "aspose_metrics_api"
DEFAULT_METRICS_API_RETRIES = 2
DEFAULT_METRICS_API_TIMEOUT_SECONDS = 30.0

_DOTENV_LOADED = False


def normalized_metrics_payload(metrics: dict[str, Any]) -> dict[str, Any]:
    items_discovered = nonnegative_int(metrics.get("items_discovered"))
    items_failed = nonnegative_int(metrics.get("items_failed"))
    items_succeeded = nonnegative_int(
        metrics.get("items_succeeded") if "items_succeeded" in metrics else max(items_discovered - items_failed, 0)
    )
    duration_seconds = nonnegative_float(metrics.get("duration_seconds"))
    run_duration_ms = nonnegative_float(
        metrics.get("run_duration_ms") if "run_duration_ms" in metrics else duration_seconds * 1000
    )
    return {
        "timestamp": nonempty_string(metrics.get("timestamp"), default=datetime.now(timezone.utc).isoformat()),
        "agent_name": nonempty_string(metrics.get("agent_name"), default=AGENT_NAME),
        "agent_owner": nonempty_string(metrics.get("agent_owner"), default=AGENT_OWNER),
        "job_type": nonempty_string(metrics_job_type(), metrics.get("job_type"), default=JOB_TYPE),
        "run_id": nonempty_string(metrics.get("run_id"), default=str(uuid4())),
        "status": nonempty_string(metrics.get("status"), default="success"),
        "product": nonempty_string(metrics.get("product"), default="Unknown product"),
        "platform": nonempty_string(metrics.get("platform"), default=PLATFORM),
        "website": nonempty_string(metrics.get("website"), default=WEBSITE),
        "website_section": nonempty_string(metrics.get("website_section"), default=WEBSITE_SECTION),
        "item_name": nonempty_string(metrics.get("item_name"), default=ITEM_NAME),
        "items_discovered": items_discovered,
        "items_failed": items_failed,
        "items_succeeded": items_succeeded,
        "run_duration_ms": run_duration_ms,
        "token_usage": nonnegative_int(metrics.get("token_usage")),
        "api_calls_count": nonnegative_int(metrics.get("api_calls_count")),
    }


def metrics_enabled() -> bool:
    """Best-effort delivery is on by default; set METRICS_ENABLED=false to opt out.
    Delivery still no-ops (see send_metrics_api) when no API key is configured.
    """
    load_dotenv()
    return str(env_first("METRICS_ENABLED") or "true").strip().lower() not in {"0", "false", "no", "off"}


def send_metrics_api(metrics: dict[str, Any], log: Callable[[str], None] | None = None) -> list[dict[str, Any]]:
    load_dotenv()
    payload = normalized_metrics_payload(metrics)
    url = metrics_api_url()
    api_key = metrics_api_key()
    if log:
        log(f"Metrics API payload: {json_for_log(payload)}")
    if not api_key:
        if log:
            log("Metrics API sending skipped; set MUZAMMIL_KHAN_METRICS_API_KEY to enable delivery.")
        return [{"target": METRICS_TARGET, "sent": False, "status": "skipped", "reason": "missing_api_key"}]
    try:
        response = put_json(url, api_key, payload)
        delivery = classify_metrics_api_response(METRICS_TARGET, response)
        result = {
            "target": METRICS_TARGET,
            "sent": True,
            "status": delivery["status"],
            "status_code": response["status_code"],
            "response_body": response["response_body"],
            "attempts": response.get("attempts", 1),
            "reason": delivery["reason"],
        }
        if log:
            log(
                f"Metrics API sent: delivery={delivery['status']}; status={response['status_code']}; "
                f"response={json_text_for_log(response['response_body'])}"
            )
        return [result]
    except Exception as exc:
        if log:
            log(f"Metrics API failed: {exc}")
        return [{"target": METRICS_TARGET, "sent": False, "status": "failed", "reason": str(exc)}]


def send_run_metrics(
    *,
    run_id: str,
    platform: str,
    product: str,
    items_discovered: int,
    items_succeeded: int,
    items_failed: int,
    duration_seconds: float,
    api_calls_count: int = 0,
    token_usage: int = 0,
    log: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    """Sends ONE metrics payload for the whole pipeline run, aggregated across every
    topic processed (regardless of how many blog posts that run produced), instead
    of one payload per topic (best-effort, never raises).
    """
    if items_discovered == 0:
        status = "no_topics"
    elif items_failed == 0:
        status = "success"
    elif items_succeeded == 0:
        status = "failed"
    else:
        status = "partial_failure"
    metrics = {
        "run_id": run_id,
        "status": status,
        "product": product,
        "platform": platform,
        "items_discovered": items_discovered,
        "items_succeeded": items_succeeded,
        "items_failed": items_failed,
        "duration_seconds": duration_seconds,
        "token_usage": token_usage,
        "api_calls_count": api_calls_count,
    }
    if not metrics_enabled():
        if log:
            log(
                "Metrics API sending skipped (METRICS_ENABLED=false); payload would have been: "
                f"{json_for_log(normalized_metrics_payload(metrics))}"
            )
        return [{"target": METRICS_TARGET, "sent": False, "status": "skipped", "reason": "disabled_by_env"}]
    try:
        return send_metrics_api(metrics, log)
    except Exception as exc:
        if log:
            log(f"Metrics API failed: {exc}")
        return [{"target": METRICS_TARGET, "sent": False, "status": "failed", "reason": str(exc)}]


def put_json(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Api-Key": api_key,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8"),
        headers=headers,
        method="PUT",
    )
    retries = metrics_api_retries()
    timeout = metrics_api_timeout_seconds()
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return {
                    "status_code": int(getattr(response, "status", 200) or 200),
                    "response_body": response.read().decode("utf-8", errors="replace"),
                    "attempts": attempt + 1,
                }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body[:300]}") from exc
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"Metrics API request failed after {retries + 1} attempt(s): {last_error}") from last_error


def classify_metrics_api_response(target: str, response: dict[str, Any]) -> dict[str, str]:
    status_code = int(response.get("status_code") or 0)
    body = str(response.get("response_body") or "").strip()
    lowered = body.lower()
    if status_code < 200 or status_code >= 300:
        return {"status": "failed", "reason": f"http_status_{status_code}"}
    if not body:
        return {"status": "success", "reason": ""}
    parsed = parse_response_json(body)
    if isinstance(parsed, dict):
        parsed_status = parsed.get("status")
        parsed_error = parsed.get("error") or parsed.get("message")
        if isinstance(parsed_status, int) and parsed_status >= 400:
            return {"status": "failed", "reason": str(parsed_error or f"metrics_api_status_{parsed_status}")}
        if str(parsed_status).lower() in {"error", "failed", "failure", "unauthorized", "forbidden"}:
            return {"status": "failed", "reason": str(parsed_error or parsed_status)}
        if parsed_error:
            return {"status": "failed", "reason": str(parsed_error)}
        return {"status": "success", "reason": ""}
    if lowered.startswith("error") or "unauthorized" in lowered or "forbidden" in lowered:
        return {"status": "failed", "reason": body[:300]}
    return {"status": "success", "reason": ""}


def parse_response_json(body: str) -> Any:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def json_for_log(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def json_text_for_log(body: str) -> str:
    parsed = parse_response_json(body)
    if parsed is None:
        return body
    return json.dumps(parsed, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def metrics_api_retries() -> int:
    raw = env_first("METRICS_API_RETRIES")
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            return DEFAULT_METRICS_API_RETRIES
    return DEFAULT_METRICS_API_RETRIES


def metrics_api_timeout_seconds() -> float:
    raw = env_first("METRICS_API_TIMEOUT_SECONDS")
    if raw:
        try:
            return max(1.0, float(raw))
        except ValueError:
            return DEFAULT_METRICS_API_TIMEOUT_SECONDS
    return DEFAULT_METRICS_API_TIMEOUT_SECONDS


def metrics_api_url() -> str:
    return env_first("METRICS_API_URL", "METRICS_ENDPOINT", "ASPOSE_METRICS_API_URL") or DEFAULT_METRICS_ENDPOINT


def metrics_api_key() -> str:
    return env_first("MUZAMMIL_KHAN_METRICS_API_KEY", "METRICS_API_KEY", "ASPOSE_METRICS_API_KEY")


def metrics_job_type() -> str:
    return env_first("METRICS_JOB_TYPE")


def nonempty_string(*values: Any, default: str) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def nonnegative_int(value: Any, default: int = 0) -> int:
    try:
        number = float(value)
        if not math.isfinite(number):
            return default
        return max(0, int(number))
    except (TypeError, ValueError, OverflowError):
        return default


def nonnegative_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if not math.isfinite(number):
            return default
        return max(0.0, number)
    except (TypeError, ValueError, OverflowError):
        return default


def env_first(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""


def load_dotenv(path: str | Path | None = None) -> None:
    """Minimal, dependency-free .env loader so this module works standalone
    (mirrors the sibling agents' metrics_api.py) instead of depending on the
    pipeline's pydantic-settings config being loaded first.
    """
    global _DOTENV_LOADED
    if path is None and _DOTENV_LOADED:
        return
    candidates = [Path(path)] if path else [Path.cwd() / ".env"]
    for candidate in candidates:
        if not candidate.exists():
            continue
        for raw in candidate.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            os.environ[key] = value
    if path is None:
        _DOTENV_LOADED = True
