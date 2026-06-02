# metrics.py
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from .logging_utils import get_logger
from .normalization import normalize_product_display_name

log = get_logger("cg.metrics")


def _clean_optional(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_z() -> str:
    # Example: "2025-12-15T10:12:45.123Z"
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond/1000):03d}Z"


def _looks_like_invalid_token_response(body: str) -> bool:
    text = str(body or "").strip().lower()
    return "invalid token" in text or "unauthorized" in text


def new_run_id(prefix: str = "run") -> str:
    # Example: kb_article_writer_7f2a91c0
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ------------------ Metrics helpers ------------------

@dataclass(frozen=True)
class MetricsPayload:
    """
    Payload shape exactly aligned to your required fields.
    """
    timestamp: str
    agent_name: str
    agent_owner: str
    run_id: str
    status: str  # "success" | "failed"

    # Optional classifier
    job_type: Optional[str] = None

    # Required metadata (as per your need)
    product: str = ""
    platform: str = ""
    website: str = ""
    website_section: str = ""
    item_name: str = ""

    # Counters
    items_discovered: int = 0
    items_failed: int = 0
    items_succeeded: int = 0

    # Duration
    run_duration_ms: int = 0

    # API usage
    token_usage: int = 0
    api_calls_count: int = 0

    # Extensibility (safe extra data without schema break)
    extra: Dict[str, Any] = None  # will be normalized to {} when sending


class MetricsSender:
    """
    Reads agent metadata + transport config from Settings.
    No env vars, no duplication in agent.py.
    """

    def __init__(self, *, settings: Any) -> None:
        self.enabled: bool = bool(getattr(settings, "METRICS_ENABLED", True))
        self.required: bool = bool(getattr(settings, "METRICS_REQUIRED", False))
        self.timeout_s: float = float(getattr(settings, "METRICS_TIMEOUT_S", 2.0))

        self.webhook_url: str = _clean_optional(getattr(settings, "METRICS_WEBHOOK_URL", ""))
        self.token: str = _clean_optional(getattr(settings, "METRICS_TOKEN", ""))

        self.agent_name: str = _clean_optional(getattr(settings, "METRICS_AGENT_NAME", ""))
        self.agent_owner: str = _clean_optional(getattr(settings, "METRICS_AGENT_OWNER", ""))

        self.int_webhook_url: str = _clean_optional(getattr(settings, "INT_METRICS_WEBHOOK_URL", ""))
        self.int_token: str = _clean_optional(getattr(settings, "INT_METRICS_TOKEN", ""))

    def _handle_send_failure(self, message: str, exc: Exception | None = None) -> None:
        if exc is not None:
            log.warning("%s: %s", message, exc)
        else:
            log.warning("%s", message)
        if self.required:
            raise RuntimeError(message) from exc

    def _post_metric(self, url: str, token: str, data: Dict[str, Any]) -> None:
        if not token:
            raise RuntimeError("Metrics token is empty.")
        resp = requests.post(
            url,
            params={"token": token},
            headers={"Content-Type": "application/json"},
            data=json.dumps(data, ensure_ascii=False),
            timeout=self.timeout_s,
        )
        print("[metrics] response status =", resp.status_code)
        print("[metrics] response text =", resp.text[:500])
        if resp.status_code < 200 or resp.status_code >= 300:
            raise RuntimeError(f"Metrics webhook returned status={resp.status_code}: {resp.text[:500]}")
        if _looks_like_invalid_token_response(resp.text):
            raise RuntimeError(f"Metrics webhook rejected token: {resp.text[:500]}")

    def send(self, payload: MetricsPayload) -> None:
        if not self.enabled:
            print("[metrics] disabled (METRICS_ENABLED=False). Not sending.")
            return

        if not self.webhook_url and not self.int_webhook_url:
            self._handle_send_failure("Metrics enabled, but no metrics webhooks are configured. Not sending.")
            return

        data = asdict(payload)
        if data.get("extra") is None:
            data["extra"] = {}

        # If your Apps Script expects token in JSON
        # if self.token:
        #    data["token"] = self.token

        # Remove job_type if None (keeps payload clean)
        if data.get("job_type") is None:
            data.pop("job_type", None)

        try:
            log.info("Metrics payload (about to send):\n%s", json.dumps(data, ensure_ascii=False, indent=2))
            # Aspose Metrics
            if self.webhook_url:
                self._post_metric(self.webhook_url, self.token, data)

            # Ensure run_env is present (default to PROD if missing/None)
            data.setdefault("run_env", "PROD")
            if data.get("run_env") is None:
                data["run_env"] = "PROD"

            # Blog metrics
            if self.int_webhook_url:
                self._post_metric(self.int_webhook_url, self.int_token, data)

        except Exception as e:
            print("[metrics] send failed:", repr(e))
            self._handle_send_failure("Metrics send failed", e)


class MetricsRun:
    """
    Context manager for one metric event.
    It calculates duration and sets status based on exceptions.
    You can update counters dynamically via .set_counts(...)
    """

    def __init__(
        self,
        *,
        sender: MetricsSender,
        run_id: str,
        product: str,
        platform: str,
        website: str,
        website_section: str,
        item_name: str,
        job_type: Optional[str] = None,
        items_discovered: int = 0,
        items_failed: int = 0,
        items_succeeded: int = 0,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._sender = sender
        self._t0 = 0.0

        self.run_id = run_id
        self.job_type = job_type

        self.product = normalize_product_display_name(product)
        self.platform = platform
        self.website = website
        self.website_section = website_section
        self.item_name = item_name

        self.items_discovered = int(items_discovered)
        self.items_failed = int(items_failed)
        self.items_succeeded = int(items_succeeded)
        self.token_usage = 0
        self.api_calls_count = 0

        self.extra: Dict[str, Any] = extra or {}

    def set_counts(self, *, discovered: int, succeeded: int, failed: int) -> None:
        self.items_discovered = int(discovered)
        self.items_succeeded = int(succeeded)
        self.items_failed = int(failed)

    def set_usage(self, *, token_usage: int, api_calls_count: int) -> None:
        self.token_usage = int(token_usage)
        self.api_calls_count = int(api_calls_count)

    def __enter__(self) -> "MetricsRun":
        self._t0 = time.time()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if not self._sender.enabled:
            print("[metrics] disabled (METRICS_ENABLED=False). Not sending.")
            return False

        duration_ms = int((time.time() - self._t0) * 1000)
        status = "success" if exc is None else "failed"

        payload = MetricsPayload(
            timestamp=_utc_now_z(),
            agent_name=self._sender.agent_name,
            agent_owner=self._sender.agent_owner,
            job_type=self.job_type,
            run_id=self.run_id,
            status=status,
            product=self.product,
            platform=self.platform,
            website=self.website,
            website_section=self.website_section,
            item_name=self.item_name,
            items_discovered=self.items_discovered,
            items_failed=self.items_failed,
            items_succeeded=self.items_succeeded,
            run_duration_ms=duration_ms,
            token_usage=self.token_usage,
            api_calls_count=self.api_calls_count,
            extra=self.extra,
        )

        payload_data = asdict(payload)

        print("[metrics] payload before send:")
        print(json.dumps(payload_data, ensure_ascii=False, indent=2))

        self._sender.send(payload)

        # Do not swallow exceptions
        return False
