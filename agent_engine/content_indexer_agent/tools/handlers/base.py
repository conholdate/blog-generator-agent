from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI

from ...settings import Settings
from ...types import IndexRecord, RepoTarget
from ..text_utils import ParsedMarkdown


@dataclass(frozen=True)
class HandlerContext:
    """
    Shared context passed to handlers.
    """
    settings: Settings
    client: OpenAI
    brand_key: str
    product_key: str
    platform_for_record: str  # 'all' for scope=all repos, else the selected platform key
    normalize_topics: bool = False

class MarkdownRepoHandler(ABC):
    """
    A handler processes markdown files for a specific repo_type (or generic).
    The indexer remains incremental + generic; handlers decide inclusion and record shape.
    """

    name: str = "markdown"

    def get_scan_base(
        self,
        *,
        base: Path,
        repo_target: RepoTarget,
        product_key: str,
    ) -> Path:
        """
        Optionally narrow scanning to a subtree. Default: scan full base.
        IMPORTANT: relpaths should still be computed relative to `base` in the indexer.
        """
        return base

    @abstractmethod
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
        """
        Decide if a file belongs in the index. Returns (include, reason_if_excluded).
        """

    @abstractmethod
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
        """
        Build IndexRecord for a file that should be included.
        """
