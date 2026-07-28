from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .metrics import RunMetrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    approved: bool
    reason: str
    risk_level: str = "none"


def check_external_write_policy(
    *,
    action: str,
    dry_run: bool,
    topics_count: Optional[int] = None,
    metrics: Optional["RunMetrics"] = None,
) -> PolicyDecision:
    """
    Explicit, logged approval checkpoint before an action that writes to
    shared external state (currently: appending a row to a live Google
    Sheet in live-sheet mode).

    Why this exists: previously, "should this run be allowed to happen" was
    reasoned about only at the CI layer (GitLab's `when: manual`, GitHub's
    `workflow_dispatch`) — that gates whether the whole job runs, not
    whether any specific write inside it happens. This function moves that
    one decision into the agent's own control flow instead, so it is
    explicit and recorded rather than an implicit, unconditional write once
    the job itself was allowed to start.

    Risk reasoning: `topics_count` lets the caller tell this function what
    it's actually about to write. A zero-topic run is flagged
    `risk_level="low_signal"` and still approved by default — a zero-topic
    row is *intentionally* written so an operator watching the tracking
    sheet sees the row was attempted rather than silently skipped (see
    `tests/test_runner_sheet_and_missing_modes.py::
    test_main_live_sheet_mode_runs_and_appends_output`). Blocking it would
    be guessing at a behavior change this codebase doesn't ask for. The
    real improvement is that the decision now actually inspects what it's
    approving instead of returning a uniform, uninformative "approved"
    regardless of content — the audit trail (POLICY_DECISION event) is
    genuinely risk-aware even though the action isn't gated on it (yet).

    This is deliberately not an autonomous refusal mechanism: default is
    approved (--dry-run is opt-in), so existing automated callers are
    unaffected. The value today is that the decision point now exists, is
    informed by real signal, and is auditable — the precondition for any
    future real approval logic — see
    Docs/adr/0003-ci-based-approval-gating.md.
    """
    risk_level = "low_signal" if topics_count == 0 else "none"

    if dry_run:
        decision = PolicyDecision(
            action=action, approved=False, reason="dry_run flag set", risk_level=risk_level
        )
    elif risk_level == "low_signal":
        decision = PolicyDecision(
            action=action,
            approved=True,
            reason=(
                "approved: 0 topics generated this run; writing a result row anyway "
                "for tracking visibility (intentional design, not a fallback)"
            ),
            risk_level=risk_level,
        )
    else:
        decision = PolicyDecision(
            action=action,
            approved=True,
            reason="default: no --dry-run, existing automation unaffected",
            risk_level=risk_level,
        )

    logger.info(
        "POLICY: %s %s (risk=%s, %s).",
        action,
        "approved" if decision.approved else "not performed",
        decision.risk_level,
        decision.reason,
    )

    if metrics is not None:
        metrics.add_event(
            "POLICY_DECISION",
            f"{action}: {'approved' if decision.approved else 'blocked'}",
            action=action,
            approved=decision.approved,
            reason=decision.reason,
            risk_level=decision.risk_level,
        )
    return decision
