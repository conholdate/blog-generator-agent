"""
Product Reconciler MCP Server

Keeps a brand's productsData JSON in sync with what's actually published
on that brand's products/releases repos: adds new products/platforms as
they launch, and fixes fields that have drifted from their real source.
Runs on its own schedule (see the GitHub Actions workflow), independent
of individual blog-post runs.

aspose.cloud, groupdocs.cloud, and aspose.com each have a populated
BrandConfig + extraction logic (see reconciler/config.py) — a new brand
needs both a config entry and brand-aware scraping before "brand" here
can do real work for it.
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../"))
if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from fastmcp import FastMCP
from dotenv import load_dotenv

from agent_engine.blog_generator.config import settings
from reconciler.run import reconcile
from reconciler.config import BRANDS

load_dotenv()

mcp = FastMCP("product-reconciler")


@mcp.tool()
def reconcile_products(brand: str = "aspose.cloud", dry_run: bool = False) -> dict:
    """
    Reconciles a brand's productsData JSON against its live products/
    releases repos.

    Args:
        brand: which brand to reconcile. Currently supported: aspose.cloud,
            groupdocs.cloud, aspose.com.
        dry_run: if True, computes and returns the report without writing
            anything to the JSON file. Defaults to False (applies fixes
            and adds new entries) since this tool is only ever invoked
            from a scheduled job that commits its own branch and opens
            a PR for review — nothing reaches main without a human glance.

    Returns:
        A report: new_products, new_platforms, fixed_fields,
        potential_removals (flagged only, never auto-deleted), and
        unresolved (things that need a human because no source could
        confirm them). Or {"error": ...} if the brand isn't configured
        yet or something else went wrong.
    """
    if brand not in BRANDS:
        return {"error": f"Unsupported brand {brand!r}. Configured brands: {', '.join(sorted(BRANDS))}"}

    token = settings.REPO_PAT or os.environ.get("GITHUB_TOKEN", "")
    try:
        return reconcile(brand=brand, token=token, dry_run=dry_run)
    except Exception as e:
        print(f"Error in reconcile_products({brand!r}): {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
