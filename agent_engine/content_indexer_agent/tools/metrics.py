# metrics.py
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .logging_utils import get_logger
from .normalization import normalize_product_display_name

log = get_logger("cg.metrics")


def _load_send_metrics_api():
    """Load the shared metrics sender only when metrics delivery is actually needed.

    Importing the transport eagerly at module load time would break every
    caller (including both CLI entry points) whenever it is absent, not just
    metrics delivery. Returns None if it can't be found so callers can degrade
    instead of crashing on import. A missing third-party dependency still
    raises, since that is a broken install rather than absent metrics config.
    """
    try:
        from ...metrics_api import send_metrics_api
    except ModuleNotFoundError as exc:
        if exc.name == "agent_engine.metrics_api":
            return None
        raise
    return send_metrics_api


def _clean_optional(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_z() -> str:
    # Example: "2025-12-15T10:12:45.123Z"
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond/1000):03d}Z"


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
    Reads agent metadata from Settings and sends through the shared metrics API.

    Only reporting policy lives here (whether metrics are enabled/required, and
    who the run is attributed to). Delivery config -- endpoint, credential,
    timeout, retries -- is owned by ``agent_engine.metrics_api``, which reads its
    own environment variables. Do not re-read webhook URLs or tokens here.
    """

    def __init__(self, *, settings: Any) -> None:
        self.enabled: bool = bool(getattr(settings, "METRICS_ENABLED", True))
        self.required: bool = bool(getattr(settings, "METRICS_REQUIRED", False))

        self.agent_name: str = _clean_optional(getattr(settings, "METRICS_AGENT_NAME", ""))
        self.agent_owner: str = _clean_optional(getattr(settings, "METRICS_AGENT_OWNER", ""))

    def _handle_send_failure(self, message: str, exc: Exception | None = None) -> None:
        if exc is not None:
            log.warning("%s: %s", message, exc)
        else:
            log.warning("%s", message)
        if self.required:
            raise RuntimeError(message) from exc

    def send(self, payload: MetricsPayload) -> None:
        if not self.enabled:
            print("[metrics] disabled (METRICS_ENABLED=False). Not sending.")
            return

        data = asdict(payload)
        if data.get("extra") is None:
            data["extra"] = {}

        # Remove job_type if None (keeps payload clean)
        if data.get("job_type") is None:
            data.pop("job_type", None)

        send_metrics_api = _load_send_metrics_api()
        if send_metrics_api is None:
            self._handle_send_failure("Metrics API unavailable (hugo_blog_audit_agent not installed); skipping delivery")
            return

        log.info("Metrics API payload (about to send):\n%s", json.dumps(data, ensure_ascii=False, indent=2))
        try:
            deliveries = send_metrics_api(
                data,
                log.info,
            )
        except Exception as e:
            print("[metrics] send failed:", repr(e))
            self._handle_send_failure("Metrics API send failed", e)
            return

        # "skipped" means delivery was never attempted because no endpoint or
        # credential is configured. That is the normal state for local runs, so
        # it stays informational unless the operator declared metrics required.
        skipped = [delivery for delivery in deliveries if delivery.get("status") == "skipped"]
        if skipped:
            reasons = ", ".join(str(item.get("reason") or "unknown") for item in skipped)
            if self.required:
                self._handle_send_failure(f"Metrics API delivery skipped: {reasons}")
            else:
                log.info("Metrics API delivery skipped: %s", reasons)

        failed = [
            delivery
            for delivery in deliveries
            if delivery.get("status") not in {"success", "skipped"}
        ]
        if failed:
            reasons = ", ".join(str(item.get("reason") or item.get("status") or "unknown") for item in failed)
            self._handle_send_failure(f"Metrics API delivery failed: {reasons}")


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
