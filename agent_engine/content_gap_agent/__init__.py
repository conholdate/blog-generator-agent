"""
Content Gap Analyzer

An AI-powered tool that identifies missing blog topics by analyzing documentation,
API references, and existing blog posts.
"""

__version__ = "1.0.0"

# Import from new package structure
from agent_engine.content_gap_agent.core.tools import (
    ContentIndexer,
    ContentParser,
    CoverageMatrixGenerator,
    ReportGenerator,
    RepositoryAnalyzer,
)
from .services import (
    PipelineRunner,
)
from agent_engine.content_gap_agent.core.models import (
    AnalysisResult,
    Blog,
    BlogAnalysisResult,
    BlogPost,
    CrossPlatformGap,
    GapSeverity,
    GapType,
    Platform,
    PlatformCoverage,
    Product,
    ProductAnalysisResult,
    RepositoryInfo,
    Topic,
)

__all__ = [
    # Version
    "__version__",
    # Tools
    "ContentIndexer",
    "ContentParser",
    "CoverageMatrixGenerator",
    "ReportGenerator",
    "RepositoryAnalyzer",
    # Agent
    "PipelineRunner",
    # Models
    "AnalysisResult",
    "Blog",
    "BlogAnalysisResult",
    "BlogPost",
    "CrossPlatformGap",
    "GapSeverity",
    "GapType",
    "Platform",
    "PlatformCoverage",
    "Product",
    "ProductAnalysisResult",
    "RepositoryInfo",
    "Topic",
]
