from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable

from .llm import env_first, load_dotenv


AGENT_NAME = "Blog Audit Agent"
AGENT_OWNER = "Muzammil Khan"
JOB_TYPE = "Blog Audit"
WEBSITE = ""
WEBSITE_SECTION = "Blog"
ITEM_NAME = "Blog Posts"
PLATFORM = "All"
DEFAULT_WEBHOOK_RETRIES = 2
DEFAULT_WEBHOOK_TIMEOUT_SECONDS = 30.0


def normalized_metrics_payload(metrics: dict[str, Any]) -> dict[str, Any]:
    llm_metrics = metrics.get("llm") or {}
    items_discovered = int(metrics.get("items_discovered") or metrics.get("markdown_files_scanned") or 0)
    items_failed = int(metrics.get("items_failed") or 0)
    items_succeeded = int(metrics.get("items_succeeded") or max(items_discovered - items_failed, 0))
    duration_seconds = float(metrics.get("duration_seconds") or 0)
    return {
        "timestamp": metrics.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "agent_name": metrics.get("agent_name") or AGENT_NAME,
        "agent_owner": metrics.get("agent_owner") or AGENT_OWNER,
        "job_type": metrics.get("job_type") or JOB_TYPE,
        "run_id": metrics.get("run_id") or "",
        "status": metrics.get("status") or "success",
        "product": metrics.get("product") or metrics.get("product_name") or "",
        "platform": metrics.get("platform") or PLATFORM,
        "website": metrics.get("website") or WEBSITE,
        "website_section": metrics.get("website_section") or WEBSITE_SECTION,
        "item_name": metrics.get("item_name") or ITEM_NAME,
        "items_discovered": items_discovered,
        "items_failed": items_failed,
        "items_succeeded": items_succeeded,
        "run_duration_ms": int(metrics.get("run_duration_ms") or round(duration_seconds * 1000)),
        "token_usage": int(metrics.get("token_usage") or llm_metrics.get("total_tokens") or 0),
        "api_calls_count": int(metrics.get("api_calls_count") or llm_metrics.get("api_calls") or 0),
        "run_env": metrics.get("run_env") or metrics_run_env(),
    }


def send_metrics_webhooks(metrics: dict[str, Any], log: Callable[[str], None] | None = None) -> list[dict[str, Any]]:
    load_dotenv()
    payload = normalized_metrics_payload(metrics)
    endpoints = [
        ("prod", os.environ.get("METRICS_WEBHOOK_URL_PROD", ""), os.environ.get("TOKEN_FOR_PROD", "")),
        ("team", os.environ.get("METRICS_WEBHOOK_URL_TEAM", ""), os.environ.get("TOKEN_FOR_TEAM", "")),
    ]
    deliveries = []
    for name, url, token in endpoints:
        if not url:
            deliveries.append({"target": name, "sent": False, "status": "skipped", "reason": "missing_url"})
            continue
        try:
            response = post_json(url, token, payload)
            delivery = classify_webhook_response(name, response)
            deliveries.append({
                "target": name,
                "sent": True,
                "status": delivery["status"],
                "status_code": response["status_code"],
                "response_body": response["response_body"],
                "attempts": response.get("attempts", 1),
                "reason": delivery["reason"],
            })
            if log:
                log(f"Metrics webhook sent: {name}; delivery={delivery['status']}; status={response['status_code']}; response={response['response_body'][:120]}")
        except Exception as exc:
            deliveries.append({"target": name, "sent": False, "status": "failed", "reason": str(exc)})
            if log:
                log(f"Metrics webhook failed for {name}: {exc}")
    return deliveries


def post_json(url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Webhook-Token"] = token
    request = urllib.request.Request(
        webhook_url_with_token(url, token),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    retries = metrics_webhook_retries()
    timeout = metrics_webhook_timeout_seconds()
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return {
                    "status_code": int(getattr(response, "status", 200) or 200),
                    "response_body": response.read().decode("utf-8", errors="replace")[:1000],
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
    raise RuntimeError(f"Webhook request failed after {retries + 1} attempt(s): {last_error}") from last_error


def webhook_url_with_token(url: str, token: str) -> str:
    if not token:
        return url
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [(key, value) for key, value in query if key != "token"]
    query.append(("token", token))
    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        urllib.parse.urlencode(query),
        parsed.fragment,
    ))


def classify_webhook_response(target: str, response: dict[str, Any]) -> dict[str, str]:
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
            return {"status": "failed", "reason": str(parsed_error or f"webhook_status_{parsed_status}")}
        if str(parsed_status).lower() in {"error", "failed", "failure", "unauthorized", "forbidden"}:
            return {"status": "failed", "reason": str(parsed_error or parsed_status)}
        if parsed_error and any(term in str(parsed_error).lower() for term in ["invalid token", "unauthorized", "forbidden", "error"]):
            return {"status": "failed", "reason": str(parsed_error)}
        return {"status": "success", "reason": ""}
    if lowered.startswith("error") or "invalid token" in lowered or "unauthorized" in lowered or "forbidden" in lowered:
        return {"status": "failed", "reason": body[:300]}
    return {"status": "success", "reason": ""}


def parse_response_json(body: str) -> Any:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def metrics_webhook_retries() -> int:
    raw = env_first("METRICS_WEBHOOK_RETRIES", "WEBHOOK_RETRIES")
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            return DEFAULT_WEBHOOK_RETRIES
    return DEFAULT_WEBHOOK_RETRIES


def metrics_webhook_timeout_seconds() -> float:
    raw = env_first("METRICS_WEBHOOK_TIMEOUT_SECONDS", "WEBHOOK_TIMEOUT_SECONDS")
    if raw:
        try:
            return max(1.0, float(raw))
        except ValueError:
            return DEFAULT_WEBHOOK_TIMEOUT_SECONDS
    return DEFAULT_WEBHOOK_TIMEOUT_SECONDS


def metrics_run_env() -> str:
    value = env_first("METRICS_RUN_ENV", "RUN_ENV").upper()
    if value in {"PROD", "DEV"}:
        return value
    return "PROD" if os.environ.get("METRICS_WEBHOOK_URL_PROD") else "DEV"
