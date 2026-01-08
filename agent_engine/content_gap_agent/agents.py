"""
Agents + shared pipeline runner for Content Gap Analyzer.

Requirements implemented:
- Modes: index / coverage / analyze kept
- run-all: Index -> Coverage -> Gap Analysis
- flush + force
- Everything scoped to a SINGLE (brand, product, platform) per invocation
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from .services.content_gap_service import TopicAnalyzerService
from .services.metrics_service import get_metrics_service, MetricsContext

logger = logging.getLogger(__name__)

PipelineMode = Literal["index", "coverage", "semantic-coverage", "semantic-analyze", "analyze", "run-all"]


@dataclass(frozen=True)
class PipelineOptions:
    case: str = "docs_to_blogs"
    flush: bool = False
    force: bool = False
    # Optional overrides via env vars
    config_dir: Path = Path(os.getenv("BTA_CONFIG_DIR", "config"))
    cache_dir: Path = Path(os.getenv("BTA_CACHE_DIR", "repo_cache"))
    output_dir: Path = Path(os.getenv("BTA_OUTPUT_DIR", "outputs"))
    state_dir: Path = Path(os.getenv("BTA_STATE_DIR", ".bta_state"))


@dataclass(frozen=True)
class PipelinePaths:
    cache_root: Path
    output_root: Path
    state_root: Path
    brand: str
    product: str
    platform: str

    @property
    def cache_scope(self) -> Path:
        return self.cache_root / self.brand / self.product / self.platform

    @property
    def output_scope(self) -> Path:
        return self.output_root / self.brand / self.product / self.platform

    @property
    def state_scope(self) -> Path:
        return self.state_root / self.brand / self.product / self.platform

    def marker(self, step: str) -> Path:
        return self.state_scope / f"{step}.done"


def _safe_rmtree(path: Path) -> None:
    if not path.exists():
        return
    resolved = path.resolve()
    if resolved == resolved.root or len(resolved.parts) < 2:
        raise RuntimeError(f"Refusing to delete suspicious path: {resolved}")
    shutil.rmtree(resolved, ignore_errors=True)


def _flush_for_scope(paths: PipelinePaths) -> None:
    """
    Flush ONLY scoped data for this (brand, product, platform).
    """
    logger.info(
        "Flushing scoped cache/output/state for %s/%s/%s",
        paths.brand,
        paths.product,
        paths.platform,
    )
    _safe_rmtree(paths.cache_scope)
    _safe_rmtree(paths.output_scope)
    _safe_rmtree(paths.state_scope)


def _is_done(paths: PipelinePaths, step: str) -> bool:
    return paths.marker(step).exists()


def _mark_done(paths: PipelinePaths, step: str) -> None:
    paths.state_scope.mkdir(parents=True, exist_ok=True)
    paths.marker(step).write_text("ok\n", encoding="utf-8")


def _get_service(paths: PipelinePaths, options: PipelineOptions) -> TopicAnalyzerService:
    """Create a TopicAnalyzerService instance with scoped paths."""
    return TopicAnalyzerService(
        config_dir=str(options.config_dir),
        cache_dir=str(paths.cache_root),
        output_dir=str(paths.output_root),
    )


def _run_index(brand: str, product: str, platform: str, options: PipelineOptions, paths: PipelinePaths) -> Any:
    """Clone repositories and build indexes for the specified brand/product/platform."""
    step = "index"
    if _is_done(paths, step) and not options.force:
        logger.info("Skipping %s (already done). Use --force to re-run.", step)
        return {"step": step, "status": "skipped"}

    service = _get_service(paths, options)

    # Clone repos and index
    logger.info("Cloning repositories for %s/%s...", brand, product)
    repos = service.clone_repos(brand, product)
    logger.info("Cloned repos: %s", list(repos.keys()))

    logger.info("Indexing content for %s/%s/%s...", brand, product, platform)
    result = service.index_all(blog=brand, product=product, platform_filter=platform)
    logger.info("Indexed: %s", result)

    _mark_done(paths, step)
    return {"step": step, "status": "ok", "result": {"repos": repos, "indexes": result}}


def _run_coverage(brand: str, product: str, platform: str, options: PipelineOptions, paths: PipelinePaths) -> Any:
    """Generate coverage matrix for the specified brand/product/platform."""
    step = "coverage"
    if _is_done(paths, step) and not options.force:
        logger.info("Skipping %s (already done). Use --force to re-run.", step)
        return {"step": step, "status": "skipped"}

    metrics = get_metrics_service()
    ctx = metrics.start_step(brand, product, platform, step)

    service = _get_service(paths, options)
    success = True

    try:
        logger.info("Generating coverage for %s/%s/%s...", brand, product, platform)
        result = service.generate_coverage(blog=brand, product=product, platform_filter=platform)
        logger.info("Coverage reports: %s", result)

        ctx.record_discovered(1)  # 1 coverage matrix
        ctx.record_success(len(result))  # Number of reports generated

        _mark_done(paths, step)
        return {"step": step, "status": "ok", "result": result}

    except Exception as e:
        success = False
        ctx.record_failure(1)
        raise

    finally:
        metrics.complete_step(ctx, success=success)


def _run_semantic_coverage(brand: str, product: str, platform: str, options: PipelineOptions, paths: PipelinePaths) -> Any:
    """Generate semantic coverage matrix for the specified brand/product/platform."""
    step = f"semantic-coverage-{options.case}"
    if _is_done(paths, step) and not options.force:
        logger.info("Skipping %s (already done). Use --force to re-run.", step)
        return {"step": step, "status": "skipped"}

    metrics = get_metrics_service()
    ctx = metrics.start_step(brand, product, platform, f"semantic-coverage:{options.case}")

    service = _get_service(paths, options)
    success = True

    try:
        logger.info("Generating semantic coverage (%s) for %s/%s/%s...", options.case, brand, product, platform)
        result = service.generate_semantic_coverage(blog=brand, product=product, platform_filter=platform, case=options.case)
        logger.info("Coverage reports: %s", result)

        ctx.record_discovered(1)  # 1 semantic coverage matrix
        ctx.record_success(len(result))  # Number of reports generated

        _mark_done(paths, step)
        return {"step": step, "status": "ok", "result": result}

    except Exception as e:
        success = False
        ctx.record_failure(1)
        raise

    finally:
        metrics.complete_step(ctx, success=success)


def _run_semantic_analyze(brand: str, product: str, platform: str, options: PipelineOptions, paths: PipelinePaths) -> Any:
    """Run AI gap analysis on semantic coverage for the specified brand/product/platform/case."""
    step = f"semantic-analyze-{options.case}"
    if _is_done(paths, step) and not options.force:
        logger.info("Skipping %s (already done). Use --force to re-run.", step)
        return {"step": step, "status": "skipped"}

    metrics = get_metrics_service()
    ctx = metrics.start_step(brand, product, platform, f"semantic-analyze:{options.case}")

    service = _get_service(paths, options)
    success = True

    try:
        logger.info("Running semantic AI gap analysis (%s) for %s/%s/%s...", options.case, brand, product, platform)
        result = service.analyze_semantic_with_llm(
            blog=brand,
            product=product,
            case=options.case,
            platform_filter=platform,
        )
        logger.info("Semantic gap analysis reports: %s", result)

        ctx.record_discovered(1)  # 1 analysis run
        ctx.record_success(len(result))  # Number of reports generated

        _mark_done(paths, step)
        return {"step": step, "status": "ok", "result": result}

    except Exception as e:
        success = False
        ctx.record_failure(1)
        raise

    finally:
        metrics.complete_step(ctx, success=success)


def _run_analyze(brand: str, product: str, platform: str, options: PipelineOptions, paths: PipelinePaths) -> Any:
    """Run AI-powered gap analysis for the specified brand/product/platform."""
    step = "analyze"
    if _is_done(paths, step) and not options.force:
        logger.info("Skipping %s (already done). Use --force to re-run.", step)
        return {"step": step, "status": "skipped"}

    metrics = get_metrics_service()
    ctx = metrics.start_step(brand, product, platform, step)

    service = _get_service(paths, options)
    success = True

    try:
        logger.info("Running AI gap analysis for %s/%s/%s...", brand, product, platform)
        result = service.analyze_with_llm(blog=brand, product=product, platform_filter=platform)
        logger.info("Gap analysis reports: %s", result)

        ctx.record_discovered(1)  # 1 analysis run
        ctx.record_success(len(result))  # Number of reports generated

        _mark_done(paths, step)
        return {"step": step, "status": "ok", "result": result}

    except Exception as e:
        success = False
        ctx.record_failure(1)
        raise

    finally:
        metrics.complete_step(ctx, success=success)


def run_pipeline(
    brand: str,
    product: str,
    platform: str,
    mode: PipelineMode,
    options: PipelineOptions,
) -> Dict[str, Any]:
    """
    Deterministic pipeline runner scoped to ONE (brand, product, platform).

    Behavior:
    - If options.flush: deletes scoped cache/output/state first.
    - If options.force: re-runs steps even if marked done.
    - run-all: index -> coverage -> analyze
    """
    brand = brand.strip()
    product = product.strip()
    platform = platform.strip()
    if not brand or not product or not platform:
        raise ValueError("brand, product, and platform must be non-empty strings")

    paths = PipelinePaths(
        cache_root=options.cache_dir,
        output_root=options.output_dir,
        state_root=options.state_dir,
        brand=brand,
        product=product,
        platform=platform,
    )

    if options.flush:
        _flush_for_scope(paths)

    # Ensure scoped dirs exist
    paths.cache_scope.mkdir(parents=True, exist_ok=True)
    paths.output_scope.mkdir(parents=True, exist_ok=True)
    paths.state_scope.mkdir(parents=True, exist_ok=True)

    out: Dict[str, Any] = {
        "brand": brand,
        "product": product,
        "platform": platform,
        "mode": mode,
        "steps": [],
    }

    if mode == "index":
        out["steps"].append(_run_index(brand, product, platform, options, paths))
        return out

    if mode == "coverage":
        out["steps"].append(_run_coverage(brand, product, platform, options, paths))
        return out

    if mode == "semantic-coverage":
        out["steps"].append(_run_semantic_coverage(brand, product, platform, options, paths))
        return out

    if mode == "semantic-analyze":
        out["steps"].append(_run_semantic_analyze(brand, product, platform, options, paths))
        return out

    if mode == "analyze":
        out["steps"].append(_run_analyze(brand, product, platform, options, paths))
        return out

    if mode == "run-all":
        out["steps"].append(_run_index(brand, product, platform, options, paths))
        out["steps"].append(_run_coverage(brand, product, platform, options, paths))
        out["steps"].append(_run_analyze(brand, product, platform, options, paths))
        return out

    raise ValueError(f"Unknown mode: {mode}")


# -------------------------
# OpenAI Agents SDK section
# -------------------------
try:
    from agents import Agent, Runner, function_tool
except Exception:  # pragma: no cover
    from openai_agents import Agent, Runner, function_tool  # type: ignore


@function_tool
def run_index_tool(
    brand: str,
    product: str,
    platform: str,
    flush: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Run Index step for a single brand+product+platform."""
    return run_pipeline(brand, product, platform, "index", PipelineOptions(flush=flush, force=force))


@function_tool
def run_coverage_tool(
    brand: str,
    product: str,
    platform: str,
    flush: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Run Coverage step for a single brand+product+platform."""
    return run_pipeline(brand, product, platform, "coverage", PipelineOptions(flush=flush, force=force))


@function_tool
def run_semantic_coverage_tool(
    brand: str,
    product: str,
    platform: str,
    case: str,
    flush: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Run Semantic Coverage step for a single brand+product+platform."""
    return run_pipeline(brand, product, platform, "semantic-coverage", PipelineOptions(case, flush=flush, force=force))


@function_tool
def run_semantic_analyze_tool(
    brand: str,
    product: str,
    platform: str,
    case: str,
    flush: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Run Semantic AI Gap Analysis for a single brand+product+platform."""
    return run_pipeline(brand, product, platform, "semantic-analyze", PipelineOptions(case, flush=flush, force=force))


@function_tool
def run_analyze_tool(
    brand: str,
    product: str,
    platform: str,
    flush: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Run Analyze (gap analysis) step for a single brand+product+platform."""
    return run_pipeline(brand, product, platform, "analyze", PipelineOptions(flush=flush, force=force))


@function_tool
def run_all_tool(
    brand: str,
    product: str,
    platform: str,
    flush: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Run full pipeline (Index -> Coverage -> Analyze) for a single brand+product+platform."""
    return run_pipeline(brand, product, platform, "run-all", PipelineOptions(flush=flush, force=force))


IndexAgent = Agent(
    name="IndexAgent",
    instructions=(
        "Build/refresh indexes for EXACTLY one brand, one product, and one platform. "
        "Never run across multiple targets. Use the tool."
    ),
    tools=[run_index_tool],
)

CoverageAgent = Agent(
    name="CoverageAgent",
    instructions=(
        "Compute coverage for EXACTLY one brand, one product, and one platform. "
        "Never run across multiple targets. Use the tool."
    ),
    tools=[run_coverage_tool],
)


SemanticCoverageAgent = Agent(
    name="SemanticCoverageAgent",
    instructions=(
        "Compute semantic coverage for EXACTLY one brand, one product, one platform, and one case. "
        "Never run across multiple targets. Use the tool."
    ),
    tools=[run_semantic_coverage_tool],
)

SemanticAnalyzeAgent = Agent(
    name="SemanticAnalyzeAgent",
    instructions=(
        "Run AI gap analysis on semantic coverage for EXACTLY one brand, one product, one platform, and one case. "
        "Never run across multiple targets. Use the tool."
    ),
    tools=[run_semantic_analyze_tool],
)

AnalyzeAgent = Agent(
    name="AnalyzeAgent",
    instructions=(
        "Perform gap analysis for EXACTLY one brand, one product, and one platform. "
        "Never run across multiple targets. Use the tool."
    ),
    tools=[run_analyze_tool],
)

OrchestratorAgent = Agent(
    name="PipelineOrchestrator",
    instructions=(
        "Run the blog topic analyzer pipeline for a SINGLE brand+product+platform.\n"
        "If full pipeline requested, call run_all_tool.\n"
        "If only one step requested, call the matching tool.\n"
        "Always respect flush/force flags."
    ),
    tools=[run_all_tool, run_index_tool, run_coverage_tool, run_analyze_tool],
)


def run_agent_sync(prompt: str) -> Any:
    """
    Synchronous example using Runner.run_sync().
    """
    return Runner.run_sync(OrchestratorAgent, prompt)


if __name__ == "__main__":
    # Example usage
    result = run_agent_sync("Run full pipeline for brand=aspose product=cells platform=net flush=false force=false")
    print(result.final_output)
