from __future__ import annotations

from pydantic import BaseModel, Field


class KeywordGroups(BaseModel):
    core_seo_keywords: list[str] = Field(default_factory=list)
    long_tail_keywords: list[str] = Field(default_factory=list)
    context_keywords: list[str] = Field(default_factory=list)


class KeywordAnalysisResult(BaseModel):
    """The subset of blog-keyword-analyzer's TopicIdea we consume: an
    SEO-refined title/angle/outline plus the keyword groups used for meta
    tags. Produced by pipeline/keyword_analyzer.py before fact-pack assembly
    so the writer never has to invent title/tag keywords itself.
    """

    title: str
    angle: str = ""
    outline: list[str] = Field(default_factory=list)
    target_persona: str = ""
    primary_keyword: str = ""
    supporting_keywords: list[str] = Field(default_factory=list)
    keyword_groups: KeywordGroups = Field(default_factory=KeywordGroups)
    editorial_notes: list[str] = Field(default_factory=list)
