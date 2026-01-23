from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, Optional, Set

from ...types import IndexRecord, RepoTarget
from ..llm import classify_blog_with_llm
from ..record_id import RecordId
from ..text_utils import ParsedMarkdown, normalize_ws, extract_subheadings
from .base import HandlerContext, MarkdownRepoHandler

GENERAL_PLATFORM = "general"

# Capture fence language tokens more broadly than \w+ (so it can match "c++", "c#", etc.)
_LANG_FENCE_RE = re.compile(r"```([^\s`]+)", re.IGNORECASE)

# Map common code-fence labels -> your platform keys
_FENCE_TO_PLATFORM = {
    "csharp": "net",
    "c#": "net",
    "cs": "net",
    "vb": "net",
    "vbnet": "net",
    "dotnet": "net",
    "java": "java",
    "python": "python",
    "py": "python",
    "cpp": "cpp",
    "c++": "cpp",
    "cplusplus": "cpp",
    "javascript": "nodejs",
    "js": "nodejs",
    "node": "nodejs",
    "nodejs": "nodejs",
}

# Strong language signals in prose/title (keep conservative to reduce false positives)
_STRONG_TEXT_SIGNALS = {
    "net": [r"\bc#\b", r"\bcsharp\b", r"\.net\b", r"\bdotnet\b", r"\bvb\.net\b"],
    "java": [r"\bjava\b", r"\bj2se\b", r"\bj2ee\b"],
    "python": [r"\bpython\b", r"\bpython\s*3\b", r"\bpython3\b", r"\bpythonnet\b", r"\bpython\s+for\s+\.net\b"],
    "cpp": [r"\bc\+\+\b", r"\bcpp\b", r"\bcplusplus\b"],
    "nodejs": [r"\bnode\.js\b", r"\bnodejs\b"],
    "android": [r"\bandroid\b"],
}


def _map_python_variants(platform_key: str) -> str:
    k = (platform_key or "").strip().lower()
    # Map old/variant keys to canonical python
    if k in {"python_net", "python-java", "python_cpp", "python"}:
        return "python"
    return k


def _detect_platform_signals(title: str, excerpt: str) -> Set[str]:
    """
    Detect which platform languages are strongly present.
    Returns a set of platform keys (normalized).
    """
    t = (title or "")
    e = (excerpt or "")
    text = (t + "\n" + e).lower()

    found: Set[str] = set()

    # Code fences
    for m in _LANG_FENCE_RE.finditer(excerpt or ""):
        fence = (m.group(1) or "").strip().lower()
        # normalize some common fence variants
        fence = fence.replace("language-", "")
        plat = _FENCE_TO_PLATFORM.get(fence)
        if plat:
            found.add(_map_python_variants(plat))

    # Strong text signals
    for plat, patterns in _STRONG_TEXT_SIGNALS.items():
        for pat in patterns:
            if re.search(pat, text, flags=re.IGNORECASE):
                found.add(_map_python_variants(plat))
                break

    return {_map_python_variants(x) for x in found if x}


def _build_url(frontmatter: Dict[str, Any], brand_site: Optional[str]) -> Optional[str]:
    slug = frontmatter.get("slug") or frontmatter.get("permalink") or frontmatter.get("url")
    if not slug:
        return None
    slug_s = str(slug).strip()
    if slug_s.startswith("http"):
        return slug_s
    if brand_site:
        return brand_site.rstrip("/") + "/" + slug_s.lstrip("/")
    return slug_s


def _normalize_token(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _coerce_str_list(v: Any) -> List[str]:
    """
    Normalize frontmatter fields like tags/categories that may be:
      - list
      - comma-separated string
      - None
    Removes empty tokens and the common '[]' artifact.
    """
    if v is None:
        return []
    if isinstance(v, list):
        out = [str(x).strip() for x in v if str(x).strip()]
    elif isinstance(v, str):
        s = v.strip()
        if s in {"[]", "null", "none"}:
            return []
        out = [t.strip() for t in s.split(",") if t.strip()]
    else:
        out = [str(v).strip()] if str(v).strip() else []

    cleaned: List[str] = []
    for x in out:
        if not x or x == "[]":
            continue
        cleaned.append(x)
    return cleaned


def _clean_keywords(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in items:
        t = (x or "").strip()
        if not t or t == "[]":
            continue
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
    return out


def _platform_defs_as_dict(platform_defs: Any) -> Dict[str, Dict[str, Any]]:
    """
    Normalize platform_definitions into dict form:
      {key: {"display_name": str, "keywords": [str, ...]}}
    """
    out: Dict[str, Dict[str, Any]] = {}
    if not platform_defs:
        return out
    if isinstance(platform_defs, dict):
        for k, v in platform_defs.items():
            if isinstance(v, dict):
                out[str(k)] = v
            else:
                out[str(k)] = {
                    "display_name": getattr(v, "display_name", "") or "",
                    "keywords": list(getattr(v, "keywords", []) or []),
                }
    return out


def _platforms_from_text_and_path(text: str, relpath: str, platform_defs: Any) -> List[str]:
    found = set()
    lt = (text or "").lower()
    lp = (relpath or "").lower()

    # Path-based hint
    parts = [p for p in re.split(r"[\\/]", lp) if p]
    for seg in parts[:3]:
        if isinstance(platform_defs, dict) and seg in platform_defs:
            found.add(seg)

    # Keyword/display-based hints
    items = platform_defs.items() if isinstance(platform_defs, dict) else []
    for key, pd in items:
        display_name = ""
        keywords: List[str] = []
        if isinstance(pd, dict):
            display_name = str(pd.get("display_name") or "")
            keywords = list(pd.get("keywords") or [])
        else:
            display_name = getattr(pd, "display_name", "") or ""
            keywords = list(getattr(pd, "keywords", []) or [])

        candidates = keywords + ([display_name] if display_name else [])
        for kw in candidates:
            if kw and str(kw).lower() in lt:
                found.add(str(key))
                break

    plats = sorted(found) if found else [GENERAL_PLATFORM]
    return [_map_python_variants(p) for p in plats]


def _expand_search_patterns(
    search_patterns: Sequence[str],
    *,
    product_key: str,
    product_display_name: str,
    platform_keys: Sequence[str],
) -> List[str]:
    """
    Safely expands patterns that may contain {product} and {platform}.
    Avoids KeyError by expanding both dimensions.
    """
    product_variants = sorted({_normalize_token(product_key), _normalize_token(product_display_name)})
    product_variants = [p for p in product_variants if p]

    plats = sorted({_normalize_token(p) for p in platform_keys if p})
    if GENERAL_PLATFORM not in plats:
        plats.append(GENERAL_PLATFORM)

    expanded: Set[str] = set()
    for pat in (search_patterns or []):
        pat = _normalize_token(pat)
        if not pat:
            continue

        if "{platform}" in pat:
            for pv in product_variants:
                for pl in plats:
                    expanded.add(pat.format(product=pv, platform=pl))
        else:
            for pv in product_variants:
                expanded.add(pat.format(product=pv))

    expanded.update(product_variants)
    return sorted([x for x in expanded if x])


def _path_indicates_product(relpath: str, product_key: str) -> bool:
    rp = (relpath or "").strip().lower().lstrip("/")
    pk = (product_key or "").strip().lower()
    if not pk:
        return False
    return rp == pk or rp.startswith(pk + "/") or ("/" + pk + "/") in ("/" + rp)


def _score_platform(
    platform_key: str,
    *,
    title: str,
    excerpt: str,
    relpath: str,
    platform_defs: Dict[str, Dict[str, Any]],
) -> float:
    """
    Deterministic, title-weighted platform scoring.
    Prevents ".NET" content being labeled "java" due to alphabetical sorting.
    """
    platform_key = _map_python_variants(platform_key)
    pd = platform_defs.get(platform_key, {}) or {}
    display = str(pd.get("display_name") or "").strip().lower()
    kws = [str(x).strip().lower() for x in (pd.get("keywords") or []) if str(x).strip()]

    t = (title or "").lower()
    e = (excerpt or "").lower()
    p = (relpath or "").lower()

    score = 0.0

    # Strong explicit signals
    if platform_key == "net" and (".net" in t or " for .net" in t or " dotnet" in t or "c#" in t):
        score += 6.0
    if platform_key == "python" and ("python" in t):
        score += 6.0
    if platform_key == "nodejs" and ("node.js" in t or "nodejs" in t):
        score += 6.0
    if platform_key == "android" and "android" in t:
        score += 4.0
    if platform_key == "cpp" and ("c++" in t or "cplusplus" in t or " cpp" in t):
        score += 4.0

    # Display hits
    if display and display in t:
        score += 2.5
    if display and display in e:
        score += 1.0

    # Keyword hits: title > excerpt > path
    for kw in kws:
        if kw in t:
            score += 2.0
        elif kw in e:
            score += 0.8
        elif kw in p:
            score += 0.6

    return score


def _select_primary_platform(
    *,
    candidates: List[str],
    title: str,
    excerpt: str,
    relpath: str,
    platform_defs: Dict[str, Dict[str, Any]],
    allowed_platforms: List[str],
) -> str:
    allowed_set = set([_map_python_variants(x) for x in allowed_platforms if x])
    allowed_set.add(GENERAL_PLATFORM)

    cands: List[str] = []
    for x in candidates:
        k = _map_python_variants((x or "").strip())
        if not k:
            continue
        if k not in allowed_set:
            continue
        if k not in cands:
            cands.append(k)

    if not cands:
        return GENERAL_PLATFORM

    order = {k: i for i, k in enumerate([_map_python_variants(x) for x in allowed_platforms])}  # stable tie-break
    scored: List[Tuple[str, float, int]] = []
    for k in cands:
        sc = _score_platform(k, title=title, excerpt=excerpt, relpath=relpath, platform_defs=platform_defs)
        scored.append((k, sc, order.get(k, 10_000)))

    scored.sort(key=lambda x: (x[1], -x[2]), reverse=True)
    return scored[0][0] or GENERAL_PLATFORM


def _apply_single_platform_policy(
    *,
    candidates: List[str],
    title: str,
    excerpt: str,
    relpath: str,
    platform_defs: Dict[str, Dict[str, Any]],
    allowed_platforms: List[str],
) -> str:
    """
    Your policy:
      - If multiple languages strongly present => general
      - Else if python present => python
      - Else choose best single platform via scoring among candidates
    """
    allowed = set([_map_python_variants(x) for x in allowed_platforms if x])
    allowed.add(GENERAL_PLATFORM)

    signals = _detect_platform_signals(title, excerpt)
    signals = {s for s in signals if s in allowed and s != GENERAL_PLATFORM}

    # Multi-language => general
    if len(signals) >= 2:
        return GENERAL_PLATFORM

    # Python wins if present
    if "python" in signals:
        return "python"

    # If exactly one strong signal (non-python), use it
    if len(signals) == 1:
        return next(iter(signals))

    # Otherwise, choose best candidate via scoring
    cleaned: List[str] = []
    for c in candidates or []:
        k = _map_python_variants(c)
        if k and k in allowed and k not in cleaned:
            cleaned.append(k)

    return _select_primary_platform(
        candidates=cleaned,
        title=title,
        excerpt=excerpt,
        relpath=relpath,
        platform_defs=platform_defs,
        allowed_platforms=allowed_platforms,
    )


class BlogsHandler(MarkdownRepoHandler):
    """
    Blog handler:
    - Optimizes scanning to base/<product_key> if present
    - Path-first product inclusion, then pattern/text fallback
    - Uses LLM to normalize topic/category/subcategory when ctx.normalize_topics=True
    - Enforces one-platform policy:
        * python wins if present
        * multi-language => general
        * else scored single platform
    """

    name = "blog"

    def get_scan_base(
        self,
        *,
        base: Path,
        repo_target: RepoTarget,
        product_key: str,
    ) -> Path:
        product_dir = base / product_key
        if product_dir.exists() and product_dir.is_dir():
            return product_dir
        return base

    def should_include(
        self,
        *,
        parsed: ParsedMarkdown,
        raw_for_match: str,
        relpath: str,
        repo_target: RepoTarget,
        brand: Any,
        product: Any,
        ctx: HandlerContext,
        scan_base: Path,
        base: Path,
    ) -> Tuple[bool, str]:
        if scan_base != base:
            return True, ""

        if _path_indicates_product(relpath, ctx.product_key):
            return True, ""

        expanded = _expand_search_patterns(
            getattr(brand, "search_patterns", []) or [],
            product_key=ctx.product_key,
            product_display_name=getattr(product, "display_name", ctx.product_key),
            platform_keys=list(getattr(product, "platform_definitions", {}).keys()),
        )
        text = (raw_for_match or "").lower()
        if any(p and p in text for p in expanded):
            return True, ""

        return False, "not_product"

    def build_record(
        self,
        *,
        parsed: ParsedMarkdown,
        relpath: str,
        repo_target: RepoTarget,
        brand: Any,
        product: Any,
        ctx: HandlerContext,
    ) -> IndexRecord:
        platform_defs_raw = getattr(product, "platform_definitions", {}) or {}
        platform_defs = _platform_defs_as_dict(platform_defs_raw)
        allowed_platforms = [_map_python_variants(x) for x in list(platform_defs.keys())]

        raw = f"{parsed.title}\n{parsed.body[:2500]}"
        inferred_plats = _platforms_from_text_and_path(raw, relpath, platform_defs_raw)

        fm = parsed.frontmatter or {}
        headings = extract_subheadings(parsed.body, max_items=30)

        # Keywords = tags + headings only (NO platform keys)
        tags = fm.get("tags") or fm.get("tag") or []
        tag_list = _coerce_str_list(tags)
        keywords = _clean_keywords(tag_list + headings)

        url = _build_url(fm, getattr(brand, "website", None))

        excerpt = parsed.body[:2500]

        if ctx.normalize_topics:
            topic, cat, subcat, plats = classify_blog_with_llm(
                client=ctx.client,
                model=ctx.settings.PROFESSIONALIZE_LLM_MODEL,
                title=parsed.title,
                excerpt=excerpt,
                allowed_platforms=allowed_platforms,
                inferred_platforms=inferred_plats,
            )

            primary_platform = _apply_single_platform_policy(
                candidates=(plats or []) + (inferred_plats or []),
                title=parsed.title,
                excerpt=excerpt,
                relpath=relpath,
                platform_defs=platform_defs,
                allowed_platforms=allowed_platforms,
            )

            return IndexRecord(
                id=RecordId.for_markdown(repo_key=repo_target.repo_key, relpath=relpath),
                brand=ctx.brand_key,
                product=ctx.product_key,
                repo_key=repo_target.repo_key,
                repo_type=repo_target.repo_type,
                platform=primary_platform,
                title=parsed.title[:300],
                topic=str(topic)[:200],
                category=str(cat)[:100],
                sub_category=str(subcat)[:100],
                url=url,
                source_path=relpath,
                excerpt=normalize_ws(parsed.body[:400]),
                keywords=keywords,
            )

        # Non-LLM fallback (still enforces single-platform policy)
        category = fm.get("category") or fm.get("categories") or "General"
        sub_category = fm.get("sub_category") or fm.get("subcategory") or "General"
        topic = fm.get("topic") or fm.get("title") or parsed.title

        if isinstance(category, list):
            category = category[0] if category else "General"
        if isinstance(sub_category, list):
            sub_category = sub_category[0] if sub_category else "General"

        primary_platform = _apply_single_platform_policy(
            candidates=inferred_plats or [GENERAL_PLATFORM],
            title=parsed.title,
            excerpt=excerpt,
            relpath=relpath,
            platform_defs=platform_defs,
            allowed_platforms=allowed_platforms,
        )

        return IndexRecord(
            id=RecordId.for_markdown(repo_key=repo_target.repo_key, relpath=relpath),
            brand=ctx.brand_key,
            product=ctx.product_key,
            repo_key=repo_target.repo_key,
            repo_type=repo_target.repo_type,
            platform=primary_platform,
            title=parsed.title[:300],
            topic=str(topic)[:200],
            category=str(category)[:100],
            sub_category=str(sub_category)[:100],
            url=url,
            source_path=relpath,
            excerpt=normalize_ws(parsed.body[:400]),
            keywords=keywords,
        )
