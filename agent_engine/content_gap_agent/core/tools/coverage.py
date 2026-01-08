# coverage.py (patch)
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Literal

from ..models import (
    ProductIndex,
    BlogIndex,
    CoverageEntry,
    CoverageMatrix,
    TopicEntry,
    CategoryNode,
)
from ..models.indexer_types import CoverageStatus

logger = logging.getLogger(__name__)


@dataclass
class _TypeCluster:
    """Internal bucket: one cluster per API type (class/enum/interface/struct)."""
    category_path: List[str]
    type_name: str
    type_url: Optional[str] = None
    members: List[TopicEntry] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return f"{self.type_name} (members: {len(self.members)})"


class CoverageMatrixGenerator:
    """
    Generates coverage matrices by comparing API Reference (baseline)
    against Docs, Blogs, and Tutorials indexes.
    """

    def __init__(self, output_dir: str = "./output/coverage"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_coverage_matrix(
        self,
        api_index: ProductIndex,
        docs_index: Optional[ProductIndex],
        blog_index: Optional[BlogIndex],
        tutorials_index: Optional[ProductIndex],
        platform: str,
        coverage_level: Literal["member", "type"] = "type",  # ✅ NEW
    ) -> CoverageMatrix:
        """
        Generate a coverage matrix for a specific platform.

        coverage_level:
          - "member": old behavior (1 entry per API member/topic) => huge output
          - "type":   cluster members into their parent type => sane output
        """
        logger.info(
            "Generating coverage matrix for %s - %s (coverage_level=%s)",
            api_index.product_display_name,
            platform,
            coverage_level,
        )

        api_platform = api_index.get_platform(platform)
        if not api_platform:
            logger.warning("Platform %s not found in API index", platform)
            return CoverageMatrix(
                product=api_index.product,
                product_display_name=api_index.product_display_name,
                brand=api_index.brand,
                platform=platform,
                platform_display_name=platform,
            )

        matrix = CoverageMatrix(
            product=api_index.product,
            product_display_name=api_index.product_display_name,
            brand=api_index.brand,
            platform=platform,
            platform_display_name=api_platform.display_name,
        )

        docs_platform = docs_index.get_platform(platform) if docs_index else None
        tutorials_platform = tutorials_index.get_platform(platform) if tutorials_index else None

        # lookups: normalized string -> list of TopicEntry
        docs_topics = self._build_topic_lookup(docs_platform) if docs_platform else {}
        tutorials_topics = self._build_topic_lookup(tutorials_platform) if tutorials_platform else {}
        blog_topics = self._build_blog_lookup(blog_index) if blog_index else {}

        if coverage_level == "member":
            # Old behavior
            self._process_categories_members(
                api_platform.categories,
                [],
                matrix,
                docs_topics,
                blog_topics,
                tutorials_topics,
            )
        else:
            # ✅ New behavior: type clustering
            clusters = self._collect_type_clusters(api_platform.categories)
            for cluster in clusters.values():
                entry = self._create_type_cluster_entry(
                    category_path=cluster.category_path,
                    cluster=cluster,
                    docs_topics=docs_topics,
                    blog_topics=blog_topics,
                    tutorials_topics=tutorials_topics,
                )
                matrix.add_entry(entry)

        logger.info("  Generated %d coverage entries", len(matrix.entries))
        return matrix

    # -----------------------
    # Lookup builders (same)
    # -----------------------

    def _build_topic_lookup(self, platform_index) -> Dict[str, List[TopicEntry]]:
        if not platform_index:
            return {}
        lookup: Dict[str, List[TopicEntry]] = {}
        for category in platform_index.categories.values():
            self._add_category_to_lookup(category, lookup)
        return lookup

    def _add_category_to_lookup(self, category: CategoryNode, lookup: Dict[str, List[TopicEntry]]) -> None:
        for topic in category.topics:
            for key in self._topic_keys(topic):
                lookup.setdefault(key, []).append(topic)
        for sub_cat in category.sub_categories.values():
            self._add_category_to_lookup(sub_cat, lookup)

    def _topic_keys(self, topic: TopicEntry) -> Set[str]:
        keys: Set[str] = set()

        if topic.title:
            keys.add(self._normalize_title(topic.title))

        for h in topic.headings or []:
            keys.add(self._normalize_title(h))

        fm = topic.frontmatter or {}
        for k in ("title", "description"):
            v = fm.get(k)
            if isinstance(v, str) and v.strip():
                keys.add(self._normalize_title(v))

        for k in ("tags", "keywords", "categories"):
            v = fm.get(k)
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and item.strip():
                        keys.add(self._normalize_title(item))
            elif isinstance(v, str) and v.strip():
                keys.add(self._normalize_title(v))

        if topic.file_path:
            parts = [p for p in topic.file_path.replace("\\", "/").split("/") if p]
            for p in parts[-6:]:
                keys.add(self._normalize_title(p))

        return {k for k in keys if k}

    def _build_blog_lookup(self, blog_index: Optional[BlogIndex]) -> Dict[str, List[TopicEntry]]:
        if not blog_index:
            return {}

        lookup: Dict[str, List[TopicEntry]] = {}
        for post in blog_index.posts:
            for key in self._topic_keys(post):
                lookup.setdefault(key, []).append(post)

            if post.title:
                for kw in self._extract_keywords(post.title):
                    lookup.setdefault(kw, []).append(post)

        return lookup

    # -----------------------
    # Normalization helpers
    # -----------------------

    def _strip_kind_prefix(self, title: str) -> str:
        t = title.strip()
        for p in ("class ", "enum ", "interface ", "struct "):
            if t.lower().startswith(p):
                return t[len(p):].strip()
        return t

    def _split_camel(self, s: str) -> str:
        import re
        return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)

    def _aliases(self, raw: str) -> Set[str]:
        raw = raw.strip()
        if not raw:
            return set()

        core = self._strip_kind_prefix(raw)
        core = core.replace("()", "").strip()

        variants = {core}

        parts = core.split(".")
        spaced_parts = [self._split_camel(p) for p in parts]
        variants.add(".".join(spaced_parts))
        variants.add(" ".join(spaced_parts))
        variants.add(self._split_camel(core))
        variants.add(self._split_camel(core).replace(" ", ""))

        return {self._normalize_title(v) for v in variants if v}

    def _match_one(self, aliases: Set[str], lookup: Dict[str, List[TopicEntry]]) -> Optional[TopicEntry]:
        for a in aliases:
            hits = lookup.get(a)
            if hits:
                return hits[0]
        return None

    def _match_many(self, aliases: Set[str], lookup: Dict[str, List[TopicEntry]]) -> List[TopicEntry]:
        found: Dict[str, TopicEntry] = {}
        for a in aliases:
            for t in lookup.get(a, []):
                found.setdefault(t.file_path, t)
        return list(found.values())

    def _normalize_title(self, title: str) -> str:
        if not title:
            return ""
        import re
        normalized = title.lower()
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _extract_keywords(self, title: str) -> List[str]:
        if not title:
            return []
        stop_words = {
            "a", "an", "the", "in", "on", "at", "to", "for", "of", "with",
            "and", "or", "is", "are", "was", "were", "be", "been",
            "how", "what", "when", "where", "why", "which",
            "using", "use", "create", "creating", "add", "adding",
            "net", "java", "python", "c", "cpp", "csharp",
            "aspose", "cells", "words", "pdf",
        }
        import re
        words = re.findall(r"\b\w+\b", title.lower())
        return [w for w in words if len(w) > 2 and w not in stop_words]

    # -----------------------------------------
    # Old behavior: member-by-member processing
    # -----------------------------------------

    def _process_categories_members(
        self,
        categories: Dict[str, CategoryNode],
        parent_path: List[str],
        matrix: CoverageMatrix,
        docs_topics: Dict[str, List[TopicEntry]],
        blog_topics: Dict[str, List[TopicEntry]],
        tutorials_topics: Dict[str, List[TopicEntry]],
    ) -> None:
        for cat_name, category in categories.items():
            current_path = parent_path + [cat_name]

            for topic in category.topics:
                entry = self._create_coverage_entry(
                    current_path,
                    topic,
                    docs_topics,
                    blog_topics,
                    tutorials_topics,
                )
                matrix.add_entry(entry)

            self._process_categories_members(
                category.sub_categories,
                current_path,
                matrix,
                docs_topics,
                blog_topics,
                tutorials_topics,
            )

    def _create_coverage_entry(
        self,
        category_path: List[str],
        api_topic: TopicEntry,
        docs_topics: Dict[str, List[TopicEntry]],
        blog_topics: Dict[str, List[TopicEntry]],
        tutorials_topics: Dict[str, List[TopicEntry]],
    ) -> CoverageEntry:
        title = api_topic.title or api_topic.file_path
        core = self._strip_kind_prefix(title)
        is_member = "." in core
        parent = core.split(".")[0] if is_member else core

        topic_aliases = self._aliases(core)
        parent_aliases = self._aliases(parent)

        docs_exact = self._match_one(topic_aliases, docs_topics)
        docs_parent = None if docs_exact else self._match_one(parent_aliases, docs_topics)

        tut_exact = self._match_one(topic_aliases, tutorials_topics)
        tut_parent = None if tut_exact else self._match_one(parent_aliases, tutorials_topics)

        blog_exact = self._match_many(topic_aliases, blog_topics)
        blog_parent = [] if blog_exact else self._match_many(parent_aliases, blog_topics)

        entry = CoverageEntry(
            category_path=category_path,
            topic_title=title,
            in_api=True,
            api_url=api_topic.url,
        )

        if docs_exact:
            entry.docs_status = CoverageStatus.EXACT
            entry.docs_url = docs_exact.url
        elif is_member and docs_parent:
            entry.docs_status = CoverageStatus.INHERITED
            entry.docs_url = docs_parent.url
            entry.inherited_from = parent
        else:
            entry.docs_status = CoverageStatus.MISSING

        if tut_exact:
            entry.tutorials_status = CoverageStatus.EXACT
            entry.tutorial_url = tut_exact.url
        elif is_member and tut_parent:
            entry.tutorials_status = CoverageStatus.INHERITED
            entry.tutorial_url = tut_parent.url
            entry.inherited_from = entry.inherited_from or parent
        else:
            entry.tutorials_status = CoverageStatus.MISSING

        blogs = blog_exact or (blog_parent if is_member else [])
        if blog_exact:
            entry.blogs_status = CoverageStatus.EXACT
        elif is_member and blog_parent:
            entry.blogs_status = CoverageStatus.INHERITED
            entry.inherited_from = entry.inherited_from or parent
        else:
            entry.blogs_status = CoverageStatus.MISSING

        entry.blog_urls = [b.url for b in blogs if b.url]

        entry.in_docs = entry.docs_status != CoverageStatus.MISSING
        entry.in_tutorials = entry.tutorials_status != CoverageStatus.MISSING
        entry.in_blogs = entry.blogs_status != CoverageStatus.MISSING

        return entry

    # -----------------------------
    # ✅ New behavior: type clusters
    # -----------------------------
    def _collect_type_clusters(self, categories: Dict[str, CategoryNode]) -> Dict[str, _TypeCluster]:
        """
        Walk API categories and bucket all topics into one cluster per type.

        IMPORTANT:
        API reference often nests members under sub-categories like:
          Aboveaverage > Isaboveaverage  (member)
        while the type lives at:
          Aboveaverage                  (class)
        If we include full path, members won't collapse into the type cluster.
        """
        clusters: Dict[str, _TypeCluster] = {}

        def walk(cats: Dict[str, CategoryNode], parent: List[str]) -> None:
            for cat_name, cat in cats.items():
                current_path = parent + [cat_name]

                for topic in cat.topics:
                    raw_title = topic.title or topic.file_path or ""
                    core = self._strip_kind_prefix(raw_title).strip()
                    if not core:
                        continue

                    is_member = "." in core
                    type_name = core.split(".")[0] if is_member else core

                    # ✅ KEY FIX: drop member leaf category to align with type category
                    # Example:
                    #   path: ["Aspose.Cells","Aboveaverage","Isaboveaverage"] + member => cluster_path becomes ["Aspose.Cells","Aboveaverage"]
                    cluster_path = current_path[:-1] if (is_member and len(current_path) > 1) else current_path

                    key = f"{' > '.join(cluster_path)}::{type_name}".lower()
                    cluster = clusters.get(key)
                    if not cluster:
                        cluster = _TypeCluster(category_path=cluster_path, type_name=type_name)
                        clusters[key] = cluster

                    # Prefer type-level URL if we see it (Class X / Enum X topic usually not member)
                    if (not is_member) and topic.url and not cluster.type_url:
                        cluster.type_url = topic.url

                    cluster.members.append(topic)

                walk(cat.sub_categories, current_path)

        walk(categories, [])
        logger.info("Type clustering: %d clusters built from API topics", len(clusters))
        return clusters

    def _create_type_cluster_entry(
        self,
        category_path: List[str],
        cluster: _TypeCluster,
        docs_topics: Dict[str, List[TopicEntry]],
        blog_topics: Dict[str, List[TopicEntry]],
        tutorials_topics: Dict[str, List[TopicEntry]],
    ) -> CoverageEntry:
        """
        Match coverage for a type cluster.
        We match:
          - type aliases (preferred)
          - plus a limited sample of member aliases (fallback)
        """
        type_aliases = self._aliases(cluster.type_name)

        # Member aliases can improve recall, but don't let it explode CPU.
        member_aliases: Set[str] = set()
        for t in cluster.members[:50]:  # hard cap
            raw = t.title or t.file_path or ""
            core = self._strip_kind_prefix(raw).strip()
            if core:
                member_aliases |= self._aliases(core)

        # For docs/tutorials: prefer type match; fallback to member match.
        docs_type = self._match_one(type_aliases, docs_topics)
        docs_member = None if docs_type else self._match_one(member_aliases, docs_topics)

        tut_type = self._match_one(type_aliases, tutorials_topics)
        tut_member = None if tut_type else self._match_one(member_aliases, tutorials_topics)

        # For blogs: collect multiple hits
        blog_type = self._match_many(type_aliases, blog_topics)
        blog_member = [] if blog_type else self._match_many(member_aliases, blog_topics)

        entry = CoverageEntry(
            category_path=category_path,
            topic_title=cluster.display_title,
            in_api=True,
            api_url=cluster.type_url or (cluster.members[0].url if cluster.members and cluster.members[0].url else None),
        )

        if docs_type:
            entry.docs_status = CoverageStatus.EXACT
            entry.docs_url = docs_type.url
        elif docs_member:
            entry.docs_status = CoverageStatus.INHERITED  # reuse status to mean "covered via member/topic"
            entry.docs_url = docs_member.url
            entry.inherited_from = cluster.type_name
        else:
            entry.docs_status = CoverageStatus.MISSING

        if tut_type:
            entry.tutorials_status = CoverageStatus.EXACT
            entry.tutorial_url = tut_type.url
        elif tut_member:
            entry.tutorials_status = CoverageStatus.INHERITED
            entry.tutorial_url = tut_member.url
            entry.inherited_from = entry.inherited_from or cluster.type_name
        else:
            entry.tutorials_status = CoverageStatus.MISSING

        blogs = blog_type or blog_member
        if blog_type:
            entry.blogs_status = CoverageStatus.EXACT
        elif blog_member:
            entry.blogs_status = CoverageStatus.INHERITED
            entry.inherited_from = entry.inherited_from or cluster.type_name
        else:
            entry.blogs_status = CoverageStatus.MISSING

        entry.blog_urls = [b.url for b in blogs if b.url]

        entry.in_docs = entry.docs_status != CoverageStatus.MISSING
        entry.in_tutorials = entry.tutorials_status != CoverageStatus.MISSING
        entry.in_blogs = entry.blogs_status != CoverageStatus.MISSING

        return entry

    def generate_markdown_report(
            self,
            matrix: CoverageMatrix,
            output_path: str = None,
    ) -> str:
        """
        Generate a markdown report from a coverage matrix.

        Format:
        | NO | Product | Platform | Category | Sub-Category | Topic | Docs | Blog | Tutorial |
        """
        if output_path is None:
            filename = f"{matrix.brand}_{matrix.product}_{matrix.platform}_coverage.md"
            output_path = self.output_dir / matrix.brand / filename
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Coverage Report: {matrix.product_display_name} - {matrix.platform_display_name}",
            "",
            f"Generated: {matrix.generated_at}",
            "",
            "## Summary",
            "",
        ]

        stats = matrix.get_coverage_stats()
        lines.extend([
            f"- **Total Topics**: {stats['total']}",
            f"- **Covered in Docs**: {stats['docs']} ({stats.get('docs_percent', 0)}%)",
            f"- **Covered in Blogs**: {stats['blogs']} ({stats.get('blogs_percent', 0)}%)",
            f"- **Covered in Tutorials**: {stats['tutorials']} ({stats.get('tutorials_percent', 0)}%)",
            "",
            "## Coverage Matrix",
            "",
            "| NO | Product | Platform | Category | Sub-Category | Topic | Docs | Blog | Tutorial |",
            "|---:|---------|----------|----------|--------------|-------|:----:|:----:|:--------:|",
        ])

        for i, entry in enumerate(matrix.entries, 1):
            category = entry.category_path[0] if entry.category_path else ""
            sub_category = " > ".join(entry.category_path[1:]) if len(entry.category_path) > 1 else ""

            docs_mark = entry.docs_status.mark()
            blog_mark = entry.blogs_status.mark()
            tutorial_mark = entry.tutorials_status.mark()

            topic_title = entry.topic_title[:50] + "..." if len(entry.topic_title) > 50 else entry.topic_title

            lines.append(
                f"| {i} | {matrix.product_display_name} | {matrix.platform_display_name} | "
                f"{category} | {sub_category} | {topic_title} | {docs_mark} | {blog_mark} | {tutorial_mark} |"
            )

        lines.extend([
            "",
            "## Gaps (Not Covered in Blogs)",
            "",
            "Topics that exist in API but have no blog coverage:",
            "",
        ])

        gaps = [e for e in matrix.entries if not e.in_blogs]
        for entry in gaps[:20]:
            category_str = " > ".join(entry.category_path)
            lines.append(f"- **{entry.topic_title}** ({category_str})")

        if len(gaps) > 20:
            lines.append(f"\n... and {len(gaps) - 20} more gaps")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("Saved coverage report to %s", output_path)
        return str(output_path)

    def save_matrix_json(self, matrix: CoverageMatrix, output_path: str = None) -> str:
        """Save coverage matrix as JSON."""
        if output_path is None:
            filename = f"{matrix.brand}_{matrix.product}_{matrix.platform}_coverage.json"
            output_path = self.output_dir / matrix.brand / filename
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(matrix.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info("Saved coverage matrix JSON to %s", output_path)
        return str(output_path)
