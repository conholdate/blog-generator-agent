from __future__ import annotations

from typing import List, Optional, Literal, Dict

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from agent_engine.blog_keyword_analyzer.tools.normalization import canonical_product_name, normalize_display_text


class KeywordRecord(BaseModel):
    """
    One row of keyword data imported from the source file (GKP, etc.).
    The `keyword` is normalized to lowercase for consistent clustering.
    """

    keyword: str
    source: Literal["upload", "serpapi", "llm"]
    locale: str = "en-US"
    volume: Optional[int] = None
    cpc: Optional[float] = None
    kd: Optional[float] = None
    clicks: Optional[float] = None
    url: Optional[str] = None
    competition: Optional[float] = None
    competition_label: Optional[str] = None

    @field_validator("keyword")
    @classmethod
    def norm_kw(cls, v: str) -> str:
        # Normalize for clustering & deduplication
        return v.strip().lower()


class KeywordOpportunity(BaseModel):
    """
    Local SEO strategy decision for one keyword candidate.

    This sits between raw KeywordRecord inputs and final TopicIdea generation.
    It lets the workflow decide whether a keyword is suitable for a blog post
    before spending an LLM call on a topic brief.
    """

    keyword: str
    source: str = ""
    formats: List[str] = Field(default_factory=list)
    action: Optional[str] = None
    language: Optional[str] = None
    product_family: Optional[str] = None
    strategic_cluster: Optional[str] = None
    intent: Literal["informational", "commercial", "transactional", "navigational"] = "informational"
    funnel_stage: Literal["awareness", "consideration", "decision", "retention"] = "awareness"
    best_page_type: str = "blog_tutorial"
    recommended_action: str = "new_blog_tutorial"
    internal_link_target: Optional[str] = None
    conversion_cta: Optional[str] = None
    business_fit_score: int = 1
    developer_intent_score: int = 1
    conversion_potential_score: int = 1
    cluster_value_score: int = 1
    specificity_score: int = 1
    blog_suitability_score: int = 1
    genericness_penalty: int = 0
    duplicate_penalty: int = 0
    final_priority_score: float = 0.0
    priority_label: Literal["Very High", "High", "Medium", "Low", "Reject"] = "Low"
    duplicate_status: str = "safe_to_generate"
    rationale: List[str] = Field(default_factory=list)


class ClusterMetrics(BaseModel):
    """
    Aggregated metrics for a cluster of keywords.
    These are used to score and rank clusters.
    """

    avg_volume: float = 0.0
    avg_kd: float = 0.0
    avg_cpc: float = 0.0
    brand_fit: float = 0.0
    intent: Literal["informational", "commercial", "transactional", "navigational"] = "informational"
    score: float = 0.0
    avg_competition: Optional[float] = None


class Cluster(BaseModel):
    """
    Represents a cluster of related keywords plus its aggregate metrics.
    """

    cluster_id: str
    label: str
    members: List[KeywordRecord]
    metrics: ClusterMetrics


class SupportingKeywordGroups(BaseModel):
    core_seo_keywords: List[str] = Field(default_factory=list)
    long_tail_keywords: List[str] = Field(default_factory=list)
    context_keywords: List[str] = Field(default_factory=list)


class TopicProfile(BaseModel):
    original_topic: str = ""
    normalized_topic: str = ""
    core_topic: str = ""
    modifiers: List[str] = Field(default_factory=list)
    industry_context: List[str] = Field(default_factory=list)
    audience: List[str] = Field(default_factory=list)
    implied_intent: List[str] = Field(default_factory=list)
    search_type: List[str] = Field(default_factory=list)


class KeywordInsight(BaseModel):
    keyword: str
    keyword_type: Literal[
        "primary",
        "secondary",
        "long_tail",
        "semantic",
        "question",
        "entity",
        "intent_based",
        "aio_aeo",
    ]
    intent: Literal["informational", "commercial", "transactional", "navigational", "local"] = "informational"
    funnel_stage: Literal["awareness", "consideration", "decision", "retention"] = "awareness"
    specificity: Literal["broad", "mid", "specific"] = "mid"
    placement: List[str] = Field(default_factory=list)
    score: float = 0.0
    aeo_score: float = 0.0


class KeywordClusterGroup(BaseModel):
    cluster_name: str
    keywords: List[str] = Field(default_factory=list)


class KeywordAnalysis(BaseModel):
    topic: str = ""
    topic_profile: TopicProfile = Field(default_factory=TopicProfile)
    primary_keyword: Optional[KeywordInsight] = None
    secondary_keywords: List[KeywordInsight] = Field(default_factory=list)
    long_tail_keywords: List[KeywordInsight] = Field(default_factory=list)
    semantic_keywords: List[str] = Field(default_factory=list)
    question_keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    intent_based_keywords: List[KeywordInsight] = Field(default_factory=list)
    aio_aeo_keywords: List[KeywordInsight] = Field(default_factory=list)
    keyword_clusters: List[KeywordClusterGroup] = Field(default_factory=list)
    rejected_keywords: List[str] = Field(default_factory=list)
    keyword_inventory: List[KeywordInsight] = Field(default_factory=list)


class TopicIdea(BaseModel):
    """
    Final topic proposal produced by the LLM.
    This is what the consumer agent / UI will work with.
    """

    cluster_id: str
    title: str
    angle: str
    outline: List[str]
    target_persona: str
    primary_keyword: str
    supporting_keywords: List[str]
    keyword_groups: SupportingKeywordGroups = Field(default_factory=SupportingKeywordGroups)
    editorial_notes: List[str] = Field(default_factory=list)
    internal_links: List[str] = Field(default_factory=list)
    keyword_analysis: KeywordAnalysis = Field(default_factory=KeywordAnalysis)


class RunRequest(BaseModel):
    """
    Input configuration passed into the orchestration runner.

    Note:
      - `file_path` may be an empty string to let the importer search defaults.
      - `weights` allow overriding the default scoring weights if needed.
    """

    brand: str = "Aspose"
    product: str = "Aspose.Cells"
    locale: str = "en-US"
    file_path: str = "/mnt/data/keywords.csv"
    clustering_k: int | None = None
    top_clusters: int = 10
    max_rows: int = 50000
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "volume": 0.35,
            "kd": 0.25,
            "cpc": 0.15,
            "brand": 0.15,
            "intent": 0.10,
        }
    )

    @field_validator("product")
    @classmethod
    def norm_product(cls, v: str, info: ValidationInfo) -> str:
        brand = info.data.get("brand") if info.data else None
        return canonical_product_name(brand, v.strip())


class RunResult(BaseModel):
    """
    Aggregate result returned by the runner:
      - run_id: opaque identifier (useful for logs and file names)
      - clusters: top clusters (already scored and sorted)
      - topics: generated TopicIdea objects
    """

    run_id: str
    brand: str
    product: str
    locale: str
    clusters: List[Cluster]
    topics: List[TopicIdea]
    keyword_opportunities: List[KeywordOpportunity] = Field(default_factory=list)

    @field_validator("product")
    @classmethod
    def norm_product(cls, v: str) -> str:
        return normalize_display_text(v.strip())


class ExistingPost(BaseModel):
    """
    Minimal structure used to represent posts discovered in the content index.

    This is what we pass around when deduplicating topics against existing blogs.
    """

    title: str
    slug: str
    url: str
    product: Optional[str] = None
    platform: Optional[str] = None
    rel_path: Optional[str] = None
