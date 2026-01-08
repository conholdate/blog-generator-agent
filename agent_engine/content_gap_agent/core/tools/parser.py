"""Content parsing for markdown files."""

import re
from pathlib import Path
from typing import Dict, List

import yaml


class ContentParser:
    """Parses markdown content to extract topics and features."""

    @staticmethod
    def extract_headings(content: str) -> List[str]:
        """Extract all headings from markdown content."""
        headings = re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)
        return [h.strip() for h in headings]

    @staticmethod
    def extract_code_elements(content: str) -> Dict[str, List[str]]:
        """Extract classes, methods, and properties from documentation."""
        elements = {"classes": [], "methods": [], "properties": [], "enums": []}

        # Extract class names (common patterns in API docs)
        classes = re.findall(r"(?:class|Class)\s+([A-Z][a-zA-Z0-9]+)", content)
        elements["classes"].extend(classes)

        # Extract method names
        methods = re.findall(r"(?:public|Public)\s+(?:\w+\s+)?(\w+)\s*\(", content)
        elements["methods"].extend(methods)

        # Extract properties
        properties = re.findall(
            r"(?:Property|property):\s*`?([A-Z][a-zA-Z0-9]+)`?", content
        )
        elements["properties"].extend(properties)

        return elements

    @staticmethod
    def extract_metadata(file_path: Path, content: str) -> Dict:
        """Extract metadata from markdown files."""
        metadata = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "relative_path": None,
            "title": None,
            "description": None,
        }

        # Try to extract YAML frontmatter
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                metadata["title"] = frontmatter.get("title")
                metadata["description"] = frontmatter.get("description")
            except Exception:
                pass

        # If no title in frontmatter, get first heading
        if not metadata["title"]:
            first_heading = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if first_heading:
                metadata["title"] = first_heading.group(1).strip()

        return metadata
