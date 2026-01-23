from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from agent_engine.content_gap_agent.tools.normalize import nor_website_domain
from .settings import CoverageSettings
from .agent import CoverageRunRequest, run_sync
from .tools.logging_utils import get_logger
from .tools.prerequisites import PrerequisiteError

logger = get_logger("cg-cover.cli")


def load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid brand yaml: {path}")
    if not data.get("key"):
        raise ValueError(f"Yaml missing 'key': {path}")
    return data


def build_parser() -> argparse.ArgumentParser:
    # supported_cases = list_supported_cases()

    p = argparse.ArgumentParser(prog="cg-cover", description="Content Gap Coverage Map CLI")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Compute coverage maps and write JSON/MD outputs")
    run.add_argument("--brand", required=True, type=Path, help="Path to brand yaml (e.g., configs/aspose.yaml)")
    run.add_argument("--product", required=True, type=Path, help="Path to product yaml (e.g., configs/aspose/cells.yaml)")
    run.add_argument(
        "--case",
        required=True,
        choices=["docs_to_blogs", "docs_to_tutorials", "blogs_to_blogs"],
        help=f"Coverage case. Supported: {'blogs_to_blogs, docs_to_blogs '}",
    )
    run.add_argument("--platform", required=False, help="Baseline platform (e.g., net)")
    run.add_argument("--threshold-strict", type=float, default=0.86)
    run.add_argument("--threshold-loose", type=float, default=0.80)
    run.add_argument("--top-k", type=int, default=5)
    run.add_argument("--platforms", default="", help="Optional comma-separated platform limit (blogs_to_blogs)")
    run.add_argument("--no-embeddings", action="store_true", help="Force lexical-only fallback (Step 2 will use this)")

    return p


def _resolve_outputs_root(brand_data: Dict[str, Any], brand_yaml_path: Path) -> Path:
    """
    Resolve outputs_root from brand yaml.
    - If missing: default to 'outputs'
    - If relative: resolve relative to the brand yaml directory
    """
    raw = (brand_data.get("outputs_root") or "outputs")
    p = Path(str(raw))
    if not p.is_absolute():
        p = (brand_yaml_path.parent / p).resolve()
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command != "run":
        return 1

    # Load brand config
    brand_yaml_path: Path = args.brand
    try:
        brand_data = load_yaml(brand_yaml_path)
    except Exception as e:
        logger.error("Failed to load brand yaml: %s (%s)", brand_yaml_path, e)
        return 2

    brand_key = str(brand_data["key"]).strip()
    if not brand_key:
        logger.error("Brand yaml key is empty: %s", brand_yaml_path)
        return 2

    # Load product config
    product_yaml_path: Path = args.product
    try:
        product_data = load_yaml(product_yaml_path)
    except Exception as e:
        logger.error("Failed to load product yaml: %s (%s)", product_yaml_path, e)
        return 2

    product_key = str(product_data["key"]).strip()
    if not product_key:
        logger.error("Product yaml key is empty: %s", product_yaml_path)
        return 2

    website = str(brand_data["website"]).strip()
    brand_site = nor_website_domain(str(website))

    product_name = str(product_data["display_name"]).strip()

    # Apply outputs_root from brand yaml (repos under outputs/_repos; products under outputs/{brand}/{product})
    outputs_root = _resolve_outputs_root(brand_data, brand_yaml_path)
    logger.info("Brand resolved: key=%s yaml=%s outputs_root=%s", brand_key, brand_yaml_path, outputs_root)

    effective_platform = args.platform.strip() if args.platform else None

    # NOTE: today only blogs_to_blogs is supported, and it does NOT require --platform.
    # Keep this defensive for the day you add docs_to_* / api_coverage.
    if args.case != "blogs_to_blogs" and not effective_platform:
        logger.error("Error: --platform is required for case '%s'.", args.case)
        return 2

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()] if args.platforms else None

    req = CoverageRunRequest(
        brand_key=brand_key,
        brand_site=brand_site,
        product_key=product_key,
        product_name=product_name,
        case=args.case,
        baseline_platform=effective_platform,
        threshold_strict=args.threshold_strict,
        threshold_loose=args.threshold_loose,
        top_k=args.top_k,
        platforms=platforms,
        no_embeddings=bool(args.no_embeddings),
    )

    logger.info(
        "Coverage request: brand=%s product=%s case=%s baseline=%s platforms_limit=%s no_embeddings=%s",
        req.brand_key,
        req.product_name,
        req.case,
        req.baseline_platform or "all",
        ",".join(req.platforms) if req.platforms else "None",
        req.no_embeddings,
    )

    try:
        settings = CoverageSettings()
        summary = run_sync(settings, req)
    except PrerequisiteError as e:
        logger.error(str(e))
        return 2
    except NotImplementedError as e:
        logger.error(str(e))
        return 3
    except Exception:
        logger.exception("Coverage failed unexpectedly")
        return 4

    logger.info("Coverage completed: out_dir=%s topics=%s", summary.get("out_dir"), summary.get("topics"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
