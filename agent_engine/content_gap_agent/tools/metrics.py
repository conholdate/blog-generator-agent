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

log = get_logger("cg.metrics")


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

    # Extensibility (safe extra data without schema break)
    extra: Dict[str, Any] = None  # will be normalized to {} when sending


class MetricsSender:
    """
    Reads agent metadata + transport config from Settings.
    No env vars, no duplication in agent.py.
    """

    def __init__(self, *, settings: Any) -> None:
        self.enabled: bool = bool(getattr(settings, "METRICS_ENABLED", True))
        self.timeout_s: float = float(getattr(settings, "METRICS_TIMEOUT_S", 2.0))

        self.webhook_url: str = str(getattr(settings, "METRICS_WEBHOOK_URL", "")).strip()
        self.token: str = str(getattr(settings, "METRICS_TOKEN", "")).strip()

        self.agent_name: str = str(getattr(settings, "METRICS_AGENT_NAME", "")).strip()
        self.agent_owner: str = str(getattr(settings, "METRICS_AGENT_OWNER", "")).strip()

        self.int_webhook_url: str = str(getattr(settings, "INT_METRICS_WEBHOOK_URL", "")).strip()
        self.int_token: str = str(getattr(settings, "INT_METRICS_TOKEN", "")).strip()

    def send(self, payload: MetricsPayload) -> None:
        if not self.enabled:
            print("[metrics] disabled (METRICS_ENABLED=False). Not sending.")
            return


        data = asdict(payload)
        # if data.get("extra") is None:
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
            resp1 = requests.post(
                self.webhook_url,
                params={"token": self.token},
                headers={"Content-Type": "application/json"},
                data=json.dumps(data, ensure_ascii=False),
                timeout=self.timeout_s,
            )

            print("[metrics] response status =", resp1.status_code)
            print("[metrics] response text =", resp1.text[:500])

            # Blog metrics
            resp2 = requests.post(
                self.int_webhook_url,
                params={"token": self.int_token},
                headers={"Content-Type": "application/json"},
                data=json.dumps(data, ensure_ascii=False),
                timeout=self.timeout_s,
            )

            print("[metrics] response status =", resp2.status_code)
            print("[metrics] response text =", resp2.text[:500])

        except Exception as e:
            print("[metrics] send failed:", repr(e))
            log.debug("Metrics send failed: %s", e)


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

        self.product = product
        self.platform = platform
        self.website = website
        self.website_section = website_section
        self.item_name = item_name

        self.items_discovered = int(items_discovered)
        self.items_failed = int(items_failed)
        self.items_succeeded = int(items_succeeded)

        self.extra: Dict[str, Any] = extra or {}

    def set_counts(self, *, discovered: int, succeeded: int, failed: int) -> None:
        self.items_discovered = int(discovered)
        self.items_succeeded = int(succeeded)
        self.items_failed = int(failed)

    def __enter__(self) -> "MetricsRun":
        self._t0 = time.time()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
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
            extra=self.extra,
        )
        self._sender.send(payload)

        # Do not swallow exceptions
        return False
