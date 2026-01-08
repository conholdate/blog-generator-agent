"""Data models for the blog topic analyzer."""

from .types import (
    GapType,
    GapSeverity,
    Platform,
    Product,
    Blog,
    Topic,
    BlogPost,
    PlatformCoverage,
    CrossPlatformGap,
    AnalysisResult,
    ProductAnalysisResult,
    BlogAnalysisResult,
    RepositoryInfo,
)

from .indexer_types import (
    TopicEntry,
    CategoryNode,
    PlatformIndex,
    ProductIndex,
    BlogIndex,
    CoverageEntry,
    CoverageMatrix,
)

__all__ = [
    "GapType",
    "GapSeverity",
    "Platform",
    "Product",
    "Blog",
    "Topic",
    "BlogPost",
    "PlatformCoverage",
    "CrossPlatformGap",
    "AnalysisResult",
    "ProductAnalysisResult",
    "BlogAnalysisResult",
    "RepositoryInfo",
    # Indexer types
    "TopicEntry",
    "CategoryNode",
    "PlatformIndex",
    "ProductIndex",
    "BlogIndex",
    "CoverageEntry",
    "CoverageMatrix",
]
