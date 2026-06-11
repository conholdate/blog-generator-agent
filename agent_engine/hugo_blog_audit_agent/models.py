from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BlogConfig:
    blog_name: str
    repo_url: str | None = None
    repo_path: str | None = None
    branch: str | None = None
    content_dir: str = "content"
    expected_languages: list[str] = field(default_factory=list)
    output_dir: str = "outputs"
    website: str = ""
    audience_profile: str = ""
    developer_audience: bool = False
    policy_files: list[str] = field(default_factory=list)
    known_product_mentions: list[str] = field(default_factory=list)
    sdk_validation: dict[str, Any] = field(default_factory=dict)
    llm: dict[str, Any] = field(default_factory=dict)
    file_formats_path: str = ""
    file_format_aliases: list[str] = field(default_factory=list)
    product_config_dir: str = ""
    product_configs: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def repository_source(self) -> str:
        source = self.repo_path or self.repo_url
        if not source:
            raise ValueError("Blog config must define either repo_path for a local repository or repo_url for cloning.")
        return source


@dataclass
class HugoDetection:
    root: Path
    config_files: list[str]
    directories: dict[str, bool]
    multilingual: bool
    languages: list[str]


@dataclass
class Link:
    text: str
    target: str
    is_internal: bool
    line: int
    exists: bool | None = None


@dataclass
class ImageRef:
    alt: str
    target: str
    line: int
    exists: bool | None = None


@dataclass
class CodeSample:
    language: str
    code: str
    line: int


@dataclass
class Heading:
    level: int
    text: str
    line: int


@dataclass
class Issue:
    file_path: str
    issue_type: str
    severity: str
    explanation: str
    why_it_matters: str
    recommended_fix: str
    estimated_effort: str
    expected_seo_impact: str
    line: int = 0
    policy_id: str = ""
    rule_id: str = ""
    evidence: str = ""
    intended_audiences: list[str] = field(default_factory=list)


@dataclass
class LLMSuggestion:
    file_path: str
    provider: str
    model: str
    cached: bool
    summary: str = ""
    suggested_title: str = ""
    suggested_description: str = ""
    outline: list[str] = field(default_factory=list)
    faq_questions: list[str] = field(default_factory=list)
    content_actions: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    issues_addressed: list[str] = field(default_factory=list)


@dataclass
class Post:
    path: Path
    relative_path: str
    url_candidate: str
    language: str
    front_matter_format: str
    front_matter: dict[str, Any]
    body: str
    body_line_offset: int
    title: str
    description: str
    date: str
    lastmod: str
    draft: bool
    slug: str
    aliases: list[str]
    tags: list[str]
    categories: list[str]
    keywords: list[str]
    canonical_url: str
    translation_key: str
    word_count: int
    character_count: int
    headings: list[Heading]
    paragraphs: list[str]
    images: list[ImageRef]
    links: list[Link]
    code_samples: list[CodeSample]
    code_blocks: int
    tables: int
    shortcodes: list[str]
    faq_like_sections: int
    schema_like_blocks: int
    issues: list[Issue] = field(default_factory=list)
    llm_suggestions: list[LLMSuggestion] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)
    translation_group: str = ""


@dataclass
class TranslationGroup:
    key: str
    posts: list[Post]
    available_languages: list[str]
    missing_languages: list[str]
    canonical_path: str
    issues: list[Issue] = field(default_factory=list)


@dataclass
class AuditResult:
    config: BlogConfig
    repo_root: Path
    detection: HugoDetection
    posts: list[Post]
    groups: list[TranslationGroup]
    technical_issues: list[Issue]
    internal_link_issues: list[Issue]
    llm_metrics: dict[str, Any] = field(default_factory=dict)
