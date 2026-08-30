"""
Builds/refreshes content/exampleRepos/<brand>.json - the Repo Registry
snapshot that registry.py reads at retrieval time.

Run manually for now (`python build_registry.py aspose.com`); the
architecture calls for this to eventually run on a schedule (e.g.
piggybacking the product-reconciler's weekly cron) so the snapshot stays
current as new Example-Agent repos get created, without the blog pipeline
ever making a live GitHub existence check itself.

Today only the ".NET" platform + the "agentic-net-examples" repo-name
convention is known to exist (9 real repos, confirmed 2026-08-27). Other
platforms are intentionally left out of the generated snapshot rather than
guessed at - a wrong convention would be worse than an absent entry, since
registry.resolve() already treats "missing" and "not found" the same way
(fall through to the LLM path).
"""
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from github_client import GitHubClient  # noqa: E402

PRODUCTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../content/productsData")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../content/exampleRepos")

PLATFORM_REPO_CONVENTIONS = {
    ".NET": lambda url_prefix: f"aspose-{url_prefix}/agentic-net-examples",
}


def _platform_from_product_name(name: str) -> str | None:
    if name.endswith("for .NET") or name.endswith("for .NET Core"):
        return ".NET"
    return None


def build(brand: str, token: str = "") -> list[dict]:
    products_path = os.path.join(PRODUCTS_DIR, f"{brand}.json")
    with open(products_path, "r") as f:
        products = json.load(f)

    client = GitHubClient(token=token)
    today = date.today().isoformat()
    entries = []

    for product in products:
        platform = _platform_from_product_name(product.get("ProductName", ""))
        url_prefix = product.get("urlPrefix")
        if not platform or not url_prefix:
            continue
        repo_convention = PLATFORM_REPO_CONVENTIONS.get(platform)
        if not repo_convention:
            continue

        candidate_repo = repo_convention(url_prefix)
        exists = client.repo_exists(candidate_repo)
        entries.append({
            "brand": brand,
            "urlPrefix": url_prefix,
            "product": product["ProductName"],
            "platform": platform,
            "repository": candidate_repo if exists else None,
            "branch": "main",
            "status": "verified" if exists else "not_found",
            "last_verified": today,
        })
        print(f"{'✓' if exists else '✗'} {product['ProductName']} -> {candidate_repo}")

    return entries


def main():
    brand = sys.argv[1] if len(sys.argv) > 1 else "aspose.com"
    token = os.environ.get("REPO_PAT") or os.environ.get("GITHUB_TOKEN", "")
    entries = build(brand, token=token)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{brand}.json")
    with open(out_path, "w") as f:
        json.dump(entries, f, indent=2)

    verified = sum(1 for e in entries if e["status"] == "verified")
    print(f"\nWrote {out_path}: {verified}/{len(entries)} products have a known repo.")


if __name__ == "__main__":
    main()
