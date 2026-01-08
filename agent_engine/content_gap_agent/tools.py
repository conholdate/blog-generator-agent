# content_gap_agent/agents/tools.py
"""
Agents SDK function tools.

These tools are thin wrappers around TopicAnalyzerService.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents import function_tool

from .services.content_gap_service import TopicAnalyzerService

_SERVICE: Optional[TopicAnalyzerService] = None


def init_service(config_dir: str, cache_dir: str, output_dir: str) -> None:
    """Initialize the singleton service used by tools."""
    global _SERVICE
    _SERVICE = TopicAnalyzerService(config_dir=config_dir, cache_dir=cache_dir, output_dir=output_dir)


def _svc() -> TopicAnalyzerService:
    if _SERVICE is None:
        raise RuntimeError("Service not initialized. Call init_service() first.")
    return _SERVICE


@function_tool
def flush_everything() -> str:
    """Delete cache + output directories."""
    _svc().flush()
    return "Flushed cache and output directories."


@function_tool
def list_targets(blog: str, product: str | None = None, platform: str | None = None) -> Dict[str, Any]:
    """List enabled analysis targets from config."""
    svc = _svc()
    products = svc.select_products(blog, product)

    targets: List[tuple[str, str, str]] = []
    for prod_name, prod_cfg in products.items():
        for p in prod_cfg.get_enabled_platforms():
            if platform and p.name != platform:
                continue
            targets.append((blog, prod_name, p.name))

    return {"targets": targets, "count": len(targets)}


@function_tool
def clone_repos(blog: str, product: str) -> Dict[str, str]:
    """Clone/update repos for blog+product."""
    return _svc().clone_repos(blog, product)


@function_tool
def index_all(blog: str, product: str, platform: str | None = None) -> Dict[str, str]:
    """Index docs/api/tutorials/blogs and save JSON indexes."""
    return _svc().index_all(blog=blog, product=product, platform_filter=platform)


@function_tool
def generate_coverage(blog: str, product: str, platform: str | None = None) -> List[str]:
    """Generate coverage matrices (MD + JSON)."""
    return _svc().generate_coverage(blog=blog, product=product, platform_filter=platform)


@function_tool
def list_coverage_json(blog: str, product: str) -> List[str]:
    """List saved coverage matrix JSON files."""
    return _svc().list_coverage_json(blog, product)


@function_tool
def summarize_coverage_gaps(coverage_json_path: str, max_missing: int = 200) -> Dict[str, Any]:
    """Summarize coverage gaps from a coverage matrix JSON."""
    return _svc().summarize_coverage_gaps(coverage_json_path, max_missing=max_missing)


@function_tool
def write_markdown(rel_path: str, markdown: str) -> str:
    """Write markdown under output_dir/<rel_path> safely."""
    return _svc().write_markdown(rel_path, markdown)

@function_tool
def generate_gap_reports(blog: str, product: str, max_missing: int = 200) -> List[str]:
    """Deterministically generate gap report markdown files from coverage JSONs."""
    return _svc().generate_gap_reports(blog=blog, product=product, max_missing=max_missing)
