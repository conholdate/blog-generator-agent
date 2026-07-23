from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PublicationStatus(str, Enum):
    DRAFT_GENERATED = "draft_generated"
    NEEDS_CODE_REVIEW = "needs_code_review"
    NEEDS_FACT_CHECK = "needs_fact_check"
    READY_FOR_EDITOR = "ready_for_editor"
    APPROVED_FOR_PUBLISH = "approved_for_publish"
    PUBLISHED = "published"
    BLOCKED = "blocked"
    INSUFFICIENT_CODE_SAMPLES = "insufficient_code_samples"


class QualityScores(BaseModel):
    technical_accuracy: int
    code_correctness: int
    original_value: int
    source_faithfulness: int
    seo_readiness: int
    readability: int
    duplication_risk: int
    missing_citations: bool
    unsupported_claims: bool


class QualityAssessment(BaseModel):
    scores: QualityScores
    publication_status: PublicationStatus
    reasons: list[str] = Field(default_factory=list)
