from __future__ import annotations

import json
import math
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from .config_sources import env_first


AGENT_NAME = "Blog Audit Agent"
AGENT_OWNER = "Muzammil Khan"
JOB_TYPE = "test"
WEBSITE = "unknown"
WEBSITE_SECTION = "Blog"
ITEM_NAME = "Blog Posts"
PLATFORM = "All"
DEFAULT_METRICS_ENDPOINT = "https://metrics-api.aspose.app/agents"
METRICS_TARGET = "aspose_metrics_api"
DEFAULT_METRICS_API_RETRIES = 2
DEFAULT_METRICS_API_TIMEOUT_SECONDS = 30.0


def normalized_metrics_payload(metrics: dict[str, Any]) -> dict[str, Any]:
    llm_metrics = metrics.get("llm") or {}
    items_discovered = nonnegative_int(value_with_fallback(metrics, "items_discovered", "markdown_files_scanned"))
    items_failed = nonnegative_int(metrics.get("items_failed"))
    items_succeeded = nonnegative_int(metrics.get("items_succeeded") if "items_succeeded" in metrics else max(items_discovered - items_failed, 0))
    duration_seconds = nonnegative_float(metrics.get("duration_seconds"))
    run_duration_ms = nonnegative_float(metrics.get("run_duration_ms") if "run_duration_ms" in metrics else duration_seconds * 1000)
    return {
        "timestamp": nonempty_string(metrics.get("timestamp"), default=datetime.now(timezone.utc).isoformat()),
        "agent_name": nonempty_string(metrics.get("agent_name"), default=AGENT_NAME),
        "agent_owner": nonempty_string(metrics.get("agent_owner"), default=AGENT_OWNER),
        "job_type": nonempty_string(metrics_job_type(), metrics.get("job_type"), default=JOB_TYPE),
        "run_id": nonempty_string(metrics.get("run_id"), default=str(uuid4())),
        "status": nonempty_string(metrics.get("status"), default="success"),
        "product": nonempty_string(metrics.get("product"), metrics.get("product_name"), metrics.get("blog_name"), default="Unknown product"),
        "platform": nonempty_string(metrics.get("platform"), default=PLATFORM),
        "website": nonempty_string(metrics.get("website"), default=WEBSITE),
        "website_section": nonempty_string(metrics.get("website_section"), default=WEBSITE_SECTION),
        "item_name": nonempty_string(metrics.get("item_name"), default=ITEM_NAME),
        "items_discovered": items_discovered,
        "items_failed": items_failed,
        "items_succeeded": items_succeeded,
        "run_duration_ms": run_duration_ms,
        "token_usage": nonnegative_int(metrics.get("token_usage") if "token_usage" in metrics else llm_metrics.get("total_tokens")),
        "api_calls_count": nonnegative_int(metrics.get("api_calls_count") if "api_calls_count" in metrics else llm_metrics.get("api_calls")),
    }


def send_metrics_api(metrics: dict[str, Any], log: Callable[[str], None] | None = None) -> list[dict[str, Any]]:
    payload = normalized_metrics_payload(metrics)
    url = metrics_api_url()
    api_key = metrics_api_key()
    if not api_key:
        if log:
            log("Metrics API sending skipped; set MUZAMMIL_KHAN_METRICS_API_KEY to enable delivery.")
        return [{"target": METRICS_TARGET, "sent": False, "status": "skipped", "reason": "missing_api_key"}]
    if log:
        log(f"Metrics API payload: {json_for_log(payload)}")
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
            log(f"Metrics API sent: delivery={delivery['status']}; status={response['status_code']}; response={json_text_for_log(response['response_body'])}")
        return [result]
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
        # A 2xx response carrying an "id" is the stored record echoed back. Its
        # "status" field is the *agent run* status we submitted, not a delivery
        # status, so a failed run would otherwise be misread as a failed POST.
        if parsed.get("id") is not None and not parsed_error:
            return {"status": "success", "reason": ""}
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


def value_with_fallback(metrics: dict[str, Any], preferred: str, fallback: str) -> Any:
    return metrics[preferred] if preferred in metrics else metrics.get(fallback)


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
