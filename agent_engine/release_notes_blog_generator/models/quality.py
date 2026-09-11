from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# The blog-writing skill's publish bar: 85+ on the 100-point QA scorecard with
# no critical technical error (prompts/blog-writing/references/aspose-article-brief.md §5).
QA_SCORECARD_PASS_THRESHOLD = 85


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


class QAScorecard(BaseModel):
    """The blog-writing skill's 100-point QA scorecard, scored deterministically
    by content_metrics.qa_scorecard() from the same measurements QualityScores
    is built from. Point ceilings per criterion:
    search_intent 10, technical_accuracy 25, original_value 20,
    answer_first_structure 15, seo_metadata 10, internal_linking 10,
    accessibility 5, llm_clarity 5.

    `passes` is the skill's rule: total >= QA_SCORECARD_PASS_THRESHOLD AND
    not critical_technical_error.
    """

    search_intent: int
    technical_accuracy: int
    original_value: int
    answer_first_structure: int
    seo_metadata: int
    internal_linking: int
    accessibility: int
    llm_clarity: int
    total: int
    critical_technical_error: bool
    passes: bool


class QualityAssessment(BaseModel):
    scores: QualityScores
    scorecard: QAScorecard | None = None
    publication_status: PublicationStatus
    reasons: list[str] = Field(default_factory=list)
