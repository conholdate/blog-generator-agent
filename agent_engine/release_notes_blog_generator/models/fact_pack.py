from __future__ import annotations

from pydantic import BaseModel, Field

from .code_verification import CodeVerificationResult
from .keyword_analysis import KeywordAnalysisResult
from .platform import PlatformContext


class FactPack(BaseModel):
    """The single source of truth the writer agent is allowed to write from.

    Per instructions.md: "the writer agent should only write from this fact
    pack, not from memory."
    """

    topic: str
    primary_source_url: str
    source_title: str
    sdk_version: str
    main_problem_solved: str
    platform: PlatformContext
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
