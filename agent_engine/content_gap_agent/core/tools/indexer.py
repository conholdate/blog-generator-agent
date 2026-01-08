"""Content indexer for parsing and indexing repository content."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..models import (
    TopicEntry,
    CategoryNode,
    PlatformIndex,
    ProductIndex,
    BlogIndex,
)

logger = logging.getLogger(__name__)


class ContentIndexer:
    """
    Indexes content from repositories by parsing markdown files,
    extracting frontmatter and headings, and organizing by folder hierarchy.
    """

    # Folders to skip when extracting categories
    SKIP_FOLDERS = {
        "english",
        "en",
        "developer-guide",
        "getting-started",
        "_index.md",
    }

    def __init__(self, output_dir: str = "./output/indexes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def index_product_repo(
        self,
        repo_path: str,
        product: str,
        product_display_name: str,
        brand: str,
        repo_type: str,
        repo_url: str,
        platforms: List[Dict[str, str]],
    ) -> ProductIndex:
        """
        Index a product repository (API, Docs, or Tutorials).
        
        Args:
            repo_path: Local path to the cloned repository
            product: Product name (e.g., "cells")
            product_display_name: Display name (e.g., "Aspose.Cells")
            brand: Brand name (e.g., "aspose")
            repo_type: Type of repo ("api", "docs", "tutorials")
            repo_url: URL of the repository
            platforms: List of platform configs with "name", "display_name", "path"
        
        Returns:
            ProductIndex with all indexed content
        """
        logger.info(f"Indexing {repo_type} repo for {product_display_name}")
        
        product_index = ProductIndex(
            product=product,
            product_display_name=product_display_name,
            brand=brand,
            repo_type=repo_type,
            repo_url=repo_url,
        )
        
        repo_path = Path(repo_path)
        
        for platform_config in platforms:
            platform_name = platform_config["name"]
            platform_display = platform_config.get("display_name", platform_name)
            platform_path = platform_config["path"]
            
            full_path = repo_path / platform_path
            if not full_path.exists():
                logger.warning(f"Platform path not found: {full_path}")
                continue
            
            logger.info(f"  Processing platform: {platform_display} at {platform_path}")
            
            platform_index = self._index_platform_folder(
                full_path,
                platform_name,
                platform_display,
                platform_path,
            )
            
            product_index.platforms[platform_name] = platform_index
            logger.info(f"    Found {platform_index.get_topic_count()} topics")
        
        return product_index

    def index_blog_repo(
        self,
        repo_path: str,
        product: str,
        product_display_name: str,
        brand: str,
        repo_url: str,
        blog_path_pattern: str = "content/Aspose.Blog/{product}",
    ) -> BlogIndex:
        """
        Index a blog repository for a specific product.
        
        Blogs are organized as: content/Aspose.Blog/cells/2025-11-17-title/index.md
        
        Args:
            repo_path: Local path to the cloned repository
            product: Product name (e.g., "cells")
            product_display_name: Display name (e.g., "Aspose.Cells")
            brand: Brand name (e.g., "aspose")
            repo_url: URL of the repository
            blog_path_pattern: Path pattern to the product's blog folder
        
        Returns:
            BlogIndex with all blog posts for this product
        """
        logger.info(f"Indexing blog repo for {product_display_name}")
        
        blog_index = BlogIndex(
            product=product,
            product_display_name=product_display_name,
            brand=brand,
            repo_url=repo_url,
        )
        
        repo_path = Path(repo_path)
        # Replace {product} placeholder with actual product name
        blog_path = blog_path_pattern.replace("{product}", product)
        full_path = repo_path / blog_path
        
        if not full_path.exists():
            logger.warning(f"Blog path not found: {full_path}")
            return blog_index
        
        # Find all markdown files in the blog folder
        md_files = list(full_path.rglob("index.md"))
        logger.info(f"  Found {len(md_files)} markdown files")
        
        for md_file in md_files:
            topic = self._parse_markdown_file(md_file, str(full_path))
            if topic:
                blog_index.add_post(topic)
        
        logger.info(f"  Indexed {blog_index.get_post_count()} blog posts")
        return blog_index

    def _index_platform_folder(
        self,
        folder_path: Path,
        platform_name: str,
        platform_display: str,
        base_path: str,
    ) -> PlatformIndex:
        """Index all markdown files in a platform folder."""
        platform_index = PlatformIndex(
            platform=platform_name,
            display_name=platform_display,
        )
        
        # Find all markdown files
        md_files = list(folder_path.rglob("*.md"))
        
        for md_file in md_files:
            # Extract category path from folder structure
            category_path = self._extract_category_path(md_file, folder_path)
            
            if not category_path:
                continue
            
            # Parse the markdown file
            topic = self._parse_markdown_file(md_file, str(folder_path))
            if topic:
                platform_index.add_topic(category_path, topic)
        
        return platform_index

    def _extract_category_path(self, file_path: Path, base_path: Path) -> List[str]:
        """
        Extract category hierarchy from file path.
        
        Example:
            base_path: english/net
            file_path: english/net/developer-guide/charts/chart-format/_index.md
            Returns: ["Charts", "Chart Format"]
        """
        try:
            relative = file_path.relative_to(base_path)
            parts = list(relative.parts)
            
            # Remove the filename
            if parts and parts[-1].endswith(".md"):
                parts = parts[:-1]
            
            # Filter out skip folders and convert to title case
            category_path = []
            for part in parts:
                # Skip common non-category folders
                if part.lower() in self.SKIP_FOLDERS:
                    continue
                # Skip hidden folders
                if part.startswith(".") or part.startswith("_"):
                    continue
                # Convert to title case with proper formatting
                formatted = self._format_category_name(part)
                if formatted:
                    category_path.append(formatted)
            
            return category_path
        except ValueError:
            return []

    def _format_category_name(self, name: str) -> str:
        """
        Format a folder name as a proper category name.
        
        Examples:
            "chart-format" -> "Chart Format"
            "cells_data" -> "Cells Data"
            "worksheets" -> "Worksheets"
        """
        # Replace hyphens and underscores with spaces
        name = name.replace("-", " ").replace("_", " ")
        # Title case
        name = name.title()
        return name

    def _parse_markdown_file(self, file_path: Path, base_path: str) -> Optional[TopicEntry]:
        """
        Parse a markdown file to extract frontmatter and headings.
        
        Args:
            file_path: Path to the markdown file
            base_path: Base path for calculating relative path
        
        Returns:
            TopicEntry or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return None
        
        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        
        # Extract headings
        headings = self._extract_headings(content)
        
        # Get title from frontmatter or first heading
        title = frontmatter.get("title")
        if not title and headings:
            title = headings[0]
        
        # Get URL from frontmatter
        url = frontmatter.get("url") or frontmatter.get("slug")
        
        # Calculate relative path
        try:
            relative_path = str(file_path.relative_to(base_path))
        except ValueError:
            relative_path = str(file_path)
        
        return TopicEntry(
            file_path=relative_path,
            title=title,
            description=frontmatter.get("description"),
            url=url,
            headings=headings,
            frontmatter=frontmatter,
        )

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from markdown content."""
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if frontmatter_match:
            try:
                return yaml.safe_load(frontmatter_match.group(1)) or {}
            except yaml.YAMLError as e:
                logger.debug(f"Failed to parse frontmatter: {e}")
        return {}

    def _extract_headings(self, content: str) -> List[str]:
        """Extract all headings from markdown content."""
        # Remove frontmatter first
        content = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
        # Extract headings
        headings = re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)
        return [h.strip() for h in headings]

    def save_index(self, index: ProductIndex | BlogIndex, output_path: str = None) -> str:
        """
        Save an index to a JSON file.
        
        Args:
            index: The index to save
            output_path: Optional custom output path
        
        Returns:
            Path to the saved file
        """
        if output_path is None:
            # Generate default path based on index type and product
            if isinstance(index, BlogIndex):
                filename = f"{index.brand}_{index.product}_blogs.json"
            else:
                filename = f"{index.brand}_{index.product}_{index.repo_type}.json"
            output_path = self.output_dir / index.brand / filename
        else:
            output_path = Path(output_path)
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved index to {output_path}")
        return str(output_path)

    def load_index(self, index_path: str) -> ProductIndex | BlogIndex:
        """
        Load an index from a JSON file.
        
        Args:
            index_path: Path to the JSON file
        
        Returns:
            ProductIndex or BlogIndex
        """
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Determine type based on content
        if "posts" in data:
            return BlogIndex.from_dict(data)
        else:
            return ProductIndex.from_dict(data)

    def list_indexes(self, brand: str = None) -> List[str]:
        """
        List all available index files.
        
        Args:
            brand: Optional brand to filter by
        
        Returns:
            List of index file paths
        """
        if brand:
            search_path = self.output_dir / brand
        else:
            search_path = self.output_dir
        
        if not search_path.exists():
            return []
        
        return [str(p) for p in search_path.rglob("*.json")]
