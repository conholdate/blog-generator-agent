from __future__ import annotations

from dataclasses import dataclass, field

from ..models.security import EngineeringSignals, SignalStatus

_CRITICAL_FIELD_LABELS = {
    "tracked_secrets": "tracked secrets",
    "tracked_env_files": "tracked env files",
    "hardcoded_credentials": "hardcoded credentials",
    "insecure_defaults": "insecure defaults",
    "sensitive_logs_or_fixtures": "sensitive logs or fixtures",
    "risky_docker_or_ci": "risky Docker/CI configuration",
}


@dataclass
class SecurityGateResult:
    safe_to_generate_blog: bool
    publication_readiness: str  # "clear" | "blocked"
    blocker_reason: str | None
    critical_findings: list[str] = field(default_factory=list)


def assess(signals: EngineeringSignals) -> SecurityGateResult:
    """Engineering-signals.md gating rule: any confirmed high-risk artifact
    blocks public blog generation outright, regardless of engineering
    maturity elsewhere in the source (docs, CI/CD, ownership, etc.).
    """
    security = signals.security
    findings = [
        label
        for field_name, label in _CRITICAL_FIELD_LABELS.items()
        if getattr(security, field_name) == SignalStatus.CONFIRMED
    ]

    if findings:
        return SecurityGateResult(
            safe_to_generate_blog=False,
            publication_readiness="blocked",
            blocker_reason="Confirmed high-risk security artifacts found",
            critical_findings=findings,
        )

    return SecurityGateResult(
        safe_to_generate_blog=True,
        publication_readiness="clear",
        blocker_reason=None,
        critical_findings=[],
    )


def build_remediation_report(result: SecurityGateResult) -> str:
    findings_list = "\n".join(f"- {finding.capitalize()}" for finding in result.critical_findings)
    return f"""# Security Review Report

## Status

Publication readiness: Blocked
Severity: Critical

## Confirmed Critical Findings

{findings_list}

## Impact

These findings may expose credentials, internal system details, deployment configuration, test data, access tokens, or insecure operational defaults. Publishing generated content from this source could accidentally leak sensitive implementation details.

## Immediate Actions

1. Remove secrets and sensitive files from the source.
2. Rotate any exposed credentials.
3. Add `.env`, secret files, logs, fixtures, and generated artifacts to ignore rules.
4. Review Dockerfiles and CI/CD workflows for unsafe defaults.
5. Replace real credentials with safe placeholders.
6. Re-run security scanning.
7. Resume blog generation only after the security status changes from `critical` to `clear` or `acceptable`.

## Publication Decision

Do not generate or publish a technical blog post from this source until remediation is complete.
"""
