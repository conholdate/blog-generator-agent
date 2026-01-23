from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from ..types import RepoTarget


class BrandSpec(BaseModel):
    key: str
    display_name: str
    website: Optional[str] = None
    enabled: bool = True

    # Legacy blog repo fields
    blog_repo: Optional[str] = None
    blog_branch: str = "master"
    search_patterns: List[str] = Field(default_factory=list)

    # Future-ready generic repos
    repositories: List[Dict[str, Any]] = Field(default_factory=list)


class PlatformDefinition(BaseModel):
    display_name: str
    keywords: List[str] = Field(default_factory=list)


class PlatformSpec(BaseModel):
    key: str
    enabled: bool = True
    definition: str
    doc_path: Optional[str] = None
    tut_path: Optional[str] = None
    api_path: Optional[str] = None


class ProductSpec(BaseModel):
    display_name: str
    enabled: bool = True
    description: Optional[str] = None

    # Brand key
    blog: str

    # Legacy repo fields
    doc_repo: Optional[str] = None
    doc_branch: str = "master"
    tut_repo: Optional[str] = None
    tut_branch: str = "master"
    api_repo: Optional[str] = None
    api_branch: str = "master"

    platform_definitions: Dict[str, PlatformDefinition] = Field(default_factory=dict)
    platforms: List[Dict[str, Dict[str, Any]]] = Field(default_factory=list)

    # Future-ready generic repos
    repositories: List[Dict[str, Any]] = Field(default_factory=list)

    def iter_platforms(self) -> List[PlatformSpec]:
        out: List[PlatformSpec] = []
        for entry in self.platforms:
            if not isinstance(entry, dict):
                continue
            for k, v in entry.items():
                out.append(PlatformSpec(key=k, **v))
        return out


def load_brand_yaml(path: Path) -> Dict[str, BrandSpec]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}

    # Backward/forward compatible:
    # - registry format: { blog: { aspose: {...}, ... } }  (your current expectation)
    # - older format:    { blogs: { aspose: {...}, ... } }
    # - single brand:    { key: aspose, ... } OR { brand_key: aspose, ... }
    if "blog" in data and isinstance(data["blog"], dict):
        brands_map = data["blog"]
        return {k: BrandSpec(key=k, **v) for k, v in brands_map.items() if isinstance(v, dict)}

    if "blogs" in data and isinstance(data["blogs"], dict):
        brands_map = data["blogs"]
        return {k: BrandSpec(key=k, **v) for k, v in brands_map.items() if isinstance(v, dict)}

    # Single-brand YAML support
    # If this looks like a BrandSpec document, construct one BrandSpec.
    if "key" in data or "brand_key" in data:
        key = str(data.get("key") or data.get("brand_key") or "").strip()
        if not key:
            return {}
        # Normalize field name so BrandSpec validation passes
        if "key" not in data and "brand_key" in data:
            data = dict(data)
            data["key"] = data.pop("brand_key")
        return {key: BrandSpec(**data)}

    # Unwrapped registry: { aspose: {...}, groupdocs: {...} }
    # Detect by values being dict-like BrandSpec bodies.
    out: Dict[str, BrandSpec] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            out[str(k)] = BrandSpec(key=str(k), **v)
    return out

def load_product_yaml(path: Path) -> ProductSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid product yaml: {path}")
    return ProductSpec(**data)


def find_product_yamls(products_dir: Path) -> List[Path]:
    return sorted([p for p in products_dir.rglob("*.yaml") if p.is_file()])


def product_key_from_yaml(path: Path) -> str:
    return path.stem


def build_repo_targets_for_product(brand: BrandSpec, product: ProductSpec) -> List[RepoTarget]:
    """
    Converts YAML repo definitions into a generic list of RepoTarget.

    Supports:
    - Future: brand.repositories + product.repositories
    - Legacy: brand.blog_repo + product.doc_repo/tut_repo/api_repo + per-platform paths

    Each RepoTarget becomes a selectable "step" via its repo_key.
    """
    targets: List[RepoTarget] = []

    # Future generic repos (brand-level)
    for r in (brand.repositories or []):
        targets.append(_repo_target_from_dict(r, default_type="brand_repo"))

    # Future generic repos (product-level)
    for r in (product.repositories or []):
        targets.append(_repo_target_from_dict(r, default_type="product_repo"))

    existing_keys = {t.repo_key for t in targets}

    # Legacy blogs
    if brand.blog_repo and "blog" not in existing_keys:
        targets.append(
            RepoTarget(
                repo_key="blog",
                repo_type="blog",
                repo_url=brand.blog_repo,
                branch=brand.blog_branch,
                scope="all",
                handler="blog",
            )
        )

    plats = [p for p in product.iter_platforms() if p.enabled]
    plat_paths_docs = {p.key: p.doc_path for p in plats}
    plat_paths_tut = {p.key: p.tut_path for p in plats}
    plat_paths_api = {p.key: p.api_path for p in plats}

    if product.doc_repo and "docs" not in existing_keys:
        targets.append(
            RepoTarget(
                repo_key="docs",
                repo_type="docs",
                repo_url=product.doc_repo,
                branch=product.doc_branch,
                scope="platform",
                platform_paths=plat_paths_docs,
            )
        )

    if product.tut_repo and "tutorials" not in existing_keys:
        targets.append(
            RepoTarget(
                repo_key="tutorials",
                repo_type="tutorials",
                repo_url=product.tut_repo,
                branch=product.tut_branch,
                scope="platform",
                platform_paths=plat_paths_tut,
            )
        )

    if product.api_repo and "api" not in existing_keys:
        targets.append(
            RepoTarget(
                repo_key="api",
                repo_type="api",
                repo_url=product.api_repo,
                branch=product.api_branch,
                scope="platform",
                platform_paths=plat_paths_api,
            )
        )

    targets.sort(key=lambda t: t.repo_key)
    return targets


def _repo_target_from_dict(d: Dict[str, Any], default_type: str) -> RepoTarget:
    """
    Flexible adapter for future YAML repository entries.

    Recommended fields in YAML:
      repo_key, repo_type, repo_url, branch, scope, root_subdir, platform_paths, include_globs

    Aliases accepted:
      key/name -> repo_key
      type -> repo_type
      repo/url -> repo_url
      paths -> platform_paths
      globs -> include_globs
    """
    repo_key = str(d.get("repo_key") or d.get("key") or d.get("name") or default_type)
    repo_type = str(d.get("repo_type") or d.get("type") or repo_key)
    repo_url = str(d.get("repo_url") or d.get("repo") or d.get("url"))
    branch = str(d.get("branch") or "master")
    scope = str(d.get("scope") or "all")
    kind = str(d.get("kind") or "markdown")
    root_subdir = d.get("root_subdir")
    platform_paths = d.get("platform_paths") or d.get("paths") or {}
    include_globs = d.get("include_globs") or d.get("globs") or ["**/*.md"]
    handler = d.get("handler")

    return RepoTarget(
        repo_key=repo_key,
        repo_type=repo_type,
        repo_url=repo_url,
        branch=branch,
        kind=kind,           # type: ignore[arg-type]
        scope=scope,         # type: ignore[arg-type]
        root_subdir=root_subdir,
        platform_paths=dict(platform_paths),
        include_globs=list(include_globs),
        handler=str(handler) if handler else None,
    )
