"""Data models for the blog topic analyzer."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class GapType(Enum):
    """Types of content gaps."""

    COMPLETE = "complete"  # No blogs for any platform
    PARTIAL = "partial"  # Blogs for some platforms, not all
    PLATFORM_SPECIFIC = "platform_specific"  # New in one platform


class GapSeverity(Enum):
    """Severity levels for gaps."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Platform:
    """Represents a platform configuration (e.g., .NET, Java)."""

    name: str
    display_name: str
    doc_repo: str
    doc_branch: str
    doc_path: str
    api_repo: str
    api_branch: str
    api_path: str
    tut_repo: Optional[str] = None
    tut_branch: str = "main"
    tut_path: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    enabled: bool = True



@dataclass
class Product:
    """Represents a product (e.g., Aspose.Cells)."""

    name: str
    display_name: str
    blog: str
    description: str
    platforms: List[Platform]
    enabled: bool = True

    def get_platform(self, name: str) -> Optional[Platform]:
        """Get platform by name."""
        for platform in self.platforms:
            if platform.name == name:
                return platform
        return None

    def get_enabled_platforms(self) -> List[Platform]:
        """Get all enabled platforms."""
        return [p for p in self.platforms if p.enabled]


@dataclass
class Blog:
    """Represents a blog configuration."""

    name: str
    display_name: str
    blog_repo: str
    blog_branch: str
    website: str
    search_patterns: List[str]
    enabled: bool = True


@dataclass
class Topic:
    """Represents a topic/feature extracted from documentation."""

    name: str
    category: str
    description: str
    importance: int  # 1-5
    keywords: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Topic):
            return False
        return self.name == other.name


@dataclass
class BlogPost:
    """Represents a blog post."""

    title: str
    url: str
    file_path: str
    content: str
    publish_date: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class PlatformCoverage:
    """Coverage information for a topic on a specific platform."""

    topic: Topic
    platform: str
    has_documentation: bool
    has_api_reference: bool
    has_blog_post: bool
    blog_posts: List[BlogPost] = field(default_factory=list)

    @property
    def is_covered(self) -> bool:
        """Check if this topic is fully covered for this platform."""
        return self.has_blog_post

    @property
    def gap_type(self) -> str:
        """Determine the type of gap."""
        if self.has_documentation and not self.has_blog_post:
            return "missing_blog"
        elif not self.has_documentation:
            return "not_documented"
        return "covered"


@dataclass
class CrossPlatformGap:
    """Represents a gap that exists across platforms."""

    topic: Topic
    product: str
    coverage_by_platform: Dict[str, PlatformCoverage]
    gap_type: GapType
    gap_severity: GapSeverity
    missing_platforms: List[str]
    covered_platforms: List[str]
    priority: int  # 1-5
    suggested_title: str = ""
    suggested_outline: str = ""
    target_audience: str = "intermediate"
    estimated_value: str = ""

    @property
    def is_quick_win(self) -> bool:
        """Check if this gap can be quickly filled by adapting existing content."""
        return len(self.covered_platforms) > 0 and len(self.missing_platforms) > 0

    @property
    def coverage_ratio(self) -> float:
        """Ratio of platforms with coverage."""
        total = len(self.covered_platforms) + len(self.missing_platforms)
        if total == 0:
            return 0.0
        return len(self.covered_platforms) / total


@dataclass
class AnalysisResult:
    """Results from analyzing a single product-platform combination."""

    product: str
    platform: str
    topics: List[Topic]
    blog_posts_matched: List[BlogPost]
    extraction_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class ProductAnalysisResult:
    """Results from analyzing a complete product (all platforms)."""

    product: Product
    platform_results: Dict[str, AnalysisResult]
    cross_platform_gaps: List[CrossPlatformGap]
    total_topics: int
    total_gaps: int
    analysis_time: float


@dataclass
class BlogAnalysisResult:
    """Results from analyzing an entire blog."""

    blog: Blog
    product_results: Dict[str, ProductAnalysisResult]
    total_products: int
    total_platforms: int
    total_gaps: int
    complete_gaps: int
    partial_gaps: int
    platform_specific_gaps: int
    analysis_time: float
    cost_estimate: float


@dataclass
class RepositoryInfo:
    """Information about a cloned repository."""

    url: str
    branch: str
    local_path: str
    commit_hash: str
    last_updated: str
    is_cached: bool
