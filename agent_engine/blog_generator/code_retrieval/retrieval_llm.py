"""
LLM-judgment retrieval pipeline: topic + product + platform -> a real
example file, picked and verified by the self-hosted LLM reading the full
real file list and the actual candidate content - not by keyword scoring.

Kept as a separate module from retrieval.py (the keyword-scoring version)
rather than replacing it, so both can be measured against the same 53-topic
ground truth and compared directly.
"""
import time

from . import registry
from .github_client import GitHubClient
from .llm_judge import pick_file, verify_file

LANGUAGE_BY_EXTENSION = {".cs": "csharp"}

# A Stage 1 pick that fails Stage 2 (or whose content can't be fetched) is not
# the end - the file is excluded and the LLM is asked again, told why the last
# pick was wrong. Capped so a topic with genuinely no good example still
# terminates in an honest NO_MATCH rather than looping.
MAX_PICK_ATTEMPTS = 3


def _finish(result: dict, start: float) -> dict:
    elapsed = time.monotonic() - start
    print(f"⏱️  Total time: {elapsed:.1f}s", flush=True)
    return {**result, "elapsed_seconds": round(elapsed, 1)}


def _no_match(base: dict, reason: str, start: float) -> dict:
    return _finish({**base, "repo": None, "pick": None, "verification": None, "selected": None,
                     "confidence": "NO_MATCH", "reason": reason}, start)


async def retrieve_example_llm(
    brand: str,
    product_name: str,
    platform: str,
    topic: str,
    primary_keyword: str = "",
    outline: list[str] | None = None,
    token: str = "",
) -> dict:
    start = time.monotonic()
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
        return _no_match(base, f"no verified repo registered for '{product_name}' / '{platform}'.{hint}", start)
    print(f"📦 Repo: {repo_ref.repository}", flush=True)

    client = GitHubClient(token=token)
    print("📥 Fetching repo file tree...", flush=True)
    paths = client.get_tree(repo_ref.repository, ref=repo_ref.branch)
    if not paths:
        return _no_match(base, f"could not fetch repo file tree: {client.last_error}", start)

    cs_paths = [p for p in paths if p.endswith(".cs")]
    if not cs_paths:
        return _no_match(base, "no .cs example files found in this repo's tree", start)
    print(f"📥 {len(cs_paths)} .cs files found", flush=True)

    excluded: set[str] = set()
    feedback = None
    pick = verification = None
    verified_pick = verified_content = None
    last_reason = None

    for attempt in range(1, MAX_PICK_ATTEMPTS + 1):
        pick = await pick_file(topic, primary_keyword, platform, product_name, cs_paths,
                               exclude=excluded, feedback=feedback)
        if not pick["file"]:
            return _finish({**base, "repo": repo_ref.repository, "pick": pick, "verification": verification,
                             "selected": None, "confidence": "NO_MATCH",
                             "reason": f"LLM found no matching file: {pick['reason']}"}, start)

        content = client.get_small_file(repo_ref.repository, pick["file"], ref=repo_ref.branch)
        if content is None:
            last_reason = f"could not fetch '{pick['file']}': {client.last_error}"
            print(f"↩️  {last_reason}", flush=True)
            excluded.add(pick["file"])
            feedback = (f"The file \"{pick['file']}\" could not be retrieved from the repo. "
                        f"Choose a different file, or NONE.")
            continue

        verification = await verify_file(topic, primary_keyword, platform, pick["file"], content)
        if verification["verified"]:
            verified_pick, verified_content = pick, content
            break

        last_reason = verification["reason"]
        excluded.add(pick["file"])
        feedback = (f"Your previous pick \"{pick['file']}\" was rejected on verification: {last_reason} "
                    f"Choose a different file that matches the topic more precisely, or NONE.")
        if attempt < MAX_PICK_ATTEMPTS:
            print(f"↩️  Re-picking ({attempt + 1}/{MAX_PICK_ATTEMPTS}) — previous pick rejected: {last_reason}",
                  flush=True)

    if verified_pick is None:
        return _finish({**base, "repo": repo_ref.repository, "pick": pick, "verification": verification,
                         "selected": None, "confidence": "NO_MATCH",
                         "reason": f"no verified match after {MAX_PICK_ATTEMPTS} picks; last: {last_reason}"}, start)

    pick, content = verified_pick, verified_content
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

    return _finish({
        **base,
        "repo": repo_ref.repository,
        "pick": pick,
        "verification": verification,
        "selected": selected,
        "confidence": "LLM_VERIFIED",
    }, start)
