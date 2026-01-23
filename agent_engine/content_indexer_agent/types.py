from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


RepoScope = Literal["all", "platform"]
ContentKind = Literal["markdown"]


class IndexRecord(BaseModel):
    id: str
    brand: str
    product: str

    repo_key: str          # stable key used in CLI steps (e.g., blogs, docs, api, future keys)
    repo_type: str         # semantic type label (usually same as repo_key)
    platform: str          # platform key or 'all'/'general'

    title: str
    topic: str
    category: str = "General"
    sub_category: str = "General"

    url: Optional[str] = None
    source_path: str
    excerpt: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)

    embedding_key: Optional[str] = None
    embedding_model: Optional[str] = None

    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RepoTarget(BaseModel):
    # Identifies this repository in outputs and steps selection
    repo_key: str                 # stable selection key
    repo_type: str                # human semantic type
    repo_url: str
    branch: str = "master"

    kind: ContentKind = "markdown"
    scope: RepoScope = "all"      # 'all' or 'platform'

    # For platform-scoped repos, use a per-platform root subdir.
    platform_paths: Dict[str, Optional[str]] = Field(default_factory=dict)

    # For all-scoped repos (like blogs), optional base subdir.
    root_subdir: Optional[str] = None

    # What files to index
    include_globs: List[str] = Field(default_factory=lambda: ["**/*.md"])

    # Optional explicit handler name (otherwise resolved by repo_type)
    handler: Optional[str] = None