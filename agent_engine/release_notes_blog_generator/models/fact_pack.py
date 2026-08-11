from __future__ import annotations

from pydantic import BaseModel, Field

from .code_verification import CodeVerificationResult
from .docs_extraction import DocsTopic
from .keyword_analysis import KeywordAnalysisResult
from .platform import PlatformContext

SOURCE_TYPE_RELEASE_NOTES = "release_notes"
SOURCE_TYPE_DOCS = "docs"


class FactPack(BaseModel):
    """The single source of truth the writer agent is allowed to write from.

    Per instructions.md: "the writer agent should only write from this fact
    pack, not from memory."

    The same model serves both use cases. A release-notes fact pack describes
    one feature and carries one snippet; a docs fact pack describes a whole
    documentation article and additionally populates `doc_topics` with the
    per-heading breakdown the docs writer prompt walks through. `source_type`
    says which one it is, and the docs-only fields stay empty on the
    release-notes path so nothing about that flow changes.
    """

    topic: str
    primary_source_url: str
    source_title: str
    sdk_version: str
    main_problem_solved: str
    platform: PlatformContext
    source_type: str = SOURCE_TYPE_RELEASE_NOTES
    keyword_analysis: KeywordAnalysisResult | None = None
    key_steps: list[str] = Field(default_factory=list)
    code_snippets: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    facts_confirmed_from_source: list[str] = Field(default_factory=list)
    facts_needing_verification: list[str] = Field(default_factory=list)
    suggested_article_outline: list[str] = Field(default_factory=list)
    code_verification: CodeVerificationResult

    # Docs-article use case only — see pipeline/docs_extractor.py.
    prerequisites: list[str] = Field(default_factory=list)
    doc_topics: list[DocsTopic] = Field(default_factory=list)
