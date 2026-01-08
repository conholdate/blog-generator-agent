"""Data models for the content indexing system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


@dataclass
class TopicEntry:
    """Single topic from a markdown file."""
    
    file_path: str
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    headings: List[str] = field(default_factory=list)
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "headings": self.headings,
            "frontmatter": self.frontmatter,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicEntry":
        """Create from dictionary."""
        return cls(
            file_path=data["file_path"],
            title=data.get("title"),
            description=data.get("description"),
            url=data.get("url"),
            headings=data.get("headings", []),
            frontmatter=data.get("frontmatter", {}),
        )


@dataclass
class CategoryNode:
    """
    Represents a category node in the hierarchy.
    Can contain both topics and sub-categories.
    """
    
    name: str
    topics: List[TopicEntry] = field(default_factory=list)
    sub_categories: Dict[str, "CategoryNode"] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "topics": [t.to_dict() for t in self.topics],
            "sub_categories": {
                name: cat.to_dict() for name, cat in self.sub_categories.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CategoryNode":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            topics=[TopicEntry.from_dict(t) for t in data.get("topics", [])],
            sub_categories={
                name: CategoryNode.from_dict(cat)
                for name, cat in data.get("sub_categories", {}).items()
            },
        )
    
    def add_topic(self, category_path: List[str], topic: TopicEntry) -> None:
        """
        Add a topic to the correct location in the category hierarchy.
        
        Args:
            category_path: List of category names forming the path (e.g., ["Charts", "Chart Format"])
            topic: The topic entry to add
        """
        if not category_path:
            # No more path, add topic here
            self.topics.append(topic)
            return
        
        # Navigate to or create the sub-category
        next_category = category_path[0]
        if next_category not in self.sub_categories:
            self.sub_categories[next_category] = CategoryNode(name=next_category)
        
        # Recursively add to the sub-category
        self.sub_categories[next_category].add_topic(category_path[1:], topic)
    
    def get_all_topics(self) -> List[TopicEntry]:
        """Get all topics in this category and all sub-categories recursively."""
        all_topics = list(self.topics)
        for sub_cat in self.sub_categories.values():
            all_topics.extend(sub_cat.get_all_topics())
        return all_topics
    
    def get_topic_count(self) -> int:
        """Get total count of topics in this category and all sub-categories."""
        count = len(self.topics)
        for sub_cat in self.sub_categories.values():
            count += sub_cat.get_topic_count()
        return count


@dataclass
class PlatformIndex:
    """Index for a specific platform."""
    
    platform: str
    display_name: str
    categories: Dict[str, CategoryNode] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "platform": self.platform,
            "display_name": self.display_name,
            "categories": {
                name: cat.to_dict() for name, cat in self.categories.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlatformIndex":
        """Create from dictionary."""
        return cls(
            platform=data["platform"],
            display_name=data.get("display_name", data["platform"]),
            categories={
                name: CategoryNode.from_dict(cat)
                for name, cat in data.get("categories", {}).items()
            },
        )
    
    def add_topic(self, category_path: List[str], topic: TopicEntry) -> None:
        """Add a topic to the correct category path."""
        if not category_path:
            return
        
        root_category = category_path[0]
        if root_category not in self.categories:
            self.categories[root_category] = CategoryNode(name=root_category)
        
        self.categories[root_category].add_topic(category_path[1:], topic)
    
    def get_topic_count(self) -> int:
        """Get total count of topics across all categories."""
        return sum(cat.get_topic_count() for cat in self.categories.values())


@dataclass
class ProductIndex:
    """Complete index for a product."""
    
    product: str
    product_display_name: str
    brand: str
    repo_type: str  # "api", "docs", "blogs", "tutorials"
    repo_url: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    platforms: Dict[str, PlatformIndex] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "product": self.product,
            "product_display_name": self.product_display_name,
            "brand": self.brand,
            "repo_type": self.repo_type,
            "repo_url": self.repo_url,
            "generated_at": self.generated_at,
            "platforms": {
                name: plat.to_dict() for name, plat in self.platforms.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductIndex":
        """Create from dictionary."""
        return cls(
            product=data["product"],
            product_display_name=data.get("product_display_name", data["product"]),
            brand=data["brand"],
            repo_type=data["repo_type"],
            repo_url=data.get("repo_url", ""),
            generated_at=data.get("generated_at", ""),
            platforms={
                name: PlatformIndex.from_dict(plat)
                for name, plat in data.get("platforms", {}).items()
            },
        )
    
    def get_platform(self, platform: str) -> Optional[PlatformIndex]:
        """Get platform index by name."""
        return self.platforms.get(platform)
    
    def get_or_create_platform(self, platform: str, display_name: str = None) -> PlatformIndex:
        """Get or create a platform index."""
        if platform not in self.platforms:
            self.platforms[platform] = PlatformIndex(
                platform=platform,
                display_name=display_name or platform,
            )
        return self.platforms[platform]
    
    def get_total_topic_count(self) -> int:
        """Get total count of topics across all platforms."""
        return sum(plat.get_topic_count() for plat in self.platforms.values())


@dataclass
class BlogIndex:
    """
    Index for blog posts - different structure since blogs are organized by product, not platform.
    Path: content/Aspose.Blog/cells/2025-11-17-create-waterfall-chart/index.md
    """
    
    product: str
    product_display_name: str
    brand: str
    repo_url: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    posts: List[TopicEntry] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "product": self.product,
            "product_display_name": self.product_display_name,
            "brand": self.brand,
            "repo_url": self.repo_url,
            "generated_at": self.generated_at,
            "posts": [p.to_dict() for p in self.posts],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlogIndex":
        """Create from dictionary."""
        return cls(
            product=data["product"],
            product_display_name=data.get("product_display_name", data["product"]),
            brand=data["brand"],
            repo_url=data.get("repo_url", ""),
            generated_at=data.get("generated_at", ""),
            posts=[TopicEntry.from_dict(p) for p in data.get("posts", [])],
        )
    
    def add_post(self, post: TopicEntry) -> None:
        """Add a blog post to the index."""
        self.posts.append(post)
    
    def get_post_count(self) -> int:
        """Get total count of blog posts."""
        return len(self.posts)

class CoverageStatus(str, Enum):
    EXACT = "exact"
    INHERITED = "inherited"
    MISSING = "missing"

    def mark(self) -> str:
        return {"exact": "✓", "inherited": "~", "missing": "✗"}[self.value]

@dataclass
class CoverageEntry:
    category_path: List[str]
    topic_title: str

    # Keep these if other code relies on them (optional)
    in_api: bool = False
    in_docs: bool = False
    in_blogs: bool = False
    in_tutorials: bool = False

    # ✅ New tri-state statuses
    docs_status: CoverageStatus = CoverageStatus.MISSING
    blogs_status: CoverageStatus = CoverageStatus.MISSING
    tutorials_status: CoverageStatus = CoverageStatus.MISSING

    api_url: Optional[str] = None
    docs_url: Optional[str] = None
    blog_urls: List[str] = field(default_factory=list)
    tutorial_url: Optional[str] = None

    # Optional: where the inherited match came from
    inherited_from: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_path": self.category_path,
            "topic_title": self.topic_title,
            "in_api": self.in_api,
            "in_docs": self.in_docs,
            "in_blogs": self.in_blogs,
            "in_tutorials": self.in_tutorials,
            "docs_status": self.docs_status.value,
            "blogs_status": self.blogs_status.value,
            "tutorials_status": self.tutorials_status.value,
            "api_url": self.api_url,
            "docs_url": self.docs_url,
            "blog_urls": self.blog_urls,
            "tutorial_url": self.tutorial_url,
            "inherited_from": self.inherited_from,
        }

@dataclass
class CoverageMatrix:
    """Coverage matrix for a product across all platforms."""
    
    product: str
    product_display_name: str
    brand: str
    platform: str
    platform_display_name: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    entries: List[CoverageEntry] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "product": self.product,
            "product_display_name": self.product_display_name,
            "brand": self.brand,
            "platform": self.platform,
            "platform_display_name": self.platform_display_name,
            "generated_at": self.generated_at,
            "entries": [e.to_dict() for e in self.entries],
        }
    
    def add_entry(self, entry: CoverageEntry) -> None:
        """Add a coverage entry."""
        self.entries.append(entry)
    
    def get_coverage_stats(self) -> Dict[str, Any]:
        """Get coverage statistics."""
        total = len(self.entries)
        if total == 0:
            return {"total": 0, "docs": 0, "blogs": 0, "tutorials": 0}
        
        docs_count = sum(1 for e in self.entries if e.in_docs)
        blogs_count = sum(1 for e in self.entries if e.in_blogs)
        tutorials_count = sum(1 for e in self.entries if e.in_tutorials)
        
        return {
            "total": total,
            "docs": docs_count,
            "docs_percent": round(docs_count / total * 100, 1),
            "blogs": blogs_count,
            "blogs_percent": round(blogs_count / total * 100, 1),
            "tutorials": tutorials_count,
            "tutorials_percent": round(tutorials_count / total * 100, 1),
        }
