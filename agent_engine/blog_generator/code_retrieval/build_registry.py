"""
Builds/refreshes content/exampleRepos/<brand>.json - the Repo Registry
snapshot that registry.py reads at retrieval time.

Runs on a weekly schedule (.github/workflows/example_repo_registry.yml) and
can also be run by hand (`python build_registry.py aspose.com`). It never
lets the blog pipeline make a live GitHub check itself - that stays here.

Today only the ".NET" platform + the "agentic-net-examples" repo-name
convention is known to exist (9 real repos, confirmed 2026-08-27). Other
platforms are intentionally left out of the generated snapshot rather than
guessed at - a wrong convention would be worse than an absent entry, since
registry.resolve() already treats "missing" and "not found" the same way
(fall through to the LLM path).

Unattended-safe: a `verified` repo is only ever downgraded to `not_found`
when GitHub explicitly answers 404. On any ambiguous failure (rate limit,
5xx, network) the product's previous snapshot entry is kept untouched, so a
transient error can't silently disable retrieval for a product.
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


def _check_repo(client: GitHubClient, repo: str) -> str:
    """'exists' | 'missing' (GitHub said 404) | 'error' (anything ambiguous)."""
    if client.repo_exists(repo):
        return "exists"
    return "missing" if (client.last_error or "").startswith("404") else "error"


def _load_prior_snapshot(out_path: str) -> dict:
    """Previous entries keyed by (product, platform), for downgrade protection."""
    if not os.path.exists(out_path):
        return {}
    try:
        with open(out_path, "r") as f:
            return {(e["product"], e["platform"]): e for e in json.load(f)}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def build(brand: str, token: str = "") -> tuple[list[dict], list[str]]:
    """Returns (entries, change_lines). change_lines is a human-readable list
    of what moved since the previous snapshot (empty = nothing changed)."""
    with open(os.path.join(PRODUCTS_DIR, f"{brand}.json"), "r") as f:
        products = json.load(f)

    out_path = os.path.join(OUT_DIR, f"{brand}.json")
    prior = _load_prior_snapshot(out_path)

    client = GitHubClient(token=token)
    today = date.today().isoformat()
    entries: list[dict] = []
    changes: list[str] = []

    for product in products:
        platform = _platform_from_product_name(product.get("ProductName", ""))
        url_prefix = product.get("urlPrefix")
        if not platform or not url_prefix:
            continue
        convention = PLATFORM_REPO_CONVENTIONS.get(platform)
        if not convention:
            continue

        name = product["ProductName"]
        candidate_repo = convention(url_prefix)
        prev = prior.get((name, platform))
        result = _check_repo(client, candidate_repo)

        if result == "error" and prev is not None:
            # Ambiguous failure - keep the previous entry as-is.
            entries.append(prev)
            print(f"⚠️  {name} -> {candidate_repo}: check failed "
                  f"({client.last_error}); keeping previous status "
                  f"'{prev.get('status')}'")
            continue

        verified = result == "exists"
        repository = candidate_repo if verified else None
        status = "verified" if verified else "not_found"

        prev_verified = bool(prev and prev.get("status") == "verified")
        unchanged = bool(
            prev
            and prev.get("status") == status
            and prev.get("repository") == repository
        )
        if unchanged:
            # Same result as last run - keep the old entry so `last_verified`
            # doesn't churn and a no-op weekly run produces an empty diff.
            entries.append(prev)
        else:
            entries.append({
                "brand": brand,
                "urlPrefix": url_prefix,
                "product": name,
                "platform": platform,
                "repository": repository,
                "branch": "main",
                "status": status,
                "last_verified": today,
            })

        if verified and not prev_verified:
            changes.append(f"NEW: {name} -> https://github.com/{candidate_repo}")
        elif not verified and prev_verified:
            changes.append(f"REMOVED: {name} ({candidate_repo} now returns 404)")

        print(f"{'✓' if verified else '✗'} {name} -> {candidate_repo}")

    return entries, changes


def main():
    brand = sys.argv[1] if len(sys.argv) > 1 else "aspose.com"
    summary_file = None
    for arg in sys.argv[2:]:
        if arg.startswith("--summary-file="):
            summary_file = arg.split("=", 1)[1]

    token = os.environ.get("REPO_PAT") or os.environ.get("GITHUB_TOKEN", "")
    entries, changes = build(brand, token=token)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{brand}.json")
    with open(out_path, "w") as f:
        json.dump(entries, f, indent=2)

    verified = sum(1 for e in entries if e["status"] == "verified")
    print(f"\nWrote {out_path}: {verified}/{len(entries)} products have a known repo.")
    if changes:
        print("\nChanges since last run:")
        for line in changes:
            print(f"  - {line}")
    else:
        print("\nNo changes since last run.")

    if summary_file:
        with open(summary_file, "w") as f:
            if changes:
                f.write(f"Example-repo registry update for **{brand}** "
                        f"({verified}/{len(entries)} products have a repo):\n\n")
                f.write("\n".join(f"- {c}" for c in changes) + "\n")
            else:
                f.write(f"No example-repo changes for **{brand}** this run.\n")


if __name__ == "__main__":
    main()
