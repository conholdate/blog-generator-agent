"""
CLI for Content Gap Analyzer (scoped to ONE brand + product + platform)

Modes:
  --index       Build/update index for (brand, product, platform)
  --coverage    Compute coverage for (brand, product, platform)
  --analyze     Run gap analysis for (brand, product, platform)
  --run-all     Full pipeline: Index -> Coverage -> Gap Analysis

Flags:
  --flush       Delete cached/state/output for the given (brand, product, platform) only
  --force       Re-run steps even if they look “done”
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Optional

from .agents import PipelineMode, PipelineOptions, run_pipeline

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CliArgs:
    brand: str
    product: str
    platform: str
    mode: PipelineMode
    case: str
    flush: bool
    force: bool


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="blog-topic-analyzer",
        description="Run Content Gap Analyzer pipeline for a single brand + product + platform.",
    )

    # Keep backward compatibility: --blog alias
    p.add_argument(
        "--brand",
        "--blog",
        dest="brand",
        required=True,
        help="Brand/blog key (e.g., aspose, groupdocs, conholdate, familiarize).",
    )
    p.add_argument(
        "--product",
        dest="product",
        required=True,
        help="Product key (e.g., cells, words, pdf).",
    )
    p.add_argument(
        "--platform",
        dest="platform",
        required=True,
        help="Platform key (e.g., net, java, python).",
    )

    p.add_argument(
        "--case",
        dest="case",
        type=str,
        default="no_case",
        choices=["docs_to_blogs", "docs_to_tutorials", "blogs_to_blogs"],
        help="Semantic coverage case"
    )
    mode = p.add_mutually_exclusive_group(required=True)

    mode.add_argument("--semantic-coverage", action="store_true", help="Generate semantic coverage matrix")
    mode.add_argument("--semantic-analyze", action="store_true", help="Run AI gap analysis on semantic coverage")

    mode.add_argument("--index", action="store_true", help="Run indexing only.")
    mode.add_argument("--coverage", action="store_true", help="Run coverage only.")
    mode.add_argument("--analyze", action="store_true", help="Run gap analysis only.")
    mode.add_argument(
        "--run-all",
        action="store_true",
        help="Run full pipeline: Index -> Coverage -> Gap Analysis.",
    )

    p.add_argument(
        "--flush",
        action="store_true",
        help="Flush scoped cache/output/state for the given brand+product+platform only.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Force re-run even if a step is already marked complete.",
    )

    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv).",
    )
    return p


def _resolve_mode(ns: argparse.Namespace) -> PipelineMode:
    if ns.index:
        return "index"
    if ns.coverage:
        return "coverage"
    if ns.semantic_coverage:
        return "semantic-coverage"
    if ns.semantic_analyze:
        return "semantic-analyze"
    if ns.analyze:
        return "analyze"
    if ns.run_all:
        return "run-all"
    raise SystemExit("No mode selected (argparse should prevent this).")


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def parse_args(argv: Optional[list[str]] = None) -> CliArgs:
    parser = _build_parser()
    ns = parser.parse_args(argv)

    _configure_logging(ns.verbose)

    brand = str(ns.brand).strip()
    product = str(ns.product).strip()
    platform = str(ns.platform).strip()
    case = str(ns.case).strip()

    if not brand or not product or not platform:
        raise SystemExit("--brand, --product, and --platform are required and cannot be blank.")

    return CliArgs(
        brand=brand,
        product=product,
        platform=platform,
        mode=_resolve_mode(ns),
        case=case,
        flush=bool(ns.flush),
        force=bool(ns.force),
    )


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    logger.info(
        "Starting pipeline: brand=%s product=%s platform=%s mode=%s case=%s flush=%s force=%s",
        args.brand,
        args.product,
        args.platform,
        args.mode,
        args.case,
        args.flush,
        args.force,
    )

    options = PipelineOptions(case=args.case, flush=args.flush, force=args.force)

    try:
        result = run_pipeline(
            brand=args.brand,
            product=args.product,
            platform=args.platform,
            mode=args.mode,
            options=options,
        )
    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
        return 130
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
