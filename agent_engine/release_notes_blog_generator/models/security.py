from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SignalStatus(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    CONFIRMED = "confirmed"
    NOT_DETECTED = "not_detected"
    UNKNOWN = "unknown"


class StructureSignals(BaseModel):
    src: SignalStatus = SignalStatus.UNKNOWN
    tests: SignalStatus = SignalStatus.UNKNOWN
    entrypoints: SignalStatus = SignalStatus.UNKNOWN


class DocsSignals(BaseModel):
    readme: SignalStatus = SignalStatus.UNKNOWN
    changelog: SignalStatus = SignalStatus.UNKNOWN
    extended_docs: SignalStatus = SignalStatus.UNKNOWN
    contributing: SignalStatus = SignalStatus.UNKNOWN


class AgentSignals(BaseModel):
    agent_policy: SignalStatus = SignalStatus.UNKNOWN
    prompt_directory: SignalStatus = SignalStatus.UNKNOWN


class OpsSignals(BaseModel):
    ci_cd: SignalStatus = SignalStatus.UNKNOWN
    containers: SignalStatus = SignalStatus.UNKNOWN
    ownership: SignalStatus = SignalStatus.UNKNOWN


class SecuritySignals(BaseModel):
    """Confirmed high-risk artifacts. `confirmed` is a blocker, never a good sign."""

    tracked_secrets: SignalStatus = SignalStatus.NOT_DETECTED
    tracked_env_files: SignalStatus = SignalStatus.NOT_DETECTED
    hardcoded_credentials: SignalStatus = SignalStatus.NOT_DETECTED
    insecure_defaults: SignalStatus = SignalStatus.NOT_DETECTED
    sensitive_logs_or_fixtures: SignalStatus = SignalStatus.NOT_DETECTED
    risky_docker_or_ci: SignalStatus = SignalStatus.NOT_DETECTED


class EngineeringSignals(BaseModel):
    structure: StructureSignals = Field(default_factory=StructureSignals)
    docs: DocsSignals = Field(default_factory=DocsSignals)
    agent: AgentSignals = Field(default_factory=AgentSignals)
    ops: OpsSignals = Field(default_factory=OpsSignals)
    security: SecuritySignals = Field(default_factory=SecuritySignals)
