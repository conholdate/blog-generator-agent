"""
LLM-judgment retrieval pipeline: topic + product + platform -> a real
example file, picked and verified by the self-hosted LLM reading the full
real file list and the actual candidate content - not by keyword scoring.

Kept as a separate module from retrieval.py (the keyword-scoring version)
rather than replacing it, so both can be measured against the same 53-topic
ground truth and compared directly.
"""
from . import registry
from .github_client import GitHubClient
from .llm_judge import pick_file, verify_file

LANGUAGE_BY_EXTENSION = {".cs": "csharp"}


def _no_match(base: dict, reason: str) -> dict:
    return {**base, "repo": None, "pick": None, "verification": None, "selected": None,
            "confidence": "NO_MATCH", "reason": reason}


async def retrieve_example_llm(
    brand: str,
    product_name: str,
    platform: str,
    topic: str,
    primary_keyword: str = "",
    outline: list[str] | None = None,
    token: str = "",
) -> dict:
    base = {
        "input": {
            "brand": brand, "product": product_name, "platform": platform,
            "topic": topic, "primary_keyword": primary_keyword, "outline": outline or [],
        },
    }

    repo_ref = registry.resolve(brand, product_name, platform)
    if repo_ref is None:
        known = registry.known_products(brand, platform)
        hint = f" Known {platform} products: {', '.join(known)}" if known else ""
        return _no_match(base, f"no verified repo registered for '{product_name}' / '{platform}'.{hint}")

    client = GitHubClient(token=token)
    paths = client.get_tree(repo_ref.repository, ref=repo_ref.branch)
    if not paths:
        return _no_match(base, f"could not fetch repo file tree: {client.last_error}")

    cs_paths = [p for p in paths if p.endswith(".cs")]
    if not cs_paths:
        return _no_match(base, "no .cs example files found in this repo's tree")

    pick = await pick_file(topic, primary_keyword, platform, product_name, cs_paths)
    if not pick["file"]:
        return {**base, "repo": repo_ref.repository, "pick": pick, "verification": None,
                "selected": None, "confidence": "NO_MATCH",
                "reason": f"LLM found no matching file: {pick['reason']}"}

    content = client.get_small_file(repo_ref.repository, pick["file"], ref=repo_ref.branch)
    if content is None:
        return {**base, "repo": repo_ref.repository, "pick": pick, "verification": None,
                "selected": None, "confidence": "NO_MATCH",
                "reason": f"could not fetch picked file content: {client.last_error}"}

    verification = await verify_file(topic, primary_keyword, platform, pick["file"], content)
    if not verification["verified"]:
        return {**base, "repo": repo_ref.repository, "pick": pick, "verification": verification,
                "selected": None, "confidence": "NO_MATCH",
                "reason": f"LLM rejected its own pick on verification: {verification['reason']}"}

    category, _, filename = pick["file"].rpartition("/")
    ext = "." + filename.rsplit(".", 1)[-1]
    selected = {
        "language": LANGUAGE_BY_EXTENSION.get(ext, ext.lstrip(".")),
        "code": content,
        "source": {
            "brand": brand, "product": product_name, "platform": platform,
            "repository": repo_ref.repository, "category": category or "(root)", "file": filename,
        },
    }

    return {
        **base,
        "repo": repo_ref.repository,
        "pick": pick,
        "verification": verification,
        "selected": selected,
        "confidence": "LLM_VERIFIED",
    }
