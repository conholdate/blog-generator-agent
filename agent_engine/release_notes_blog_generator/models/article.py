from __future__ import annotations

from pydantic import BaseModel, Field

from .fact_pack import FactPack
from .quality import QualityAssessment


class Cover(BaseModel):
    image: str
    alt: str
    caption: str
    hidden: bool = False


class FaqItem(BaseModel):
    q: str
    a: str


class SeoFrontMatter(BaseModel):
    """Mirrors the front matter shape used across input/2025-10-30-add-pages-to-pdf-in-python/index.md."""

    title: str
    seoTitle: str
    description: str
    date: str
    draft: bool = True
    url: str
    author: str | None = None
    summary: str
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    showtoc: bool = True
    cover: Cover
    steps: list[str] = Field(default_factory=list)
    faqs: list[FaqItem] = Field(default_factory=list)


class BlogPost(BaseModel):
    slug: str
    publish_date: str  # YYYY-MM-DD, shared by front_matter.date and the output folder name
    front_matter: SeoFrontMatter
    body_markdown: str
    fact_pack: FactPack
    quality: QualityAssessment | None = None
