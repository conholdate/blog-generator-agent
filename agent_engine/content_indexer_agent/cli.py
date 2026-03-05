from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from dotenv import load_dotenv

from .agent import IndexPlan, execute_plan, run_agent_sync
from .settings import Settings
from .tools.logging_utils import get_logger
from .tools.specs import find_product_yamls, load_brand_yaml, load_product_yaml

app = typer.Typer(no_args_is_help=True)

log = get_logger("cg-gap.indexer.cli")

def _configure_logging(level: Optional[str]) -> None:
    """
    Configure log level for this CLI invocation.
    Note: get_logger() sets INFO by default; here we allow overriding.
    """
    if not level:
        return
    lvl = getattr(logging, level.upper(), None)
    if not isinstance(lvl, int):
        raise typer.BadParameter(f"Invalid --log-level '{level}'. Use DEBUG, INFO, WARNING, ERROR.")
    log.setLevel(lvl)
    log.info("Log level set to %s", level.upper())


@app.callback()
def _main(log_level: Optional[str] = typer.Option(None, "--log-level", "-l")) -> None:
    load_dotenv()  # loads .env into os.environ
    _configure_logging(log_level)

    import os
    log.info("CLI started")
    log.info("PROFESSIONALIZE_API_KEY set: %s", bool(os.getenv("PROFESSIONALIZE_API_KEY")))


def _pick(msg: str, options: list[str]) -> str:
    log.info("Interactive selection: %s options=%d", msg, len(options))
    rprint(msg)
    for i, o in enumerate(options, 1):
        rprint(f"  {i}. {o}")
    while True:
        raw = input("Select number: ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                choice = options[idx - 1]
                log.info("Interactive selection chosen: %s", choice)
                return choice
        rprint("Invalid selection.")


@app.command("run")
def run(
    brand_yaml: Path = typer.Option(..., "--brand"),
    platform: str = typer.Option(..., "--platform"),
    steps: str = typer.Option("blog,docs,tutorials,api", "--steps", help="CSV repo keys"),
    product_yaml: Optional[Path] = typer.Option(None, "--product"),
    products_dir: Optional[Path] = typer.Option(None, "--products-dir", help="For interactive selection"),
    brand_key: Optional[str] = typer.Option(None, "--brand-key", help="Optional brand hint"),
    delete_missing: bool = typer.Option(False, "--delete-missing"),
    use_agent: bool = typer.Option(False, "--use-agent/--no-agent", help="Use Agents SDK triage+handoff"),
    normalize_topics: bool = typer.Option(
        True,
        "--normalize-topics/--no-normalize-topics",
        help="If enabled, blogs use LLM normalization; otherwise use frontmatter + subheadings only.",
    ),
) -> None:
    """
    Run incremental indexing.

    CI usage:
      cg-index run --brand blogs.yaml --product products/cells.yaml --platform net --steps blog,docs

    Local interactive usage:
      cg-index run --brand blogs.yaml --products-dir products --platform net
    """
    log.info(
        "run invoked: brand_yaml=%s platform=%s steps=%s product_yaml=%s products_dir=%s brand_hint=%s "
        "delete_missing=%s use_agent=%s normalize_topics=%s",
        brand_yaml,
        platform,
        steps,
        str(product_yaml) if product_yaml else "None",
        str(products_dir) if products_dir else "None",
        brand_key or "None",
        delete_missing,
        use_agent,
        normalize_topics,
    )

    # Instantiate settings early (ensures env/config loaded)
    _ = Settings()
    log.info("Settings initialized")

    # Agents SDK path
    if use_agent:
        log.info("Execution path: Agents SDK (triage + handoff)")
        if product_yaml:
            prompt = (
                f"Index with brand_yaml={brand_yaml} product_yaml={product_yaml} "
                f"platform={platform} steps_csv={steps} delete_missing={delete_missing}."
            )
        else:
            if not products_dir:
                raise typer.BadParameter("--use-agent without --product requires --products-dir")
            prompt = (
                f"Help me index. brand_yaml={brand_yaml}. products_dir={products_dir}. "
                f"brand_hint={brand_key or 'none'}. platform={platform}. steps_csv={steps}."
            )

        log.info("Calling run_agent_sync with prompt length=%d", len(prompt))
        result = run_agent_sync(prompt)
        log.info("Agent run complete (result length=%d)", len(str(result)))
        rprint(result)
        return

    # Deterministic path
    log.info("Execution path: deterministic (no Agents SDK)")
    if not product_yaml:
        if not products_dir:
            raise typer.BadParameter("Either --product or --products-dir is required.")

        log.info("No --product provided; entering interactive selection mode")

        brands = load_brand_yaml(brand_yaml)
        brand_keys = sorted([k for k, b in brands.items() if b.enabled])
        log.info("Brands loaded: enabled=%d total=%d", len(brand_keys), len(brands))

        chosen_brand = brand_key if brand_key in brand_keys else _pick("Select brand:", brand_keys)
        log.info("Brand selected: %s", chosen_brand)

        candidates = find_product_yamls(products_dir)
        log.info("Product YAML candidates discovered in %s: %d", products_dir, len(candidates))

        prod_paths: list[str] = []
        for p in candidates:
            ps = load_product_yaml(p)
            if ps.enabled and ps.blog == chosen_brand:
                prod_paths.append(str(p))
        prod_paths.sort()

        log.info("Filtered enabled products for brand=%s: %d", chosen_brand, len(prod_paths))
        if not prod_paths:
            raise typer.BadParameter(f"No enabled products for brand '{chosen_brand}'.")

        product_yaml = Path(_pick("Select product yaml:", prod_paths))

    # Build plan
    product = load_product_yaml(product_yaml)
    plan = IndexPlan(
        brand_yaml=str(brand_yaml),
        product_yaml=str(product_yaml),
        brand_key=product.blog,
        product_key=product_yaml.stem,
        platform=platform,
        steps=[x.strip() for x in steps.split(",") if x.strip()],
        delete_missing=delete_missing,
        normalize_topics=normalize_topics,
    )

    log.info(
        "Plan built: brand=%s product_key=%s platform=%s steps=%s delete_missing=%s normalize_topics=%s",
        plan.brand_key,
        plan.product_key,
        plan.platform,
        ",".join(plan.steps),
        plan.delete_missing,
        plan.normalize_topics,
    )

    s = Settings()

    # Load brands (for sanity) and execute
    brands = load_brand_yaml(Path(plan.brand_yaml))
    log.info("Brands YAML loaded: keys=%s", ", ".join(sorted(brands.keys())))

    log.info("Executing plan")
    out = execute_plan(plan, s=s)

    # Log a concise summary
    details = out.get("details") if isinstance(out, dict) else None
    log.info(
        "Plan execution complete: run_id=%s steps_completed=%d",
        out.get("run_id") if isinstance(out, dict) else "",
        len(details) if isinstance(details, dict) else 0,
    )

    rprint(out)


if __name__ == "__main__":
    app()
