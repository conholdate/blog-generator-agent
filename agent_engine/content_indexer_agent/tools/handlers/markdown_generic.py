from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

from ...types import IndexRecord, RepoTarget
from ..text_utils import ParsedMarkdown, normalize_ws, extract_subheadings
from .base import HandlerContext, MarkdownRepoHandler
from ..record_id import RecordId


class GenericMarkdownHandler(MarkdownRepoHandler):
    """
    Generic handler for docs/tutorials/api/any other markdown repo.
    Deterministic taxonomy from path segments.
    """

    name = "generic_markdown"

    def should_include(
        self,
        *,
        parsed: ParsedMarkdown,
        raw_for_match: str,
        relpath: str,
        repo_target: RepoTarget,
        brand: Any,
        product: Any,
        ctx: HandlerContext,
        scan_base: Path,
        base: Path,
    ) -> Tuple[bool, str]:
        return True, ""

    def build_record(
        self,
        *,
        parsed: ParsedMarkdown,
        relpath: str,
        repo_target: RepoTarget,
        brand: Any,
        product: Any,
        ctx: HandlerContext,
    ) -> IndexRecord:
        fm = parsed.frontmatter or {}

        if not ctx.normalize_topics:
            headings = extract_subheadings(parsed.body, max_items=30)

            category = fm.get("category") or fm.get("categories") or "General"
            subcat = fm.get("sub_category") or fm.get("subcategory") or "General"
            topic = fm.get("topic") or fm.get("title") or parsed.title

            tags = fm.get("tags") or fm.get("tag") or ""
            if isinstance(tags, str):
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            elif isinstance(tags, list):
                tag_list = [str(t).strip() for t in tags if str(t).strip()]
            else:
                tag_list = []

            keywords = sorted(set(tag_list + headings))

            return IndexRecord(
                id=RecordId.for_markdown(repo_key=repo_target.repo_key, platform=ctx.platform_for_record,
                                         relpath=relpath),
                brand=ctx.brand_key,
                product=ctx.product_key,
                repo_key=repo_target.repo_key,
                repo_type=repo_target.repo_type,
                platform=ctx.platform_for_record,
                title=parsed.title[:300],
                topic=str(topic)[:200],
                category=str(category)[:100],
                sub_category=str(subcat)[:100],
                url=None,
                source_path=relpath,
                excerpt=normalize_ws(parsed.body[:400]),
                keywords=keywords,
            )

        # Current implementation (path-based taxonomy)
        parts = list(Path(relpath).parts)
        category = parts[0].replace("-", " ").title() if len(parts) >= 2 else "General"
        subcat = parts[1].replace("-", " ").title() if len(parts) >= 3 else "General"

        return IndexRecord(
            id=RecordId.for_markdown(repo_key=repo_target.repo_key, platform=ctx.platform_for_record,
                                     relpath=relpath),
            brand=ctx.brand_key,
            product=ctx.product_key,
            repo_key=repo_target.repo_key,
            repo_type=repo_target.repo_type,
            platform=ctx.platform_for_record,
            title=parsed.title[:300],
            topic=parsed.title[:200],
            category=category[:100],
            sub_category=subcat[:100],
            url=None,
            source_path=relpath,
            excerpt=normalize_ws(parsed.body[:400]),
            keywords=[],
        )
