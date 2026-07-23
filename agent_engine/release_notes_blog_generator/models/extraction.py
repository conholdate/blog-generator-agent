from __future__ import annotations

from pydantic import BaseModel, Field


class EligibleTopic(BaseModel):
    """A release-notes section that passed the code-sample-first filter."""

    heading: str
    reason_for_selection: str
    feature_summary: str
    issue_ids: list[str] = Field(default_factory=list)
    code_sample: str
    language: str
    apis_used: list[str] = Field(default_factory=list)
    classes_used: list[str] = Field(default_factory=list)
    methods_used: list[str] = Field(default_factory=list)
    properties_used: list[str] = Field(default_factory=list)
    blog_angle: str
    suggested_title: str
    seo_keywords: list[str] = Field(default_factory=list)
    unsupported_or_missing_details: list[str] = Field(default_factory=list)


class RejectedSection(BaseModel):
    heading: str
    reason_for_rejection: str


class ExtractionResult(BaseModel):
    release_title: str
    source_url: str
    eligible_topics: list[EligibleTopic] = Field(default_factory=list)
    rejected_sections: list[RejectedSection] = Field(default_factory=list)
