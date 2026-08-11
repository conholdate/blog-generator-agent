from __future__ import annotations

from pydantic import BaseModel, Field


class DocsTopic(BaseModel):
    """One topic covered by a documentation article — normally one heading on
    the page (e.g. "Load from a Stream" on
    docs.aspose.com/words/net/create-or-load-a-document/).

    Unlike `EligibleTopic`, a topic here does *not* have to carry a code
    sample: a docs page routinely has framing headings ("Load a Document")
    whose children hold the samples, and the generated post covers the page
    as a whole. `code_sample` is therefore optional and the code-backed
    requirement is enforced at the article level instead — see
    pipeline/docs_extractor.py.
    """

    heading: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    code_sample: str = ""
    language: str = ""
    apis_used: list[str] = Field(default_factory=list)
    classes_used: list[str] = Field(default_factory=list)
    methods_used: list[str] = Field(default_factory=list)
    properties_used: list[str] = Field(default_factory=list)


class SkippedSection(BaseModel):
    heading: str
    reason_for_skipping: str


class DocsArticleExtraction(BaseModel):
    """The whole documentation page distilled into one blog-post plan.

    This is the structural difference between the two use cases: release
    notes fan out to one post per code-backed section (`ExtractionResult`
    holds a list of independent topics), whereas a docs article fans *in* —
    every topic on the page becomes a section of a single, longer post.
    """

    article_title: str
    source_url: str
    overview: str
    primary_language: str = ""
    suggested_title: str
    blog_angle: str = ""
    seo_keywords: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    topics: list[DocsTopic] = Field(default_factory=list)
    skipped_sections: list[SkippedSection] = Field(default_factory=list)
    unsupported_or_missing_details: list[str] = Field(default_factory=list)

    @property
    def code_backed_topics(self) -> list[DocsTopic]:
        return [topic for topic in self.topics if topic.code_sample.strip()]
