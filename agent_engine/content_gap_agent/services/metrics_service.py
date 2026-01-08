# content_gap_agent/services/metrics_service.py
"""
MetricsService - Records and sends metrics to a remote endpoint.

Tracks pipeline execution metrics including:
- Run duration
- Items discovered/succeeded/failed
- Product/platform/step information
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from ..settings import Settings, load_settings

logger = logging.getLogger(__name__)


@dataclass
class MetricsRecord:
    """Represents a single metrics record to be sent to the endpoint."""
    timestamp: str
    agent_name: str
    agent_owner: str
    job_type: str
    run_id: str
    status: str  # "success", "failure", "partial"
    product: str
    platform: str
    website: str
    website_section: str
    item_name: str  # Step name: index, coverage, semantic-coverage, etc.
    items_discovered: int
    items_failed: int
    items_succeeded: int
    run_duration_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "agent_name": self.agent_name,
            "agent_owner": self.agent_owner,
            "job_type": self.job_type,
            "run_id": self.run_id,
            "status": self.status,
            "product": self.product,
            "platform": self.platform,
            "website": self.website,
            "website_section": self.website_section,
            "item_name": self.item_name,
            "items_discovered": self.items_discovered,
            "items_failed": self.items_failed,
            "items_succeeded": self.items_succeeded,
            "run_duration_ms": self.run_duration_ms,
        }


@dataclass
class MetricsContext:
    """Context for tracking metrics during a pipeline run."""
    run_id: str
    brand: str
    product: str
    platform: str
    step: str
    start_time_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    items_discovered: int = 0
    items_succeeded: int = 0
    items_failed: int = 0

    def record_discovered(self, count: int) -> None:
        """Record number of items discovered."""
        self.items_discovered = count

    def record_success(self, count: int = 1) -> None:
        """Record successful items."""
        self.items_succeeded += count

    def record_failure(self, count: int = 1) -> None:
        """Record failed items."""
        self.items_failed += count

    def get_duration_ms(self) -> int:
        """Get duration since start in milliseconds."""
        return int(time.time() * 1000) - self.start_time_ms


class MetricsService:
    """
    Service for recording and sending pipeline metrics.

    Usage:
        metrics = MetricsService()
        ctx = metrics.start_step("aspose", "cells", "net", "index")
        try:
            # ... do work ...
            ctx.record_discovered(10)
            ctx.record_success(8)
            ctx.record_failure(2)
            metrics.complete_step(ctx, success=True)
        except Exception as e:
            metrics.complete_step(ctx, success=False, error=str(e))
    """

    # Map step names to job types for clarity
    STEP_JOB_TYPES: Dict[str, str] = {
        "coverage": "API Coverage Analysis",
        "analyze": "AI Gap Analysis",
    }

    # Semantic coverage/analyze cases map to specific job types
    SEMANTIC_COVERAGE_JOB_TYPE = "Semantic Coverage Analysis"
    SEMANTIC_ANALYZE_JOB_TYPE = "Semantic Gap Analysis"

    # Valid semantic cases (item_name will be just the case)
    SEMANTIC_CASES = {"docs_to_blogs", "docs_to_tutorials", "blogs_to_blogs"}

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or load_settings()
        self._enabled = self._settings.metrics_enabled
        self._endpoint = self._settings.metrics_endpoint
        self._token = self._settings.metrics_token

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._endpoint)

    def generate_run_id(self, step: str) -> str:
        """Generate a unique run ID for a pipeline step."""
        short_uuid = uuid.uuid4().hex[:8]
        return f"bta_{step}_{short_uuid}"

    def start_step(
        self,
        brand: str,
        product: str,
        platform: str,
        step: str,
        run_id: Optional[str] = None,
    ) -> MetricsContext:
        """
        Start tracking metrics for a pipeline step.

        Args:
            brand: Brand/blog name (e.g., "aspose")
            product: Product name (e.g., "cells")
            platform: Platform name (e.g., "net")
            step: Step name (e.g., "index", "coverage", "semantic-coverage")
            run_id: Optional run ID (auto-generated if not provided)

        Returns:
            MetricsContext for tracking metrics during the step
        """
        if run_id is None:
            run_id = self.generate_run_id(step)

        logger.debug("Starting metrics for step=%s run_id=%s", step, run_id)

        return MetricsContext(
            run_id=run_id,
            brand=brand,
            product=product,
            platform=platform,
            step=step,
        )

    def complete_step(
        self,
        ctx: MetricsContext,
        success: bool = True,
        error: Optional[str] = None,
    ) -> Optional[MetricsRecord]:
        """
        Complete a step and send metrics to the endpoint.

        Args:
            ctx: MetricsContext from start_step()
            success: Whether the step completed successfully
            error: Optional error message if failed

        Returns:
            MetricsRecord that was sent (or None if metrics disabled)
        """
        if not self.enabled:
            logger.debug("Metrics disabled, skipping send")
            return None

        logger.info(f"Pipeline Step: {ctx.step}")
        # Determine status
        if not success:
            status = "failure"
        elif ctx.items_failed > 0:
            status = "partial"
        else:
            status = "success"

        # Build job_type and item_name from step
        # Handle semantic coverage/analyze cases: "semantic-coverage:docs_to_blogs" -> job_type="Semantic Coverage Analysis", item_name="docs_to_blogs"
        if ctx.step.startswith("semantic-coverage:"):
            job_type = self.SEMANTIC_COVERAGE_JOB_TYPE
            item_name = ctx.step.split(":", 1)[1]  # Extract the case
        elif ctx.step.startswith("semantic-analyze:"):
            job_type = self.SEMANTIC_ANALYZE_JOB_TYPE
            item_name = ctx.step.split(":", 1)[1]  # Extract the case
        else:
            job_type = self.STEP_JOB_TYPES.get(ctx.step, f"Pipeline Step: {ctx.step}")
            item_name = ctx.step

        # Create record
        record = MetricsRecord(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            agent_name=self._settings.metrics_agent_name,
            agent_owner=self._settings.metrics_agent_owner,
            job_type=job_type,
            run_id=ctx.run_id,
            status=status,
            product=f"{ctx.brand.capitalize()}.{ctx.product.capitalize()}",
            platform=ctx.platform.upper() if ctx.platform else "ALL",
            website=self._settings.metrics_website,
            website_section=self._settings.metrics_website_section,
            item_name=item_name,
            items_discovered=ctx.items_discovered,
            items_failed=ctx.items_failed,
            items_succeeded=ctx.items_succeeded,
            run_duration_ms=ctx.get_duration_ms(),
        )

        # Send to endpoint
        self._send_metrics(record)

        return record

    def _send_metrics(self, record: MetricsRecord) -> bool:
        """
        Send metrics record to the endpoint.

        Returns True if successful, False otherwise.
        """
        if not self._endpoint:
            logger.warning("No metrics endpoint configured")
            return False

        payload = record.to_dict()

        try:
            logger.info(
                "Sending metrics: run_id=%s step=%s status=%s duration=%dms",
                record.run_id,
                record.item_name,
                record.status,
                record.run_duration_ms,
            )
            logger.debug("Metrics payload: %s", json.dumps(payload, indent=2))

            response = requests.post(
                self._endpoint,
                params={"token": self._token},
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code in (200, 201, 302):
                logger.info("Metrics sent successfully: %s", response.status_code)
                return True
            else:
                logger.warning(
                    "Metrics endpoint returned status %d: %s",
                    response.status_code,
                    response.text[:200] if response.text else "(no body)",
                )
                return False

        except requests.exceptions.Timeout:
            logger.warning("Metrics send timed out after 30s")
            return False
        except requests.exceptions.RequestException as e:
            logger.warning("Failed to send metrics: %s", e)
            return False
        except Exception as e:
            logger.exception("Unexpected error sending metrics: %s", e)
            return False

    def record_simple(
        self,
        brand: str,
        product: str,
        platform: str,
        step: str,
        items_discovered: int = 0,
        items_succeeded: int = 0,
        items_failed: int = 0,
        duration_ms: int = 0,
        success: bool = True,
    ) -> Optional[MetricsRecord]:
        """
        Convenience method to record metrics in one call.

        Useful when you already have all the metrics data and don't need
        the start/complete pattern.
        """
        if not self.enabled:
            return None

        ctx = self.start_step(brand, product, platform, step)
        ctx.items_discovered = items_discovered
        ctx.items_succeeded = items_succeeded
        ctx.items_failed = items_failed
        # Override start time to match provided duration
        ctx.start_time_ms = int(time.time() * 1000) - duration_ms

        return self.complete_step(ctx, success=success)


# Singleton instance for convenience
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get the global MetricsService instance."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
