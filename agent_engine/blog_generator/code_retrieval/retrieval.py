"""
Phase 1 retrieval pipeline: topic + product + platform -> ranked, verified
code-example candidates, with full provenance and scoring exposed - an
evaluation harness, not just a "topic -> snippet" black box. See
memory/architecture notes for why each stage exists.

Does NOT touch utils/code_snippet.py or orchestrator.py - this is the
standalone Phase 1 tester only. Wiring a fallback-to-LLM path into the real
pipeline is a later phase.

File discovery uses one recursive git-tree fetch, not index.json +
per-category directory listing. Original design gated file search behind a
category-name match first; real-repo testing found that misses genuinely
relevant files sitting in generically-named categories (e.g. an SVG-to-EMF
example inside "manage-presentation-media-files" - the folder name gives no
hint of what's inside it, so it never scored well enough to make the
category shortlist). The tree fetch is a single API call even for the
largest repos checked (~2,300 files, well under GitHub's truncation limit),
so scoring every file directly is both more correct and simpler than the
category-gated version - category is now reported for context, not used to
filter candidates.
"""
from dataclasses import asdict

from . import registry
from .github_client import GitHubClient
from .matcher import rank
from .normalizer import normalize
from .verification import verify

TOP_CATEGORIES = 5  # informational only - not used to filter file search
TOP_FILES = 8

CONFIDENCE_THRESHOLDS = [  # placeholders - tuned for real in Phase 2, see matcher.py docstring
    (0.75, "HIGH_CONFIDENCE"),
    (0.50, "MEDIUM_CONFIDENCE"),
    (0.30, "LOW_CONFIDENCE"),
]

LANGUAGE_BY_EXTENSION = {".cs": "csharp"}


def _confidence_for(score: float) -> str:
    for threshold, label in CONFIDENCE_THRESHOLDS:
        if score >= threshold:
            return label
    return "NO_MATCH"


def _no_match(base: dict, reason: str) -> dict:
    return {**base, "repo": None, "category_candidates": [], "file_candidates": [],
            "selected": None, "confidence": "NO_MATCH", "reason": reason}


def retrieve_example(
    brand: str,
    product_name: str,
    platform: str,
    topic: str,
    primary_keyword: str = "",
    outline: list[str] | None = None,
    token: str = "",
) -> dict:
    query_terms = normalize(topic, primary_keyword, outline)
    base = {
        "input": {
            "brand": brand, "product": product_name, "platform": platform,
            "topic": topic, "primary_keyword": primary_keyword, "outline": outline or [],
        },
        "normalized_terms": sorted(query_terms),
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

    file_pairs = []  # (category, filename)
    categories_seen = set()
    for path in paths:
        if not path.endswith(".cs"):
            continue
        category, _, filename = path.rpartition("/")
        category = category or "(root)"
        file_pairs.append((category, filename, path))
        categories_seen.add(category)

    if not file_pairs:
        return _no_match(base, "no .cs example files found in this repo's tree")

    # Informational: which folders look relevant, for the report only - no
    # longer gates which files get scored (see module docstring).
    category_candidates = rank(query_terms, [(c, c) for c in categories_seen], top_n=TOP_CATEGORIES)
    category_score_by_name = {c["id"]: c["score"] for c in category_candidates}

    ranked_files = rank(
        query_terms,
        [(path, filename) for category, filename, path in file_pairs],
        top_n=TOP_FILES,
    )

    file_candidates = []
    best = None
    for candidate in ranked_files:
        category, _, filename = candidate["id"].rpartition("/")
        category = category or "(root)"
        content = client.get_small_file(repo_ref.repository, candidate["id"], ref=repo_ref.branch)
        if content is None:
            file_candidates.append({**candidate, "category": category, "file": filename,
                                     "fetch_error": client.last_error, "verification": None,
                                     "combined_score": 0.0, "rejected": True})
            continue

        v = verify(content, query_terms, repo_ref.url_prefix)
        # category_score is deliberately NOT part of this - it's informational-only
        # (see module docstring): a file's actual category is often outside the
        # top-N category list report, and defaulting that to 0 would silently
        # reintroduce a category-name bias the tree-based file search exists to avoid.
        combined = round(0.7 * candidate["score"] + 0.3 * v.score, 4)
        entry = {
            **candidate, "category": category, "file": filename,
            "verification": asdict(v), "combined_score": combined, "rejected": not v.passed,
        }
        file_candidates.append(entry)
        if v.passed and (best is None or combined > best["combined_score"]):
            best = {**entry, "content": content}

    if best is None:
        return {
            **base, "repo": repo_ref.repository, "category_candidates": category_candidates,
            "file_candidates": file_candidates, "selected": None, "confidence": "NO_MATCH",
            "reason": "no candidate passed verification",
        }

    ext = "." + best["file"].rsplit(".", 1)[-1]
    selected = {
        "language": LANGUAGE_BY_EXTENSION.get(ext, ext.lstrip(".")),
        "code": best["content"],
        "source": {
            "brand": brand, "product": product_name, "platform": platform,
            "repository": repo_ref.repository, "category": best["category"], "file": best["file"],
        },
        "matching": {
            "category_score": category_score_by_name.get(best["category"], 0.0),
            "file_score": best["score"],
            "verification_score": best["verification"]["score"],
            "combined_score": best["combined_score"],
        },
    }

    return {
        **base,
        "repo": repo_ref.repository,
        "category_candidates": category_candidates,
        "file_candidates": [{k: v for k, v in c.items() if k != "content"} for c in file_candidates],
        "selected": selected,
        "confidence": _confidence_for(best["combined_score"]),
    }
